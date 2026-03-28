(function() {
  function normalizeLabelSlug(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeLabelSlugs(values) {
    var normalized = [];
    var seen = {};
    values.forEach(function(rawValue) {
      var value = normalizeLabelSlug(rawValue);
      if (!value || seen[value]) {
        return;
      }
      seen[value] = true;
      normalized.push(value);
    });
    return normalized;
  }

  function isLabelSelected(button) {
    return String(button.getAttribute("data-label-selected") || "false") === "true";
  }

  function buildSearchPreservingNonLabel(sourceParams, selectedLabels) {
    var nextParams = new URLSearchParams();
    sourceParams.forEach(function(value, key) {
      if (key !== "label") {
        nextParams.append(key, value);
      }
    });
    normalizeLabelSlugs(selectedLabels).forEach(function(slug) {
      nextParams.append("label", slug);
    });
    return nextParams.toString();
  }

  function buildSearchPreservingNonPanel(sourceParams, panelState) {
    var nextParams = new URLSearchParams();
    sourceParams.forEach(function(value, key) {
      if (key !== "panel") {
        nextParams.append(key, value);
      }
    });
    if (panelState) {
      nextParams.set("panel", panelState);
    }
    return nextParams.toString();
  }

  function mutateLabelQuery(action, labelSlug) {
    var params = new URLSearchParams(window.location.search);
    var selectedLabels = normalizeLabelSlugs(params.getAll("label"));

    if (action === "add") {
      selectedLabels = normalizeLabelSlugs(selectedLabels.concat([labelSlug]));
    } else if (action === "remove") {
      var normalizedSlug = normalizeLabelSlug(labelSlug);
      selectedLabels = selectedLabels.filter(function(slug) {
        return slug !== normalizedSlug;
      });
    } else if (action === "clear") {
      selectedLabels = [];
    }

    var nextSearch = buildSearchPreservingNonLabel(params, selectedLabels);
    var nextUrl = window.location.pathname + (nextSearch ? "?" + nextSearch : "") + window.location.hash;
    window.location.assign(nextUrl);
  }

  function setPanelState(panelState) {
    var params = new URLSearchParams(window.location.search);
    var nextSearch = buildSearchPreservingNonPanel(params, panelState);
    var nextUrl = window.location.pathname + (nextSearch ? "?" + nextSearch : "") + window.location.hash;
    window.history.replaceState({}, "", nextUrl);
  }

  function reorderLabelRows(listElement) {
    var buttons = Array.prototype.slice.call(
      listElement.querySelectorAll('[data-action="toggle-label"], [data-label-toggle]')
    );
    if (!buttons.length) {
      return;
    }

    var selectedBySlug = {};
    buttons.forEach(function(button) {
      selectedBySlug[normalizeLabelSlug(button.getAttribute("data-label-slug"))] = button;
    });

    var selectedInUrl = normalizeLabelSlugs(new URLSearchParams(window.location.search).getAll("label"));
    var selected = [];
    selectedInUrl.forEach(function(slug) {
      if (selectedBySlug[slug]) {
        selected.push(selectedBySlug[slug]);
      }
    });

    var selectedSet = {};
    selected.forEach(function(button) {
      selectedSet[normalizeLabelSlug(button.getAttribute("data-label-slug"))] = true;
    });

    var rest = buttons.filter(function(button) {
      return !selectedSet[normalizeLabelSlug(button.getAttribute("data-label-slug"))];
    });

    rest.sort(function(first, second) {
      var firstName = String(first.getAttribute("data-label-name") || "").toLowerCase();
      var secondName = String(second.getAttribute("data-label-name") || "").toLowerCase();
      if (firstName < secondName) {
        return -1;
      }
      if (firstName > secondName) {
        return 1;
      }
      return 0;
    });

    selected.concat(rest).forEach(function(button) {
      listElement.appendChild(button);
    });
  }

  function updateLabelListVisibility(rootElement) {
    if (!rootElement) {
      return;
    }

    var list = rootElement.querySelector('[data-role="label-options-list"], [data-label-options-list]');
    if (!list) {
      return;
    }

    var searchInput = rootElement.querySelector('[data-action="search-labels"], [data-label-search-input]');
    var showMoreButton = rootElement.querySelector('[data-action="toggle-show-more-labels"], [data-label-show-more]');
    var noMatchMessage = rootElement.querySelector('[data-role="label-no-match"], [data-label-no-match]');
    var query = String(searchInput ? searchInput.value : "").trim().toLowerCase();
    var showAll = showMoreButton
      && String(showMoreButton.getAttribute("data-expanded") || "false") === "true";

    var buttons = Array.prototype.slice.call(
      list.querySelectorAll('[data-action="toggle-label"], [data-label-toggle]')
    );
    var visibleCount = 0;

    buttons.forEach(function(button) {
      var labelName = String(button.getAttribute("data-label-name") || "").toLowerCase();
      var defaultHidden = String(button.getAttribute("data-label-default-hidden") || "false") === "true";
      var selected = isLabelSelected(button);
      var matchesQuery = !query || labelName.indexOf(query) !== -1;
      var isVisible = matchesQuery;

      if (!query && !showAll && defaultHidden && !selected) {
        isVisible = false;
      }

      button.classList.toggle("d-none", !isVisible);
      if (isVisible) {
        visibleCount += 1;
      }
    });

    if (noMatchMessage) {
      noMatchMessage.classList.toggle("d-none", !(query && visibleCount === 0));
    }

    if (showMoreButton) {
      if (query) {
        showMoreButton.classList.add("d-none");
      } else {
        var hasHiddenRows = buttons.some(function(button) {
          return String(button.getAttribute("data-label-default-hidden") || "false") === "true";
        });
        showMoreButton.classList.toggle("d-none", !hasHiddenRows);
        showMoreButton.textContent = showAll ? "Show less" : "Show more";
      }
    }
  }

  function bindLabelOptionsRoot(rootElement) {
    if (!rootElement || rootElement.getAttribute("data-label-options-init") === "true") {
      return;
    }

    rootElement.setAttribute("data-label-options-init", "true");
    var list = rootElement.querySelector('[data-role="label-options-list"], [data-label-options-list]');
    if (list) {
      reorderLabelRows(list);
    }

    updateLabelListVisibility(rootElement);

    var searchInput = rootElement.querySelector('[data-action="search-labels"], [data-label-search-input]');
    if (searchInput) {
      searchInput.addEventListener("input", function() {
        updateLabelListVisibility(rootElement);
      });
    }

    var showMoreButton = rootElement.querySelector('[data-action="toggle-show-more-labels"], [data-label-show-more]');
    if (showMoreButton) {
      showMoreButton.addEventListener("click", function() {
        var expanded = showMoreButton.getAttribute("data-expanded") === "true";
        showMoreButton.setAttribute("data-expanded", expanded ? "false" : "true");
        updateLabelListVisibility(rootElement);
      });
    }

    rootElement.addEventListener("click", function(event) {
      var toggleButton = event.target.closest('[data-action="toggle-label"], [data-label-toggle]');
      if (!toggleButton || !rootElement.contains(toggleButton)) {
        return;
      }

      event.preventDefault();
      var slug = toggleButton.getAttribute("data-label-slug");
      if (!slug) {
        return;
      }
      if (isLabelSelected(toggleButton)) {
        mutateLabelQuery("remove", slug);
        return;
      }
      mutateLabelQuery("add", slug);
    });
  }

  function collectRoots(options) {
    var opts = options || {};
    if (opts.root) {
      return [opts.root];
    }

    var providedRoots = opts.roots || opts.labelOptionsRoots || [];
    if (providedRoots.length) {
      return providedRoots.filter(Boolean);
    }

    return Array.prototype.slice.call(document.querySelectorAll('[data-component="label-filter-options"]'));
  }

  function initLabelFilterOptions(options) {
    var roots = collectRoots(options || {});
    roots.forEach(function(root) {
      bindLabelOptionsRoot(root);
    });

    window.ClipsListLabelFilters = {
      add: function(labelSlug) {
        mutateLabelQuery("add", labelSlug);
      },
      remove: function(labelSlug) {
        mutateLabelQuery("remove", labelSlug);
      },
      clear: function() {
        mutateLabelQuery("clear");
      },
      setPanelState: function(panelState) {
        setPanelState(panelState);
      }
    };
  }

  window.LabelFilterOptionsComponent = {
    init: initLabelFilterOptions
  };
})();
