/* Run before styles/content: restore only a valid manual palette. */
(() => {
  try {
    const theme = localStorage.getItem('prastora.theme');
    if (theme === 'light' || theme === 'dark') document.documentElement.dataset.scheme = theme;
  } catch { /* Storage is optional; CSS follows the system preference. */ }
})();
