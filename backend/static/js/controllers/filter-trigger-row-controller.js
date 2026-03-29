import { Controller } from "../vendor/stimulus.js"

const OPEN_EVENT = "clips:filter-drawer:open"
const STATE_EVENT = "clips:filter-drawer:state"

export default class extends Controller {
  static targets = ["trigger"]

  connect() {
    this.boundHandleDrawerState = this.handleDrawerState.bind(this)
    document.addEventListener(STATE_EVENT, this.boundHandleDrawerState)
  }

  disconnect() {
    document.removeEventListener(STATE_EVENT, this.boundHandleDrawerState)
  }

  openDrawer(event) {
    event.preventDefault()

    document.dispatchEvent(
      new CustomEvent(OPEN_EVENT, {
        detail: {
          sourceElement: this.hasTriggerTarget ? this.triggerTarget : event.currentTarget,
        },
      })
    )
  }

  handleDrawerState(event) {
    if (!this.hasTriggerTarget) {
      return
    }

    this.triggerTarget.setAttribute(
      "aria-expanded",
      event.detail?.open ? "true" : "false"
    )
  }
}
