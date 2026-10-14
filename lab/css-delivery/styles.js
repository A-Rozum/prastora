/* Optional non-blocking styles. Link positions preserve the stylesheet cascade. */
(() => {
  if (window.PrastoraStyles) return;
  const states = new Map();
  const load = link => {
    if (states.has(link)) return states.get(link);
    const promise = new Promise(resolve => {
      let done = false;
      const finish = ok => {
        if (done) return;
        done = true;
        clearTimeout(timer);
        link.removeEventListener('load', loaded);
        link.removeEventListener('error', failed);
        if (ok) link.media = link.dataset.cssMedia || 'all';
        link.dataset.cssState = ok ? 'ready' : 'failed';
        resolve(ok);
      };
      const loaded = () => finish(true);
      const failed = () => finish(false);
      const timer = setTimeout(failed, 5000);
      link.addEventListener('load', loaded, {once:true});
      link.addEventListener('error', failed, {once:true});
      if (link.sheet) finish(true);
    });
    states.set(link, promise);
    return promise;
  };
  document.querySelectorAll('link[data-css-defer]').forEach(load);
  window.PrastoraStyles = Object.freeze({
    ready: async name => {
      const links = [...document.querySelectorAll('link[data-css-defer]')]
        .filter(link => !name || link.dataset.cssDefer === name);
      return (await Promise.all(links.map(load))).every(Boolean);
    }
  });
})();
