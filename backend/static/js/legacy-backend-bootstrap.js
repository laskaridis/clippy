const scriptLoads = new Map()

function loadClassicScript(url) {
  const absoluteUrl = url.toString()
  if (scriptLoads.has(absoluteUrl)) {
    return scriptLoads.get(absoluteUrl)
  }

  const scriptLoad = new Promise(function(resolve, reject) {
    const existingScript = document.querySelector(
      'script[src="' + absoluteUrl + '"]'
    )
    if (existingScript) {
      resolve()
      return
    }

    const script = document.createElement("script")
    script.src = absoluteUrl
    script.async = false
    script.addEventListener("load", function() {
      resolve()
    })
    script.addEventListener("error", function() {
      scriptLoads.delete(absoluteUrl)
      reject(new Error("Failed to load backend script: " + absoluteUrl))
    })
    document.body.appendChild(script)
  })

  scriptLoads.set(absoluteUrl, scriptLoad)
  return scriptLoad
}

async function loadLegacyClipsListScripts() {
  await loadClassicScript(
    new URL("../clips/js/components/label-filter-options.js", import.meta.url)
  )
  await loadClassicScript(new URL("../clips/js/pages/list-page.js", import.meta.url))
}

async function bootstrapLegacyBackendScripts() {
  if (
    document.querySelector('[data-component="clips-list-layout"]')
    && !document.querySelector('[data-controller~="label-filter-options"]')
  ) {
    await loadLegacyClipsListScripts()
  }
}

export function startLegacyBackendBootstrap() {
  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      function onReady() {
        void bootstrapLegacyBackendScripts()
      },
      { once: true }
    )
    return
  }

  void bootstrapLegacyBackendScripts()
}
