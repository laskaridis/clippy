(function () {
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
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message || "Failed to query active tab"));
          return;
        }

        var tab = tabs && tabs[0];
        if (!tab || !tab.id) {
          reject(new Error("No active tab found"));
          return;
        }

        chrome.tabs.sendMessage(tab.id, { type: "GET_CLIP_DATA" }, function (response) {
          if (chrome.runtime.lastError) {
            var msg = chrome.runtime.lastError.message || "Failed to contact content script";
            // Map the common "receiving end does not exist" case to a clearer explanation.
            if (msg.indexOf("Receiving end does not exist") !== -1) {
              msg =
                "This page does not allow the WebClippings extension to run. Try a normal website (not a Chrome settings or Web Store page).";
            }
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

          var clip = response.clip || {};
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
      chrome.runtime.sendMessage({ type: "SAVE_CLIP", clip: clip }, function (response) {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message || "Failed to send clip"));
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

  function setSaving(isSaving) {
    var button = document.getElementById("save-clip");
    if (!button) return;

    button.disabled = isSaving;
    if (isSaving) {
      button.textContent = "Saving...";
    } else {
      button.textContent = "Save selected text";
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("save-clip");
    if (!button) return;

    button.addEventListener("click", function () {
      setStatus("Capturing selection...", "");
      setSaving(true);

      requestClipFromActiveTab()
        .then(function (clip) {
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
