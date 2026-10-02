/* Persistent local UI preferences. No trackers or third-party requests. */
(() => {
  const root = document.documentElement;
  const read = (store, key) => {
    try { return window[store].getItem(key); } catch { return null; }
  };
  const write = (store, key, value) => {
    try { window[store].setItem(key, value); } catch { /* UI still works without storage. */ }
  };
  const rem = () => parseFloat(getComputedStyle(root).fontSize);

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
      write('localStorage', 'prastora.theme', root.dataset.scheme);
      describe();
    });
    preference.addEventListener('change', describe);
    window.addEventListener('storage', event => {
      if (event.key !== 'prastora.theme' && event.key !== null) return;
      const theme = read('localStorage', 'prastora.theme');
      if (theme === 'light' || theme === 'dark') root.dataset.scheme = theme;
      else delete root.dataset.scheme;
      describe();
    });
    describe();
  }

  const consent = document.querySelector('[data-consent-demo]');
  if (consent) {
    const settings = consent.querySelector('[data-consent-settings]');
    const settingsButton = consent.querySelector('[data-consent-configure]');
    const reopen = document.querySelector('[data-consent-reopen]');
    const status = document.querySelector('[data-consent-status]');
    let savedChoice = null;
    try {
      const choice = JSON.parse(read('localStorage', 'prastora.consent.v1'));
      if (choice?.version === 1 && typeof choice.analytics === 'boolean' && typeof choice.marketing === 'boolean') savedChoice = choice;
    } catch { /* Ignore malformed or unavailable storage; ask again. */ }
    if (savedChoice) {
      consent.querySelector('#consent-analytics').checked = savedChoice.analytics;
      consent.querySelector('#consent-marketing').checked = savedChoice.marketing;
    }
    const measure = () => {
      root.style.setProperty('--consent-height', `${consent.hidden ? 0 : consent.getBoundingClientRect().height / rem()}rem`);
    };
    const choose = (analytics, marketing) => {
      write('localStorage', 'prastora.consent.v1', JSON.stringify({ version: 1, analytics, marketing }));
      consent.querySelector('#consent-analytics').checked = analytics;
      consent.querySelector('#consent-marketing').checked = marketing;
      consent.hidden = true;
      settings.hidden = true;
      settingsButton.setAttribute('aria-expanded', 'false');
      status.textContent = analytics || marketing ? 'Cookie preference selected.' : 'Necessary only selected.';
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
    consent.hidden = Boolean(savedChoice);
    new ResizeObserver(measure).observe(consent);
    measure();
  }
})();
