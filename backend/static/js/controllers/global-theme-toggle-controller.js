import { Controller } from "../vendor/stimulus.js"

const THEME_STORAGE_KEY = "clippy-theme"
const THEME_DARK = "dark"
const THEME_LIGHT = "light"
const ARIA_LABEL_SWITCH_TO_LIGHT = "Switch to light mode"
const ARIA_LABEL_SWITCH_TO_DARK = "Switch to dark mode"
const VALID_THEMES = new Set([THEME_DARK, THEME_LIGHT])

export default class extends Controller {
  static targets = ["moonIcon", "sunIcon"]

  connect() {
    this.updateToggleUI(this.currentTheme)
  }

  toggle() {
    const nextTheme =
      this.currentTheme === THEME_DARK ? THEME_LIGHT : THEME_DARK

    this.applyTheme(nextTheme)
    this.persistTheme(nextTheme)
    this.updateToggleUI(nextTheme)
  }

  get currentTheme() {
    const currentTheme =
      document.documentElement.getAttribute("data-bs-theme") || ""
    return VALID_THEMES.has(currentTheme) ? currentTheme : THEME_DARK
  }

  applyTheme(theme) {
    const nextTheme = VALID_THEMES.has(theme) ? theme : THEME_DARK
    document.documentElement.setAttribute("data-bs-theme", nextTheme)
    return nextTheme
  }

  persistTheme(theme) {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme)
    } catch (error) {
      // Ignore storage access errors; the document theme still updates.
    }
  }

  updateToggleUI(theme) {
    const isDark = theme === THEME_DARK

    if (this.hasMoonIconTarget) {
      this.moonIconTarget.classList.toggle("d-none", !isDark)
    }

    if (this.hasSunIconTarget) {
      this.sunIconTarget.classList.toggle("d-none", isDark)
    }

    this.element.setAttribute(
      "aria-label",
      isDark ? ARIA_LABEL_SWITCH_TO_LIGHT : ARIA_LABEL_SWITCH_TO_DARK
    )
  }
}
