import { Controller } from "../vendor/stimulus.js"

function buildPanelStateSearch(panelState) {
  const params = new URLSearchParams(window.location.search)
  const nextParams = new URLSearchParams()

  params.forEach((value, key) => {
    if (key !== "panel") {
      nextParams.append(key, value)
    }
  })

  if (panelState) {
    nextParams.set("panel", panelState)
  }

  return nextParams.toString()
}

export default class extends Controller {
  static targets = ["panel", "toggle"]

  toggle(event) {
    event.preventDefault()
    this.setExpanded(this.toggleTarget.getAttribute("aria-expanded") !== "true")
  }

  setExpanded(expanded, options = {}) {
    this.toggleTarget.setAttribute("aria-expanded", expanded ? "true" : "false")
    this.toggleTarget.textContent = expanded
      ? String(this.toggleTarget.getAttribute("data-expanded-label") || "Collapse")
      : String(this.toggleTarget.getAttribute("data-collapsed-label") || "Expand")

    this.panelTarget.classList.toggle("d-none", !expanded)
    this.element.classList.toggle("filter-sidebar--collapsed", !expanded)

    if (options.syncUrl !== false) {
      const nextSearch = buildPanelStateSearch(expanded ? "expanded" : "collapsed")
      const nextUrl = `${window.location.pathname}${nextSearch ? `?${nextSearch}` : ""}${window.location.hash}`
      window.history.replaceState({}, "", nextUrl)
    }
  }
}
