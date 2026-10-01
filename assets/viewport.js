/* Temporary device-review aid. Remove with viewport.css and its HTML hooks. */
(() => {
  const panel = document.querySelector('[data-viewport]');
  const value = panel?.querySelector('[data-viewport-value]');
  if (!value) return;
  const reading = value.parentElement;
  reading.querySelector('span')?.remove();
  value.setAttribute('aria-label', 'Browser viewport width and height');
  const timing = document.createElement('span');
  timing.className = 'load-reading';
  timing.hidden = true;
  const separator = document.createElement('span');
  separator.textContent = '|';
  separator.setAttribute('aria-hidden', 'true');
  const loadValue = document.createElement('output');
  loadValue.setAttribute('data-load-time', '');
  loadValue.setAttribute('aria-label', 'Page load time');
  loadValue.title = 'Time from navigation start to the load event; includes resource loading, not later interaction. Reloads and caching affect this value.';
  timing.append(separator, loadValue);
  reading.append(timing);

  const update = () => {
    value.textContent = `${window.innerWidth} × ${window.innerHeight}`;
    panel.hidden = false;
  };

  update();
  window.addEventListener('resize', update, { passive: true });
  const showLoadTime = () => {
    const navigation = performance.getEntriesByType('navigation')[0];
    if (!navigation || navigation.loadEventEnd <= 0) return;
    loadValue.textContent = `${((navigation.loadEventEnd - navigation.startTime) / 1000).toFixed(3)} s`;
    timing.hidden = false;
  };
  // loadEventEnd is populated after load handlers finish, not inside the event.
  const afterLoad = () => setTimeout(showLoadTime, 0);
  if (document.readyState === 'complete') afterLoad();
  else window.addEventListener('load', afterLoad, { once: true });
})();
