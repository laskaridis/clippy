(() => {
  const THEME_STORAGE_KEY = "clippy-theme";
  const VALID_THEMES = new Set(["dark", "light"]);

  try {
    const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (VALID_THEMES.has(savedTheme)) {
      document.documentElement.setAttribute("data-bs-theme", savedTheme);
    }
  } catch (error) {
    // Ignore storage access errors and keep default document theme.
  }
})();
