/* Temporary device-review aid. Remove with viewport.css and its HTML hooks. */
(() => {
  const panel = document.querySelector('[data-viewport]');
  const value = panel?.querySelector('[data-viewport-value]');
  if (!value) return;

  const update = () => {
    value.textContent = `${window.innerWidth} × ${window.innerHeight}`;
    panel.hidden = false;
  };

  update();
  window.addEventListener('resize', update, { passive: true });
})();
