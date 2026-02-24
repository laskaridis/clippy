
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
    el.className = "";
    if (kind === "success") {
      el.classList.add("success");
    } else if (kind === "error") {
      el.classList.add("error");
    }
  }
  /**
   * Toggle the saving state of the save button in the popup.
   * @param {boolean} isSaving - Whether a clip save operation is in progress.
   */
  function setSaving(isSaving) {
    var button = document.getElementById("save-clip") as HTMLButtonElement | null;
    if (!button) return;

    button.disabled = isSaving;
    if (isSaving) {
      button.textContent = "Saving...";
    } else {
      button.textContent = "Save selected text";
    }
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
            "Failed to query active tab"
          );
          reject(new Error(queryMsg));
          return;
        }

        var tab = tabs && tabs[0];
        if (!tab || !tab.id) {
          reject(new Error("No active tab found"));
          return;
        }

        chrome.tabs.sendMessage(tab.id, { type: MESSAGE_TYPES.GET_CLIP_DATA }, function (response) {
          if (chrome.runtime && chrome.runtime.lastError) {
            var msg = mapChromeRuntimeErrorToMessage(
              chrome.runtime.lastError,
              "Failed to contact content script"
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

          var clip = (response.clip || {}) as { raw_content?: string; labels?: string[] };
          if (!clip.raw_content) {
            reject(new Error("No text selected. Select text on the page and try again."));
            return;
          }

          resolve(clip);
        });
      });
    });
  }

  /**
   * Send the clip to the background service worker to POST /api/clips/.
   */
  function saveClip(clip) {
    return new Promise(function (resolve, reject) {
      chrome.runtime.sendMessage({ type: MESSAGE_TYPES.SAVE_CLIP, clip: clip }, function (response) {
        if (chrome.runtime && chrome.runtime.lastError) {
          var sendMsg = mapChromeRuntimeErrorToMessage(
            chrome.runtime.lastError,
            "Failed to send clip"
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
      });
    });
  }
  /**
   * Initialize the popup once the DOM is ready by wiring up the save button 
   * click handler.
   */
  document.addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("save-clip") as HTMLButtonElement | null;
    var labelsInput = document.getElementById("labels-input") as HTMLInputElement | null;
    if (!button) return;

    button.addEventListener("click", function () {
      setStatus("Capturing selection...", "");
      setSaving(true);

      requestClipFromActiveTab()
        .then(function (clip: any) {
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
        .then(function () {
          setStatus("Clip saved successfully.", "success");
        })
        .catch(function (error) {
          setStatus(error && error.message ? error.message : "Failed to save clip.", "error");
        })
        .finally(function () {
          setSaving(false);
        });
    });
  });
})();
