(function() {
  function resolveSearchElements(rootElement) {
    var searchInput = rootElement.querySelector('[data-js="quick-search-input"]')
      || rootElement.querySelector("#quick-search-input");
    var searchPanel = rootElement.querySelector('[data-js="quick-search-panel"]')
      || rootElement.querySelector("#quick-search-panel");
    var searchResults = rootElement.querySelector('[data-js="quick-search-results-items"]')
      || rootElement.querySelector("#quick-search-results-items")
      || rootElement.querySelector('[data-js="quick-search-results"]')
      || rootElement.querySelector("#quick-search-results");

    return {
      searchInput: searchInput,
      searchPanel: searchPanel,
      searchResults: searchResults
    };
  }

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

  function clearActiveState(searchResults) {
    var items = searchResults.querySelectorAll("[data-result-item]");
    items.forEach(function(item) {
      item.classList.remove("global-auth-quick-search__item--active");
      item.setAttribute("aria-selected", "false");
    });
  }

  function setActiveItem(index, state) {
    var searchResults = state.searchResults;
    var searchInput = state.searchInput;
    var items = searchResults.querySelectorAll("[data-result-item]");
    if (!items.length) {
      state.activeIndex = -1;
      searchInput.removeAttribute("aria-activedescendant");
      return;
    }

    if (index < 0) {
      index = items.length - 1;
    } else if (index >= items.length) {
      index = 0;
    }

    clearActiveState(searchResults);
    state.activeIndex = index;
    var activeItem = items[state.activeIndex];
    activeItem.classList.add("global-auth-quick-search__item--active");
    activeItem.setAttribute("aria-selected", "true");
    searchInput.setAttribute("aria-activedescendant", activeItem.id);
    activeItem.scrollIntoView({ block: "nearest" });
  }

  function closePanel(state) {
    var searchInput = state.searchInput;
    var searchPanel = state.searchPanel;
    state.activeIndex = -1;
    searchInput.setAttribute("aria-expanded", "false");
    searchInput.removeAttribute("aria-activedescendant");
    searchPanel.classList.add("d-none");
  }

  function openPanel(state) {
    var searchInput = state.searchInput;
    var searchPanel = state.searchPanel;
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
    groupHtml += '<div class="global-auth-quick-search__group-title quick-search-group-title">' + title + "</div>";
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
      groupHtml += '<a href="' + safeTargetUrl + '" id="' + optionId + '" class="global-auth-quick-search__item list-group-item list-group-item-action quick-search-item" role="option" aria-selected="false" data-result-item>';
      if (item.type === "clip") {
        groupHtml += '<div class="global-auth-quick-search__clip-headline fw-semibold quick-search-clip-headline">' + safeSecondaryText + "</div>";
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
          groupHtml += '<div class="global-auth-quick-search__clip-meta quick-search-clip-meta">' + clipMeta + "</div>";
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

  function renderResults(payload, state) {
    var searchResults = state.searchResults;
    var hits = payload && payload.hits ? payload.hits : { clips: [], labels: [], websites: [] };
    var total = payload && typeof payload.total === "number" ? payload.total : 0;
    state.lastRenderedQuery = payload && typeof payload.query === "string" ? payload.query : "";

    searchResults.innerHTML = "";

    if (total === 0) {
      searchResults.innerHTML = '<div class="p-3 text-secondary">No results found.</div>';
      openPanel(state);
      return;
    }

    var html = "";
    html += renderGroup(hits.clips, "clips");
    html += renderGroup(hits.labels, "labels");
    html += renderGroup(hits.websites, "websites");
    searchResults.innerHTML = html;
    openPanel(state);
  }

  function fetchQuickSearch(query, state) {
    var searchResults = state.searchResults;
    if (state.abortController) {
      state.abortController.abort();
    }
    state.abortController = new AbortController();

    var endpoint = "/api/clips/quick-search/?q=" + encodeURIComponent(query);
    fetch(endpoint, {
      method: "GET",
      credentials: "same-origin",
      signal: state.abortController.signal,
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
      state.activeIndex = -1;
      renderResults(payload, state);
    }).catch(function(error) {
      if (error && error.name === "AbortError") {
        return;
      }
      searchResults.innerHTML = '<div class="p-3 text-secondary">Unable to load quick search results.</div>';
      openPanel(state);
    });
  }

  function abortInFlightRequest(state) {
    if (state.abortController) {
      state.abortController.abort();
      state.abortController = null;
    }
  }

  function bindQuickSearchRoot(rootElement) {
    if (!rootElement || rootElement.getAttribute("data-quick-search-init") === "true") {
      return;
    }

    var elements = resolveSearchElements(rootElement);
    var searchInput = elements.searchInput;
    var searchPanel = elements.searchPanel;
    var searchResults = elements.searchResults;

    if (!searchInput || !searchPanel || !searchResults) {
      return;
    }

    rootElement.setAttribute("data-quick-search-init", "true");
    var state = {
      searchInput: searchInput,
      searchPanel: searchPanel,
      searchResults: searchResults,
      activeIndex: -1,
      requestTimer: null,
      abortController: null,
      lastRenderedQuery: ""
    };

    searchInput.addEventListener("input", function() {
      var query = searchInput.value;

      if (state.requestTimer) {
        clearTimeout(state.requestTimer);
        state.requestTimer = null;
      }

      if (!query) {
        abortInFlightRequest(state);
        state.lastRenderedQuery = "";
        searchResults.innerHTML = "";
        closePanel(state);
        return;
      }

      var validation = validateQuery(query);
      if (!validation.valid) {
        abortInFlightRequest(state);
        closePanel(state);
        return;
      }

      state.requestTimer = setTimeout(function() {
        fetchQuickSearch(validation.query, state);
      }, 200);
    });

    searchInput.addEventListener("focus", function() {
      var query = searchInput.value;
      if (!query) {
        return;
      }

      var validation = validateQuery(query);
      if (!validation.valid) {
        closePanel(state);
        return;
      }

      if (validation.query === state.lastRenderedQuery && searchResults.innerHTML.trim()) {
        openPanel(state);
        return;
      }

      fetchQuickSearch(validation.query, state);
    });

    searchInput.addEventListener("keydown", function(event) {
      var items = searchResults.querySelectorAll("[data-result-item]");
      if (!items.length) {
        if (event.key === "Escape") {
          closePanel(state);
        }
        return;
      }

      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActiveItem(state.activeIndex + 1, state);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setActiveItem(state.activeIndex - 1, state);
      } else if (event.key === "Enter") {
        if (state.activeIndex >= 0 && state.activeIndex < items.length) {
          event.preventDefault();
          window.location.href = items[state.activeIndex].getAttribute("href");
        }
      } else if (event.key === "Escape") {
        event.preventDefault();
        closePanel(state);
      }
    });

    searchResults.addEventListener("mousemove", function(event) {
      var option = event.target.closest("[data-result-item]");
      if (!option) {
        return;
      }
      var items = Array.prototype.slice.call(searchResults.querySelectorAll("[data-result-item]"));
      setActiveItem(items.indexOf(option), state);
    });

    document.addEventListener("click", function(event) {
      if (!searchPanel.contains(event.target) && !rootElement.contains(event.target)) {
        closePanel(state);
      }
    });
  }

  function initGlobalAuthQuickSearch(options) {
    var opts = options || {};
    var roots = opts.roots || Array.prototype.slice.call(document.querySelectorAll('[data-component="global-auth-quick-search"]'));
    roots.forEach(function(root) {
      bindQuickSearchRoot(root);
    });
  }

  window.GlobalAuthQuickSearchComponent = {
    init: initGlobalAuthQuickSearch
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function() {
      initGlobalAuthQuickSearch();
    });
  } else {
    initGlobalAuthQuickSearch();
  }
})();
