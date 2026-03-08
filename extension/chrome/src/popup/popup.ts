(function () {
  /**
   * Update the popup status message and styling.
   * @param {string} message - Text to display in the status area.
   * @param {"success"|"error"|""} [kind] - Visual style for the status message.
   */
  function setStatus(message, kind) {
    var el = document.getElementById("status");
    if (!el) return;

    el.textContent = message || "";
    el.className = "small mt-3";
    if (kind === "success") {
      el.classList.add("text-success");
    } else if (kind === "error") {
      el.classList.add("text-danger");
    } else {
      el.classList.add("text-secondary");
    }
  }

  /**
   * Toggle the UI that allows saving clips based on authentication state.
   */
  function setAuthenticatedUi(isAuthenticated) {
    var saveControls = document.getElementById("save-controls");
    var authControls = document.getElementById("auth-controls");
    var labelsInput = document.getElementById("labels-input");
    var labelsLabel = document.querySelector(
      'label[for="labels-input"]',
    ) as HTMLElement | null;
    var saveButton = document.getElementById("save-clip");
    if (saveControls) {
      saveControls.style.display = isAuthenticated ? "block" : "none";
      saveControls.classList.toggle("d-none", !isAuthenticated);
    }

    if (authControls) {
      authControls.style.display = isAuthenticated ? "none" : "block";
      authControls.classList.toggle("d-none", isAuthenticated);
    }

    // Defensive fallback: if older popup HTML is loaded without wrappers,
    // still enforce signed-in/signed-out control visibility.
    if (labelsInput) {
      (labelsInput as HTMLElement).style.display = isAuthenticated
        ? "block"
        : "none";
      (labelsInput as HTMLElement).classList.toggle("d-none", !isAuthenticated);
    }

    if (labelsLabel) {
      labelsLabel.style.display = isAuthenticated ? "block" : "none";
      labelsLabel.classList.toggle("d-none", !isAuthenticated);
    }

    if (saveButton) {
      (saveButton as HTMLElement).style.display = isAuthenticated
        ? "inline-flex"
        : "none";
      (saveButton as HTMLElement).classList.toggle("d-none", !isAuthenticated);
    }

    if (!isAuthenticated) {
      var allButtons = document.querySelectorAll("button");
      for (var i = 0; i < allButtons.length; i += 1) {
        var currentButton = allButtons[i] as HTMLButtonElement;
        var text = (currentButton.textContent || "").toLowerCase();
        if (currentButton.id !== "open-login" && text.indexOf("save") !== -1) {
          currentButton.style.display = "none";
        }
      }

      var textInputs = document.querySelectorAll('input[type="text"]');
      for (var j = 0; j < textInputs.length; j += 1) {
        (textInputs[j] as HTMLElement).style.display = "none";
      }
    }
  }

  /**
   * Toggle the saving state of the save button in the popup.
   * @param {boolean} isSaving - Whether a clip save operation is in progress.
   * @param {boolean} hasSelection - Whether there is selected text to save.
   * @param {boolean} alreadySaved - Whether the current selection was already saved.
   */
  function setSaving(isSaving, hasSelection, alreadySaved) {
    var button = document.getElementById(
      "save-clip",
    ) as HTMLButtonElement | null;
    if (!button) return;

    button.disabled = isSaving || !hasSelection || alreadySaved;
    if (isSaving) {
      button.textContent = "Saving...";
    } else if (alreadySaved) {
      button.textContent = "Already saved";
    } else {
      button.textContent = "Save selected text";
    }
  }

  /**
   * Ask background service worker whether the user is authenticated.
   */
  function requestAuthStatus() {
    return new Promise(function (resolve, reject) {
      chrome.runtime.sendMessage(
        { type: MESSAGE_TYPES.GET_AUTH_STATUS },
        function (response) {
          if (chrome.runtime && chrome.runtime.lastError) {
            var sendMsg = mapChromeRuntimeErrorToMessage(
              chrome.runtime.lastError,
              "Failed to check sign-in status",
            );
            reject(new Error(sendMsg));
            return;
          }

          if (!response || !response.success) {
            reject(
              new Error(
                (response && response.error) ||
                  "Failed to check sign-in status",
              ),
            );
            return;
          }

          resolve(Boolean(response.isAuthenticated));
        },
      );
    });
  }

  function openLoginPage() {
    if (typeof getLoginPageUrl !== "function") {
      return;
    }
    var loginUrl = getLoginPageUrl();

    if (chrome.tabs && chrome.tabs.create) {
      chrome.tabs.create({ url: loginUrl });
      return;
    }

    window.open(loginUrl, "_blank", "noopener,noreferrer");
  }

  /**
   * Get clip data from the active tab via the content script.
   * Resolves with { title, url, raw_content } or rejects with an Error.
   */
  function requestClipFromActiveTab() {
    return new Promise(function (resolve, reject) {
      if (!chrome.tabs || !chrome.tabs.query) {
        reject(new Error("Tabs API not available"));
        return;
      }

      chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        if (chrome.runtime && chrome.runtime.lastError) {
          var queryMsg = mapChromeRuntimeErrorToMessage(
            chrome.runtime.lastError,
            "Failed to query active tab",
          );
          reject(new Error(queryMsg));
          return;
        }

        var tab = tabs && tabs[0];
        if (!tab || !tab.id) {
          reject(new Error("No active tab found"));
          return;
        }

        chrome.tabs.sendMessage(
          tab.id,
          { type: MESSAGE_TYPES.GET_CLIP_DATA },
          function (response) {
            if (chrome.runtime && chrome.runtime.lastError) {
              var msg = mapChromeRuntimeErrorToMessage(
                chrome.runtime.lastError,
                "Failed to contact content script",
              );
              reject(new Error(msg));
              return;
            }

            if (!response || !response.success) {
              var message =
                (response && response.error) ||
                "Could not capture selection. Make sure some text is selected.";
              reject(new Error(message));
              return;
            }

            var clip = (response.clip || {}) as {
              raw_content?: string;
              labels?: string[];
            };
            if (!clip.raw_content) {
              reject(
                new Error(
                  "No text selected. Select text on the page and try again.",
                ),
              );
              return;
            }

            resolve(clip);
          },
        );
      });
    });
  }

  /**
   * Build a compact fragment to preview the selected text in the popup.
   * @param {string} rawContent - Full selected text from the page.
   * @returns {string}
   */
  function buildSelectionPreview(rawContent) {
    var normalized = (rawContent || "").replace(/\s+/g, " ").trim();
    if (!normalized) {
      return "No text selected on active page.";
    }

    var maxLength = 120;
    if (normalized.length <= maxLength) {
      return normalized;
    }

    return normalized.slice(0, maxLength) + "...";
  }

  /**
   * Build a normalized key used for duplicate-submission checks.
   * @param {string} rawContent - Full selected text from the page.
   * @returns {string}
   */
  function buildSelectionKey(rawContent) {
    return (rawContent || "").replace(/\s+/g, " ").trim();
  }

  /**
   * Update the selected text preview in the popup.
   * @param {string} text - Preview text to render.
   */
  function setSelectionPreview(text) {
    var previewEl = document.getElementById("selection-preview-text");
    if (!previewEl) return;

    previewEl.textContent = text;
  }

  /**
   * Send the clip to the background service worker to POST /api/clips/.
   */
  function saveClip(clip) {
    return new Promise(function (resolve, reject) {
      chrome.runtime.sendMessage(
        { type: MESSAGE_TYPES.SAVE_CLIP, clip: clip },
        function (response) {
          if (chrome.runtime && chrome.runtime.lastError) {
            var sendMsg = mapChromeRuntimeErrorToMessage(
              chrome.runtime.lastError,
              "Failed to send clip",
            );
            reject(new Error(sendMsg));
            return;
          }

          if (!response || !response.success) {
            var message =
              (response && response.error) ||
              "Failed to save clip. Check that you are signed in.";
            reject(new Error(message));
            return;
          }

          resolve(response.clip || null);
        },
      );
    });
  }

  /**
   * Initialize the popup once the DOM is ready by wiring up handlers.
   */
  document.addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById(
      "save-clip",
    ) as HTMLButtonElement | null;
    var labelsInput = document.getElementById(
      "labels-input",
    ) as HTMLInputElement | null;
    var hasSelection = false;
    var currentSelectionKey = "";
    var lastSavedSelectionKey = "";
    var hasSavedCurrentSelection = false;
    var authControls = document.getElementById("auth-controls");
    if (!authControls) {
      authControls = document.createElement("div");
      authControls.id = "auth-controls";
      authControls.className = "mt-2";

      var fallbackLoginButton = document.createElement("button");
      fallbackLoginButton.id = "open-login";
      fallbackLoginButton.textContent = "Log in";
      fallbackLoginButton.className = "btn btn-outline-light btn-sm w-100";
      authControls.appendChild(fallbackLoginButton);

      var statusEl = document.getElementById("status");
      if (statusEl && statusEl.parentNode) {
        statusEl.parentNode.insertBefore(authControls, statusEl);
      } else {
        document.body.appendChild(authControls);
      }
    }

    var loginButton = document.getElementById(
      "open-login",
    ) as HTMLButtonElement | null;

    if (loginButton) {
      loginButton.addEventListener("click", openLoginPage);
    }

    requestAuthStatus()
      .then(function (isAuthenticated) {
        setAuthenticatedUi(Boolean(isAuthenticated));
        if (!isAuthenticated) {
          setStatus("Sign in to WebClippings to save this clip.", "");
        }
      })
      .catch(function (error) {
        setAuthenticatedUi(false);
        setStatus(
          error && error.message
            ? error.message
            : "Unable to check sign-in status.",
          "error",
        );
      });

    requestClipFromActiveTab()
      .then(function (clip: any) {
        currentSelectionKey = buildSelectionKey(clip.raw_content || "");
        hasSelection = currentSelectionKey.length > 0;
        hasSavedCurrentSelection =
          hasSelection && currentSelectionKey === lastSavedSelectionKey;
        setSelectionPreview(buildSelectionPreview(clip.raw_content || ""));
        setSaving(false, hasSelection, hasSavedCurrentSelection);
      })
      .catch(function () {
        currentSelectionKey = "";
        hasSelection = false;
        hasSavedCurrentSelection = false;
        setSelectionPreview("No text selected on active page.");
        setSaving(false, hasSelection, hasSavedCurrentSelection);
      });

    if (!button) return;
    setSaving(false, hasSelection, hasSavedCurrentSelection);

    button.addEventListener("click", function () {
      if (!hasSelection) {
        setStatus(
          "No text selected. Select text on the page and try again.",
          "error",
        );
        return;
      }
      if (hasSavedCurrentSelection) {
        setStatus("This selected text was already saved.", "");
        setSaving(false, hasSelection, hasSavedCurrentSelection);
        return;
      }

      setStatus("Capturing selection...", "");
      setSaving(true, hasSelection, hasSavedCurrentSelection);

      requestClipFromActiveTab()
        .then(function (clip: any) {
          currentSelectionKey = buildSelectionKey(clip.raw_content || "");
          hasSelection = currentSelectionKey.length > 0;
          hasSavedCurrentSelection =
            hasSelection && currentSelectionKey === lastSavedSelectionKey;
          setSelectionPreview(buildSelectionPreview(clip.raw_content || ""));
          if (hasSavedCurrentSelection) {
            setStatus("This selected text was already saved.", "");
            return null;
          }

          // Attach labels from the popup input (comma-separated names).
          if (labelsInput && labelsInput.value) {
            var names = labelsInput.value.split(",");
            var labels = names
              .map(function (name) {
                return name.trim();
              })
              .filter(function (name) {
                return name.length > 0;
              });
            clip.labels = labels;
          } else {
            clip.labels = [];
          }

          setStatus("Sending to WebClippings...", "");
          return saveClip(clip);
        })
        .then(function (savedClip) {
          if (!savedClip) return;
          lastSavedSelectionKey = currentSelectionKey;
          hasSavedCurrentSelection = true;
          setStatus("Clip saved successfully.", "success");
        })
        .catch(function (error) {
          var message =
            error && error.message ? error.message : "Failed to save clip.";
          if (message.toLowerCase().indexOf("no text selected") !== -1) {
            currentSelectionKey = "";
            hasSelection = false;
            hasSavedCurrentSelection = false;
            setSelectionPreview("No text selected on active page.");
          }
          setStatus(message, "error");
        })
        .finally(function () {
          setSaving(false, hasSelection, hasSavedCurrentSelection);
        });
    });
  });
})();
