import { Controller } from "../vendor/stimulus.js"

const OPEN_EVENT = "clips:filter-drawer:open"
const STATE_EVENT = "clips:filter-drawer:state"

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
  static targets = ["backdrop", "closeButton", "panel"]

  static values = {
    initialPanelState: String,
  }

  connect() {
    this.lastTrigger = null
    this.boundHandleOpenEvent = this.handleOpenEvent.bind(this)
    this.boundHandleKeydown = this.handleKeydown.bind(this)

    document.addEventListener(OPEN_EVENT, this.boundHandleOpenEvent)
    document.addEventListener("keydown", this.boundHandleKeydown)

    if (this.initialPanelStateValue === "open") {
      this.open({ syncUrl: false, moveFocus: false })
      return
    }

    this.close({ syncUrl: false, returnFocus: false })
  }

  disconnect() {
    document.removeEventListener(OPEN_EVENT, this.boundHandleOpenEvent)
    document.removeEventListener("keydown", this.boundHandleKeydown)
  }

  handleOpenEvent(event) {
    this.lastTrigger = event.detail?.sourceElement || null
    this.open({
      syncUrl: event.detail?.syncUrl !== false,
      moveFocus: event.detail?.moveFocus !== false,
    })
  }

  handleKeydown(event) {
    if (event.key !== "Escape" || !this.isOpen) {
      return
    }

    event.preventDefault()
    this.close()
  }

  open(options = {}) {
    this.panelTarget.classList.remove("d-none")
    this.backdropTarget.classList.remove("d-none")
    this.panelTarget.setAttribute("aria-hidden", "false")
    this.backdropTarget.setAttribute("aria-hidden", "false")

    if (options.syncUrl !== false) {
      this.syncUrl("open")
    }

    this.dispatchState(true)

    if (options.moveFocus === false) {
      return
    }

    const focusTarget =
      this.panelTarget.querySelector('[data-label-filter-options-target="searchInput"]')
      || this.closeButtonTarget

    focusTarget?.focus()
  }

  close(eventOrOptions = {}) {
    if (typeof eventOrOptions.preventDefault === "function") {
      eventOrOptions.preventDefault()
    }

    const options =
      typeof eventOrOptions.preventDefault === "function" ? {} : eventOrOptions

    this.panelTarget.classList.add("d-none")
    this.backdropTarget.classList.add("d-none")
    this.panelTarget.setAttribute("aria-hidden", "true")
    this.backdropTarget.setAttribute("aria-hidden", "true")

    if (options.syncUrl !== false) {
      this.syncUrl("closed")
    }

    this.dispatchState(false)

    if (options.returnFocus === false) {
      return
    }

    this.returnFocusTarget?.focus()
  }

  dispatchState(open) {
    document.dispatchEvent(
      new CustomEvent(STATE_EVENT, {
        detail: { open },
      })
    )
  }

  syncUrl(panelState) {
    const nextSearch = buildPanelStateSearch(panelState)
    const nextUrl = `${window.location.pathname}${nextSearch ? `?${nextSearch}` : ""}${window.location.hash}`
    window.history.replaceState({}, "", nextUrl)
  }

  get isOpen() {
    return !this.panelTarget.classList.contains("d-none")
  }

  get returnFocusTarget() {
    if (this.lastTrigger instanceof HTMLElement) {
      return this.lastTrigger
    }

    const panelId = this.panelTarget.getAttribute("id")

    if (!panelId) {
      return null
    }

    return document.querySelector(
      `[data-filter-drawer-trigger][aria-controls="${panelId}"]`
    )
  }
}
