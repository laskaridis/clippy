(() => {
  const THEME_STORAGE_KEY = "clippy-theme";
  const THEME_DARK = "dark";
  const THEME_LIGHT = "light";
  const ARIA_LABEL_SWITCH_TO_LIGHT = "Switch to light mode";
  const ARIA_LABEL_SWITCH_TO_DARK = "Switch to dark mode";
  const VALID_THEMES = new Set([THEME_DARK, THEME_LIGHT]);

  class ThemeController {
    constructor(documentRef = document) {
      this.documentRef = documentRef;
      this.htmlElement = this.documentRef.documentElement;
      this.toggle = this.documentRef.getElementById("themeToggle");
      this.moonIcon = this.documentRef.getElementById("themeIconMoon");
      this.sunIcon = this.documentRef.getElementById("themeIconSun");
    }

    static restoreThemeFromStorage(documentRef = document) {
      try {
        const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
        if (VALID_THEMES.has(savedTheme)) {
          documentRef.documentElement.setAttribute("data-bs-theme", savedTheme);
        }
      } catch (error) {
        // Ignore storage access errors and keep default document theme.
      }
    }

    getCurrentTheme() {
      const currentTheme = this.htmlElement.getAttribute("data-bs-theme");
      return VALID_THEMES.has(currentTheme) ? currentTheme : THEME_DARK;
    }

    applyTheme(theme) {
      const nextTheme = VALID_THEMES.has(theme) ? theme : THEME_DARK;
      this.htmlElement.setAttribute("data-bs-theme", nextTheme);
      return nextTheme;
    }

    persistTheme(theme) {
      try {
        window.localStorage.setItem(THEME_STORAGE_KEY, theme);
      } catch (error) {
        // Ignore storage access errors; page-level theme should still update.
      }
    }

    updateToggleUI(theme) {
      const isDark = theme === THEME_DARK;
      this.moonIcon?.classList.toggle("d-none", !isDark);
      this.sunIcon?.classList.toggle("d-none", isDark);
      this.toggle?.setAttribute(
        "aria-label",
        isDark ? ARIA_LABEL_SWITCH_TO_LIGHT : ARIA_LABEL_SWITCH_TO_DARK
      );
    }

    toggleTheme() {
      const nextTheme =
        this.getCurrentTheme() === THEME_DARK ? THEME_LIGHT : THEME_DARK;
      this.applyTheme(nextTheme);
      this.persistTheme(nextTheme);
      this.updateToggleUI(nextTheme);
    }

    init() {
      this.updateToggleUI(this.getCurrentTheme());
      this.toggle?.addEventListener("click", () => this.toggleTheme());
    }
  }

  ThemeController.restoreThemeFromStorage();
  window.addEventListener("DOMContentLoaded", () => {
    new ThemeController().init();
  });
})();
