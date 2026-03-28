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

  function bindClipCard(rootElement, csrfToken) {
    if (!rootElement || rootElement.getAttribute("data-clip-card-init") === "true") {
      return;
    }

    var button = rootElement.querySelector('[data-action="delete-clip"], [data-delete-url]');
    if (!button) {
      return;
    }

    rootElement.setAttribute("data-clip-card-init", "true");
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
          rootElement.remove();
        } else if (response.status === 403) {
          alert("You are not allowed to delete this clip.");
        } else {
          alert("Failed to delete clip.");
        }
      }).catch(function() {
        alert("Failed to delete clip.");
      });
    });
  }

  function initClipCard(options) {
    var csrfToken = getCookie("csrftoken");
    var opts = options || {};
    var rootElement = opts.root;

    if (rootElement) {
      bindClipCard(rootElement, csrfToken);
      return;
    }

    var roots = Array.prototype.slice.call(document.querySelectorAll('[data-component="clip-card"]'));
    roots.forEach(function(root) {
      bindClipCard(root, csrfToken);
    });
  }

  window.ClipCardComponent = {
    init: initClipCard
  };
})();
