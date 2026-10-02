/* Optional maps only: local SVG controls; Google loads solely after a click. */
(() => {
  const load = document.querySelector('[data-load-google-map]');
  if (load) {
    const host = document.querySelector('[data-google-map-host]');
    const preview = host.querySelector('[data-map-preview]');
    let frame;
    load.hidden = false;
    load.addEventListener('click', () => {
      if (frame) {
        frame.remove();
        frame = null;
        preview.hidden = false;
        load.textContent = 'Load Google map';
        load.setAttribute('aria-expanded', 'false');
        return;
      }
      frame = document.createElement('iframe');
      frame.className = 'google-map-frame';
      frame.title = 'Google map of the waterfront near Viale Filippo Turati, Bagnara Calabra; approximate beach area';
      frame.referrerPolicy = 'strict-origin-when-cross-origin';
      frame.allowFullscreen = true;
      frame.src = 'https://maps.google.com/maps?q=38.2839%2C15.7990&z=16&hl=en&output=embed';
      preview.hidden = true;
      host.append(frame);
      load.textContent = 'Hide Google map';
      load.setAttribute('aria-expanded', 'true');
    });
  }

  const root = document.querySelector('[data-regional-map]');
  if (!root) return;
  const svg = root.querySelector('svg');
  const links = [...root.querySelectorAll('[data-location]')];
  const panels = [...root.querySelectorAll('.location-info')];
  const toolbar = root.querySelector('[data-map-toolbar]');
  const status = root.querySelector('[data-map-status]');
  const zoomIn = root.querySelector('[data-map-action="in"]');
  const zoomOut = root.querySelector('[data-map-action="out"]');
  const points = {
    bagnara: [500.4, 569.2], minsk: [712.2, 194.4], vilnius: [671, 175.5],
    warsaw: [594.2, 234.5], lodz: [566.2, 245.8], krakow: [575, 286.4],
    vlore: [566.7, 516.8], prague: [475.9, 286.2]
  };
  let zoom = 1;
  let center = [450, 350];
  let selected = 'vilnius';
  const render = () => {
    const width = 900 / zoom, height = 700 / zoom;
    center[0] = Math.max(width / 2, Math.min(900 - width / 2, center[0]));
    center[1] = Math.max(height / 2, Math.min(700 - height / 2, center[1]));
    svg.setAttribute('viewBox', `${center[0] - width / 2} ${center[1] - height / 2} ${width} ${height}`);
    zoomIn.disabled = zoom >= 3;
    zoomOut.disabled = zoom <= 1;
    root.querySelectorAll('[data-map-pan]').forEach(button => { button.disabled = zoom <= 1; });
    status.textContent = `${root.querySelector('#location-' + selected + ' h3').textContent}. Map zoom: ${Math.round(zoom * 100)}%.`;
  };
  const select = id => {
    selected = id;
    links.forEach(link => {
      if (link.dataset.location === id) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
    panels.forEach(panel => { panel.hidden = panel.id !== 'location-' + id; });
    if (zoom > 1) center = [...points[id]];
    render();
  };
  links.forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    select(link.dataset.location);
  }));
  links.forEach(link => link.addEventListener('focus', () => {
    if (link.closest('svg') && zoom > 1) {
      center = [...points[link.dataset.location]];
      render();
    }
  }));
  toolbar.hidden = false;
  toolbar.addEventListener('click', event => {
    const button = event.target.closest('button');
    if (!button || button.disabled) return;
    const action = button.dataset.mapAction;
    if (action === 'in') {
      if (zoom === 1) center = [...points[selected]];
      zoom = Math.min(3, zoom * 1.5);
    }
    if (action === 'out') zoom = Math.max(1, zoom / 1.5);
    if (action === 'reset') { zoom = 1; center = [450, 350]; }
    const pan = button.dataset.mapPan;
    if (pan === 'west') center[0] -= 135 / zoom;
    if (pan === 'east') center[0] += 135 / zoom;
    if (pan === 'north') center[1] -= 105 / zoom;
    if (pan === 'south') center[1] += 105 / zoom;
    render();
  });
  const initial = location.hash.replace('#location-', '');
  select(Object.hasOwn(points, initial) ? initial : selected);
})();
