(function() {
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  var csrfToken = getCookie("csrftoken");

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

  function updateSelectedCount() {
    var params = new URLSearchParams(window.location.search);
    var selectedCount = normalizeLabelSlugs(params.getAll("label")).length;
    var counters = document.querySelectorAll("[data-selected-label-count]");
    counters.forEach(function(counter) {
      counter.textContent = String(selectedCount);
    });
  }

  function reorderLabelRows(listElement) {
    var buttons = Array.prototype.slice.call(listElement.querySelectorAll("[data-label-toggle]"));
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

  function updateLabelListVisibility(targetList) {
    var list = document.querySelector('[data-label-options-list][data-target-list="' + targetList + '"]');
    if (!list) {
      return;
    }

    var searchInput = document.querySelector('[data-label-search-input][data-target-list="' + targetList + '"]');
    var showMoreButton = document.querySelector('[data-label-show-more][data-target-list="' + targetList + '"]');
    var noMatchMessage = document.querySelector('[data-label-no-match][data-target-list="' + targetList + '"]');
    var query = String(searchInput ? searchInput.value : "").trim().toLowerCase();
    var showAll = showMoreButton
      && String(showMoreButton.getAttribute("data-expanded") || "false") === "true";

    var buttons = Array.prototype.slice.call(list.querySelectorAll("[data-label-toggle]"));
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

  function initializeLabelFilteringUI() {
    var mount = document.querySelector("[data-label-filter-sidebar-mount]");
    var sidebar = document.querySelector("[data-filter-sidebar-shell]");
    var sidebarPanel = document.querySelector("[data-filter-panel-body]");
    var sidebarToggle = document.querySelector("[data-filter-panel-toggle]");
    var drawer = document.querySelector("[data-filter-drawer]");
    var drawerTrigger = document.querySelector("[data-filter-drawer-trigger]");
    var drawerClose = document.querySelector("[data-filter-drawer-close]");
    var drawerBackdrop = document.querySelector("[data-filter-drawer-backdrop]");

    if (!mount) {
      return;
    }

    updateSelectedCount();

    var rawPanelState = String(mount.getAttribute("data-panel-state") || "collapsed");

    function openDrawer(options) {
      var opts = options || {};
      if (!drawer || !drawerBackdrop || !drawerTrigger) {
        return;
      }

      drawer.classList.remove("d-none");
      drawerBackdrop.classList.remove("d-none");
      drawer.setAttribute("aria-hidden", "false");
      drawerTrigger.setAttribute("aria-expanded", "true");

      if (opts.syncUrl !== false) {
        setPanelState("open");
      }

      if (opts.moveFocus !== false) {
        var focusTarget = drawer.querySelector('[data-label-search-input][data-target-list="drawer"]') || drawerClose;
        if (focusTarget) {
          focusTarget.focus();
        }
      }
    }

    function closeDrawer(options) {
      var opts = options || {};
      if (!drawer || !drawerBackdrop || !drawerTrigger) {
        return;
      }

      drawer.classList.add("d-none");
      drawerBackdrop.classList.add("d-none");
      drawer.setAttribute("aria-hidden", "true");
      drawerTrigger.setAttribute("aria-expanded", "false");

      if (opts.syncUrl !== false) {
        setPanelState("closed");
      }

      if (opts.returnFocus !== false) {
        drawerTrigger.focus();
      }
    }

    if (sidebar && sidebarPanel && sidebarToggle) {
      sidebarToggle.addEventListener("click", function() {
        var currentlyExpanded = sidebarToggle.getAttribute("aria-expanded") === "true";
        var nextExpanded = !currentlyExpanded;
        sidebarToggle.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
        sidebarToggle.textContent = nextExpanded
          ? String(sidebarToggle.getAttribute("data-expanded-label") || "Collapse")
          : String(sidebarToggle.getAttribute("data-collapsed-label") || "Expand");
        sidebarPanel.classList.toggle("d-none", !nextExpanded);
        sidebar.classList.toggle("is-collapsed", !nextExpanded);
        setPanelState(nextExpanded ? "expanded" : "collapsed");
      });
    }

    if (drawerTrigger) {
      drawerTrigger.addEventListener("click", function() {
        openDrawer();
      });
    }

    if (drawerClose) {
      drawerClose.addEventListener("click", function() {
        closeDrawer();
      });
    }

    if (drawerBackdrop) {
      drawerBackdrop.addEventListener("click", function() {
        closeDrawer();
      });
    }

    document.addEventListener("keydown", function(event) {
      if (event.key !== "Escape") {
        return;
      }
      if (drawer && !drawer.classList.contains("d-none")) {
        closeDrawer();
      }
    });

    if (rawPanelState === "open") {
      openDrawer({ syncUrl: false, moveFocus: false });
    }

    ["sidebar", "drawer"].forEach(function(targetList) {
      var list = document.querySelector('[data-label-options-list][data-target-list="' + targetList + '"]');
      if (list) {
        reorderLabelRows(list);
        updateLabelListVisibility(targetList);
      }

      var searchInput = document.querySelector('[data-label-search-input][data-target-list="' + targetList + '"]');
      if (searchInput) {
        searchInput.addEventListener("input", function() {
          updateLabelListVisibility(targetList);
        });
      }

      var showMoreButton = document.querySelector('[data-label-show-more][data-target-list="' + targetList + '"]');
      if (showMoreButton) {
        showMoreButton.addEventListener("click", function() {
          var expanded = showMoreButton.getAttribute("data-expanded") === "true";
          showMoreButton.setAttribute("data-expanded", expanded ? "false" : "true");
          updateLabelListVisibility(targetList);
        });
      }
    });
  }

  function bindLabelQueryActions() {
    document.addEventListener("click", function(event) {
      var addLink = event.target.closest("[data-label-add-link]");
      if (addLink) {
        event.preventDefault();
        mutateLabelQuery("add", addLink.getAttribute("data-label-slug"));
        return;
      }

      var removeButton = event.target.closest("[data-label-pill-remove]");
      if (removeButton) {
        event.preventDefault();
        mutateLabelQuery("remove", removeButton.getAttribute("data-label-slug"));
        return;
      }

      var clearButton = event.target.closest("[data-label-clear-all]");
      if (clearButton) {
        event.preventDefault();
        mutateLabelQuery("clear");
        return;
      }

      var toggleButton = event.target.closest("[data-label-toggle]");
      if (toggleButton) {
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
      }
    });
  }

  bindLabelQueryActions();
  initializeLabelFilteringUI();

  window.ClipsListLabelFilters = {
    add: function(labelSlug) {
      mutateLabelQuery("add", labelSlug);
    },
    remove: function(labelSlug) {
      mutateLabelQuery("remove", labelSlug);
    },
    clear: function() {
      mutateLabelQuery("clear");
    }
  };

  var buttons = document.querySelectorAll(".clip-delete");
  buttons.forEach(function(button) {
    button.addEventListener("click", function(event) {
      event.preventDefault();
      var url = button.getAttribute("data-delete-url");
      if (!url) {
        return;
      }

      fetch(url, {
        method: "DELETE",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin"
      }).then(function(response) {
        if (response.status === 204 || response.status === 200) {
          var row = button.closest("[data-clip-row]");
          if (row) {
            row.remove();
          }
        } else if (response.status === 403) {
          alert("You are not allowed to delete this clip.");
        } else {
          alert("Failed to delete clip.");
        }
      }).catch(function() {
        alert("Failed to delete clip.");
      });
    });
  });

  var searchInput = document.getElementById("quick-search-input");
  var searchPanel = document.getElementById("quick-search-panel");
  var searchResults = document.getElementById("quick-search-results-items")
    || document.getElementById("quick-search-results");
  var activeIndex = -1;
  var requestTimer = null;
  var abortController = null;
  var lastRenderedQuery = "";

  function normalizeQuery(query) {
    return String(query || "").trim();
  }

  function validateQuery(query) {
    var normalizedQuery = normalizeQuery(query);
    if (normalizedQuery.length < 3) {
      return { valid: false, message: "Type at least 3 characters to search." };
    }
    if (normalizedQuery.length > 50) {
      return { valid: false, message: "Search must be 50 characters or less." };
    }
    return { valid: true, message: "", query: normalizedQuery };
  }

  function clearActiveState() {
    var items = searchResults.querySelectorAll("[data-result-item]");
    items.forEach(function(item) {
      item.classList.remove("active");
      item.setAttribute("aria-selected", "false");
    });
  }

  function setActiveItem(index) {
    var items = searchResults.querySelectorAll("[data-result-item]");
    if (!items.length) {
      activeIndex = -1;
      searchInput.removeAttribute("aria-activedescendant");
      return;
    }

    if (index < 0) {
      index = items.length - 1;
    } else if (index >= items.length) {
      index = 0;
    }

    clearActiveState();
    activeIndex = index;
    var activeItem = items[activeIndex];
    activeItem.classList.add("active");
    activeItem.setAttribute("aria-selected", "true");
    searchInput.setAttribute("aria-activedescendant", activeItem.id);
    activeItem.scrollIntoView({ block: "nearest" });
  }

  function closePanel() {
    activeIndex = -1;
    searchInput.setAttribute("aria-expanded", "false");
    searchInput.removeAttribute("aria-activedescendant");
    searchPanel.classList.add("d-none");
  }

  function openPanel() {
    searchInput.setAttribute("aria-expanded", "true");
    searchPanel.classList.remove("d-none");
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function renderHighlightedSnippet(value) {
    var escaped = escapeHtml(value || "");
    return escaped
      .replace(/&lt;b&gt;/g, "<b>")
      .replace(/&lt;\/b&gt;/g, "</b>");
  }

  function renderGroup(items, title) {
    if (!items || !items.length) {
      return "";
    }

    var groupHtml = '<div class="p-2 border-bottom">';
    groupHtml += '<div class="quick-search-group-title">' + title + "</div>";
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var secondaryText = "";
      var tertiaryText = "";
      if (item.type === "clip") {
        secondaryText = item.snippet || item.url || "";
        tertiaryText = item.title || "";
      } else if (item.type === "label") {
        secondaryText = item.clip_count + " clips";
      } else {
        secondaryText = item.clip_count + " clips";
      }

      var label = item.title || item.name || item.url || "Result";
      var safeLabel = escapeHtml(label);
      var safeSecondaryText = item.type === "clip"
        ? renderHighlightedSnippet(secondaryText)
        : escapeHtml(secondaryText);
      var safeTertiaryText = escapeHtml(tertiaryText);
      var safeUrl = escapeHtml(item.url || "");
      var safeTargetUrl = escapeHtml(item.target_url || "#");
      var optionId = "quick-search-option-" + title + "-" + i + "-" + Math.abs(label.length + i);
      groupHtml += '<a href="' + safeTargetUrl + '" id="' + optionId + '" class="list-group-item list-group-item-action quick-search-item" role="option" aria-selected="false" data-result-item>';
      if (item.type === "clip") {
        groupHtml += '<div class="fw-semibold quick-search-clip-headline">' + safeSecondaryText + "</div>";
        if (tertiaryText || item.url) {
          var clipMeta = "";
          if (tertiaryText) {
            clipMeta += safeTertiaryText;
          }
          if (item.url) {
            if (clipMeta) {
              clipMeta += " · ";
            }
            clipMeta += safeUrl;
          }
          groupHtml += '<div class="quick-search-clip-meta">' + clipMeta + "</div>";
        }
      } else {
        groupHtml += '<div class="fw-semibold">' + safeLabel + "</div>";
        if (secondaryText) {
          groupHtml += '<div class="small text-secondary">' + safeSecondaryText + "</div>";
        }
      }
      groupHtml += "</a>";
    }
    groupHtml += "</div>";
    return groupHtml;
  }

  function renderResults(payload) {
    var hits = payload && payload.hits ? payload.hits : { clips: [], labels: [], websites: [] };
    var total = payload && typeof payload.total === "number" ? payload.total : 0;
    lastRenderedQuery = payload && typeof payload.query === "string" ? payload.query : "";

    searchResults.innerHTML = "";

    if (total === 0) {
      searchResults.innerHTML = '<div class="p-3 text-secondary">No results found.</div>';
      openPanel();
      return;
    }

    var html = "";
    html += renderGroup(hits.clips, "clips");
    html += renderGroup(hits.labels, "labels");
    html += renderGroup(hits.websites, "websites");
    searchResults.innerHTML = html;
    openPanel();
  }

  function fetchQuickSearch(query) {
    if (abortController) {
      abortController.abort();
    }
    abortController = new AbortController();

    var endpoint = "/api/clips/quick-search/?q=" + encodeURIComponent(query);
    fetch(endpoint, {
      method: "GET",
      credentials: "same-origin",
      signal: abortController.signal,
      headers: {
        Accept: "application/json"
      }
    }).then(function(response) {
      if (!response.ok) {
        return response.json().then(function(errorBody) {
          throw errorBody;
        });
      }
      return response.json();
    }).then(function(payload) {
      activeIndex = -1;
      renderResults(payload);
    }).catch(function(error) {
      if (error && error.name === "AbortError") {
        return;
      }
      searchResults.innerHTML = '<div class="p-3 text-secondary">Unable to load quick search results.</div>';
      openPanel();
    });
  }

  function abortInFlightRequest() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
  }

  if (!searchInput || !searchPanel || !searchResults) {
    return;
  }

  searchInput.addEventListener("input", function() {
    var query = searchInput.value;

    if (requestTimer) {
      clearTimeout(requestTimer);
      requestTimer = null;
    }

    if (!query) {
      abortInFlightRequest();
      lastRenderedQuery = "";
      searchResults.innerHTML = "";
      closePanel();
      return;
    }

    var validation = validateQuery(query);
    if (!validation.valid) {
      abortInFlightRequest();
      closePanel();
      return;
    }

    requestTimer = setTimeout(function() {
      fetchQuickSearch(validation.query);
    }, 200);
  });

  searchInput.addEventListener("focus", function() {
    var query = searchInput.value;
    if (!query) {
      return;
    }

    var validation = validateQuery(query);
    if (!validation.valid) {
      closePanel();
      return;
    }

    if (validation.query === lastRenderedQuery && searchResults.innerHTML.trim()) {
      openPanel();
      return;
    }

    fetchQuickSearch(validation.query);
  });

  searchInput.addEventListener("keydown", function(event) {
    var items = searchResults.querySelectorAll("[data-result-item]");
    if (!items.length) {
      if (event.key === "Escape") {
        closePanel();
      }
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveItem(activeIndex + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveItem(activeIndex - 1);
    } else if (event.key === "Enter") {
      if (activeIndex >= 0 && activeIndex < items.length) {
        event.preventDefault();
        window.location.href = items[activeIndex].getAttribute("href");
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      closePanel();
    }
  });

  searchResults.addEventListener("mousemove", function(event) {
    var option = event.target.closest("[data-result-item]");
    if (!option) {
      return;
    }
    var items = Array.prototype.slice.call(searchResults.querySelectorAll("[data-result-item]"));
    setActiveItem(items.indexOf(option));
  });

  document.addEventListener("click", function(event) {
    if (!searchPanel.contains(event.target) && event.target !== searchInput) {
      closePanel();
    }
  });
})();
