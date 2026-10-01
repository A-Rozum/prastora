/* Small opt-in UI enhancements. No tracking, storage or third-party requests. */
(() => {
  const root = document.documentElement;
  const rem = () => parseFloat(getComputedStyle(root).fontSize);
  const utility = document.querySelector('.viewport-panel');
  const header = document.querySelector('.site-header');
  if (utility && header) {
    const slot = document.createElement('div');
    const top = document.createElement('div');
    slot.className = 'site-top-slot';
    top.className = 'site-top';
    utility.before(slot);
    slot.append(top);
    top.append(utility, header);
    const measure = () => {
      const unit = rem();
      const height = top.getBoundingClientRect().height;
      root.style.setProperty('--sticky-height', `${height / unit}rem`);
      // Reserve the expanded height so shrinking does not move page content.
      slot.style.blockSize = `${height / unit + (top.classList.contains('is-compact') ? 2 : 0)}rem`;
    };
    let pending = false;
    const update = () => {
      top.classList.toggle('is-compact', window.scrollY > 2 * rem());
      measure();
      pending = false;
    };
    window.addEventListener('scroll', () => {
      if (!pending) { pending = true; requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener('resize', update, { passive: true });
    new ResizeObserver(measure).observe(top);
    update();
    if (location.hash) requestAnimationFrame(() => {
      let id = location.hash.slice(1);
      try { id = decodeURIComponent(id); } catch { /* Keep malformed hashes harmless. */ }
      document.getElementById(id)?.scrollIntoView();
    });
  }

  const themeButton = document.querySelector('[data-theme-toggle]');
  if (themeButton) {
    const preference = matchMedia('(prefers-color-scheme: dark)');
    const isDark = () => root.dataset.scheme ? root.dataset.scheme === 'dark' : preference.matches;
    const describe = () => {
      const label = `Switch to ${isDark() ? 'light' : 'dark'} theme`;
      themeButton.setAttribute('aria-label', label);
      themeButton.title = label;
    };
    themeButton.hidden = false;
    themeButton.addEventListener('click', () => {
      root.dataset.scheme = isDark() ? 'light' : 'dark';
      describe();
    });
    preference.addEventListener('change', describe);
    describe();
  }

  const consent = document.querySelector('[data-consent-demo]');
  if (consent) {
    const settings = consent.querySelector('[data-consent-settings]');
    const settingsButton = consent.querySelector('[data-consent-configure]');
    const reopen = document.querySelector('[data-consent-reopen]');
    const status = document.querySelector('[data-consent-status]');
    const measure = () => {
      root.style.setProperty('--consent-height', `${consent.hidden ? 0 : consent.getBoundingClientRect().height / rem()}rem`);
    };
    const choose = (analytics, marketing) => {
      consent.querySelector('#consent-analytics').checked = analytics;
      consent.querySelector('#consent-marketing').checked = marketing;
      consent.hidden = true;
      settings.hidden = true;
      settingsButton.setAttribute('aria-expanded', 'false');
      status.textContent = analytics || marketing ? 'Demo choice saved for this page only.' : 'Demo choice: optional cookies declined.';
      measure();
      reopen.focus({ preventScroll: true });
    };
    consent.querySelector('[data-consent-reject]').addEventListener('click', () => choose(false, false));
    consent.querySelector('[data-consent-accept]').addEventListener('click', () => choose(true, true));
    settingsButton.addEventListener('click', () => {
      settings.hidden = !settings.hidden;
      settingsButton.setAttribute('aria-expanded', String(!settings.hidden));
      measure();
      if (!settings.hidden) settings.querySelector('input').focus({ preventScroll: true });
    });
    consent.querySelector('[data-consent-save]').addEventListener('click', () => {
      choose(consent.querySelector('#consent-analytics').checked, consent.querySelector('#consent-marketing').checked);
    });
    reopen.hidden = false;
    reopen.addEventListener('click', () => {
      consent.hidden = false;
      measure();
      settingsButton.focus({ preventScroll: true });
    });
    consent.hidden = false;
    new ResizeObserver(measure).observe(consent);
    measure();
  }
})();
