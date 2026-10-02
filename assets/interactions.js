/* Persistent local UI preferences. No trackers or third-party requests. */
(() => {
  const root = document.documentElement;
  const read = (store, key) => {
    try { return window[store].getItem(key); } catch { return null; }
  };
  const write = (store, key, value) => {
    try { window[store].setItem(key, value); } catch { /* UI still works without storage. */ }
  };
  const savedTheme = read('localStorage', 'prastora.theme');
  if (savedTheme === 'light' || savedTheme === 'dark') root.dataset.scheme = savedTheme;
  const rem = () => parseFloat(getComputedStyle(root).fontSize);
  const utility = document.querySelector('.viewport-panel');
  // Interactive utility widgets share one implementation; navigation stays static HTML.
  if (utility && !utility.querySelector('[data-theme-toggle]')) {
    const tools = document.createElement('div');
    tools.className = 'viewport-tools';
    const reading = utility.querySelector('.viewport-reading');
    reading.before(tools);
    tools.innerHTML = '<button class="theme-toggle" data-theme-toggle type="button" aria-label="Switch colour theme" hidden><svg class="theme-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg><svg class="theme-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 14.5A9 9 0 0 1 9.5 3.5a9 9 0 1 0 11 11Z"/></svg></button>';
    tools.append(reading);
  }
  if (!document.querySelector('[data-consent-demo]')) {
    const consent = document.createElement('aside');
    consent.className = 'consent-bar';
    consent.dataset.consentDemo = '';
    consent.hidden = true;
    consent.setAttribute('aria-label', 'Cookie preferences');
    consent.innerHTML = '<div class="consent-settings" id="consent-settings" data-consent-settings hidden><p>Cookie preferences · necessary functions stay available.</p><label><input type="checkbox" id="consent-analytics">Analytics</label><label><input type="checkbox" id="consent-marketing">Marketing</label><button type="button" data-consent-save>Save preferences</button></div><div class="consent-row"><p>We use cookies</p><div class="consent-actions"><button type="button" data-consent-accept>Accept all</button><button type="button" data-consent-reject>Necessary only</button><button type="button" data-consent-configure aria-expanded="false" aria-controls="consent-settings">Settings</button></div></div>';
    document.body.append(consent);
    const footer = document.querySelector('.site-footer');
    const controls = document.createElement('div');
    controls.innerHTML = '<button type="button" class="consent-reopen" data-consent-reopen hidden>Cookie settings</button><p class="small muted" data-consent-status role="status"></p>';
    footer.append(controls);
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
