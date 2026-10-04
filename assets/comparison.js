/* Mobile page -> table handoff. Native HTML/CSS still owns every comparison control.
   No-JS fallback: the existing independently scrollable table.
   Wheel/touch gestures starting below the sticky menu first move the page.
   Gestures starting at the menu keep native scrolling and momentum. */
(() => {
  const region = document.querySelector('.tm-scroll');
  if (!region) return;
  const mobile = matchMedia('(width <= 50em)');
  const header = document.querySelector('.site-header');
  const gap = () => region.getBoundingClientRect().top - Math.max(0, header?.getBoundingClientRect().bottom || 0);
  const movePage = delta => {
    const before = window.scrollY;
    window.scrollBy({ top: delta, behavior: 'instant' });
    return window.scrollY - before;
  };
  const moveTable = delta => {
    const before = region.scrollTop;
    region.scrollTop += delta;
    return region.scrollTop - before;
  };
  // Consume only the distance needed to reach the menu. The rest belongs to
  // the table; at either end of the table it returns to the page.
  const route = delta => {
    let remaining = delta;
    if (remaining > 0 && gap() > 1) remaining -= movePage(Math.min(remaining, gap()));
    if (gap() <= 1) remaining -= moveTable(remaining);
    if (Math.abs(remaining) > 1) movePage(remaining);
  };
  region.addEventListener('wheel', event => {
    if (!mobile.matches || event.ctrlKey || event.shiftKey || !event.cancelable
        || Math.abs(event.deltaY) <= Math.abs(event.deltaX) || gap() <= 1) return;
    const unit = event.deltaMode === 1 ? parseFloat(getComputedStyle(region).fontSize) * 1.6
      : event.deltaMode === 2 ? region.clientHeight : 1;
    event.preventDefault();
    route(event.deltaY * unit);
  }, { passive: false });

  region.addEventListener('keydown', event => {
    if (!mobile.matches || event.target !== region || event.ctrlKey || event.metaKey || event.altKey || gap() <= 1) return;
    const line = parseFloat(getComputedStyle(region).fontSize) * 1.6;
    const delta = event.key === 'ArrowDown' ? line : event.key === 'ArrowUp' ? -line
      : event.key === 'PageDown' ? region.clientHeight : event.key === 'PageUp' ? -region.clientHeight
      : event.key === ' ' ? region.clientHeight * (event.shiftKey ? -1 : 1) : 0;
    if (!delta) return;
    event.preventDefault();
    route(delta);
  });

  // A touch sequence already handed to JS must stay with it until touchend;
  // switching halfway would lose deltas or let the page slide past the menu.
  let gesture = null;
  region.addEventListener('touchstart', event => {
    if (!mobile.matches || event.touches.length !== 1 || gap() <= 1) { gesture = null; return; }
    const touch = event.touches[0];
    gesture = { id: touch.identifier, x: touch.clientX, y: touch.clientY, lastY: touch.clientY, vertical: false };
  }, { passive: true });
  region.addEventListener('touchmove', event => {
    if (!gesture || !mobile.matches || event.touches.length !== 1 || !event.cancelable) { gesture = null; return; }
    const touch = event.touches[0];
    if (touch.identifier !== gesture.id) { gesture = null; return; }
    if (!gesture.vertical) {
      const dx = Math.abs(touch.clientX - gesture.x), dy = Math.abs(touch.clientY - gesture.y);
      if (Math.max(dx, dy) < 6) return;
      // Horizontal swipes, taps and multi-touch remain entirely native.
      if (dx >= dy) { gesture = null; return; }
      gesture.vertical = true;
    }
    event.preventDefault();
    route(gesture.lastY - touch.clientY);
    gesture.lastY = touch.clientY;
  }, { passive: false });
  const finish = () => { gesture = null; };
  region.addEventListener('touchend', finish, { passive: true });
  region.addEventListener('touchcancel', finish, { passive: true });
  mobile.addEventListener('change', finish);
})();
