(function() {
  function toArray(nodeList) {
    return Array.prototype.slice.call(nodeList || []);
  }

  function getLabelFiltersApi() {
    if (window.ClipsListLabelFilters) {
      return window.ClipsListLabelFilters;
    }
    return null;
  }

  function setPanelState(panelState) {
    var labelFiltersApi = getLabelFiltersApi();
    if (labelFiltersApi && typeof labelFiltersApi.setPanelState === "function") {
      labelFiltersApi.setPanelState(panelState);
      return;
    }

    var params = new URLSearchParams(window.location.search);
    var nextParams = new URLSearchParams();
    params.forEach(function(value, key) {
      if (key !== "panel") {
        nextParams.append(key, value);
      }
    });
    if (panelState) {
      nextParams.set("panel", panelState);
    }

    var nextSearch = nextParams.toString();
    var nextUrl = window.location.pathname + (nextSearch ? "?" + nextSearch : "") + window.location.hash;
    window.history.replaceState({}, "", nextUrl);
  }

  function navigateToAnchorHref(anchorElement) {
    if (!anchorElement) {
      return false;
    }

    var targetHref = anchorElement.getAttribute("href");
    if (!targetHref) {
      return false;
    }

    window.location.assign(targetHref);
    return true;
  }

  function updateSelectedCount(selectedCountTargets) {
    var selectedCount = new URLSearchParams(window.location.search).getAll("label").length;
    selectedCountTargets.forEach(function(counter) {
      counter.textContent = String(selectedCount);
    });
  }

  function bindPageLabelActions(interactionRoots) {
    interactionRoots.forEach(function(root) {
      if (!root || root.getAttribute("data-page-label-actions-init") === "true") {
        return;
      }

      root.setAttribute("data-page-label-actions-init", "true");
      root.addEventListener("click", function(event) {
        var labelFiltersApi = getLabelFiltersApi();
        if (!labelFiltersApi) {
          return;
        }

        var addLink = event.target.closest('[data-action="add-label-filter"], [data-label-add-link]');
        if (addLink && root.contains(addLink)) {
          event.preventDefault();
          labelFiltersApi.add(addLink.getAttribute("data-label-slug"));
          return;
        }

        var removeButton = event.target.closest('[data-action="remove-label-filter"], [data-label-pill-remove]');
        if (removeButton && root.contains(removeButton)) {
          event.preventDefault();
          labelFiltersApi.remove(removeButton.getAttribute("data-label-slug"));
          return;
        }

        var clearButton = event.target.closest('[data-action="clear-label-filters"]');
        if (clearButton && root.contains(clearButton)) {
          event.preventDefault();
          if (!navigateToAnchorHref(clearButton)) {
            labelFiltersApi.clear();
          }
        }
      });
    });
  }

  function initPanelControls(options) {
    var opts = options || {};
    var mount = opts.mount;
    var sidebar = opts.sidebar;
    var sidebarPanel = opts.sidebarPanel;
    var sidebarToggle = opts.sidebarToggle;
    var drawer = opts.drawer;
    var drawerTrigger = opts.drawerTrigger;
    var drawerClose = opts.drawerClose;
    var drawerBackdrop = opts.drawerBackdrop;

    if (!mount) {
      return;
    }

    var rawPanelState = String(mount.getAttribute("data-panel-state") || "collapsed");

    function openDrawer(drawerOptions) {
      var localOptions = drawerOptions || {};
      if (!drawer || !drawerBackdrop || !drawerTrigger) {
        return;
      }

      drawer.classList.remove("d-none");
      drawerBackdrop.classList.remove("d-none");
      drawer.setAttribute("aria-hidden", "false");
      drawerTrigger.setAttribute("aria-expanded", "true");

      if (localOptions.syncUrl !== false) {
        setPanelState("open");
      }

      if (localOptions.moveFocus !== false) {
        var focusTarget = drawer.querySelector('[data-action="search-labels"], [data-label-search-input]') || drawerClose;
        if (focusTarget) {
          focusTarget.focus();
        }
      }
    }

    function closeDrawer(drawerOptions) {
      var localOptions = drawerOptions || {};
      if (!drawer || !drawerBackdrop || !drawerTrigger) {
        return;
      }

      drawer.classList.add("d-none");
      drawerBackdrop.classList.add("d-none");
      drawer.setAttribute("aria-hidden", "true");
      drawerTrigger.setAttribute("aria-expanded", "false");

      if (localOptions.syncUrl !== false) {
        setPanelState("closed");
      }

      if (localOptions.returnFocus !== false) {
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
        sidebar.classList.toggle("filter-sidebar--collapsed", !nextExpanded);
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

    if (drawer && drawer.getAttribute("data-drawer-escape-init") !== "true") {
      drawer.setAttribute("data-drawer-escape-init", "true");
      document.addEventListener("keydown", function(event) {
        if (event.key !== "Escape") {
          return;
        }
        if (!drawer.classList.contains("d-none")) {
          closeDrawer();
        }
      });
    }

    if (rawPanelState === "open") {
      openDrawer({ syncUrl: false, moveFocus: false });
    }
  }

  function initListPage() {
    var listLayout = document.querySelector('[data-component="clips-list-layout"]');
    if (!listLayout) {
      return;
    }

    var mount = document.querySelector("[data-label-filter-sidebar-mount]");
    var sidebar = listLayout.querySelector('[data-component="filter-sidebar"]');
    var sidebarPanel = sidebar
      ? sidebar.querySelector('[data-role="filter-panel-body"], [data-filter-panel-body]')
      : null;
    var sidebarToggle = sidebar
      ? sidebar.querySelector('[data-action="toggle-filter-panel"], [data-filter-panel-toggle]')
      : null;
    var drawer = document.querySelector('[data-component="filter-drawer"]');
    var drawerTrigger = listLayout.querySelector('[data-action="open-filter-drawer"], [data-filter-drawer-trigger]');
    var drawerClose = drawer
      ? drawer.querySelector('[data-action="close-filter-drawer"], [data-filter-drawer-close]')
      : null;
    var drawerBackdrop = document.querySelector('[data-component="filter-drawer-backdrop"]');

    var labelOptionsRoots = toArray(document.querySelectorAll('[data-component="label-filter-options"]'));
    if (window.LabelFilterOptionsComponent && typeof window.LabelFilterOptionsComponent.init === "function") {
      window.LabelFilterOptionsComponent.init({ roots: labelOptionsRoots });
    }

    bindPageLabelActions([listLayout, drawer]);

    initPanelControls({
      mount: mount,
      sidebar: sidebar,
      sidebarPanel: sidebarPanel,
      sidebarToggle: sidebarToggle,
      drawer: drawer,
      drawerTrigger: drawerTrigger,
      drawerClose: drawerClose,
      drawerBackdrop: drawerBackdrop
    });

    var selectedCountTargets = toArray(
      document.querySelectorAll('[data-role="selected-label-count"], [data-selected-label-count]')
    );
    updateSelectedCount(selectedCountTargets);

  }

  initListPage();
})();
