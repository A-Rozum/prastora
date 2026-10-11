/* Enquiry preview and directory filtering. Navigation and focus switching are native HTML/CSS. */
(() => {
  const params = new URLSearchParams(location.search);
  const form = document.getElementById('request-form');
  if (form) {
    const focus = params.get('focus');
    if (focus === 'regional' || focus === 'belarus') document.getElementById('focus-' + focus).checked = true;
    const jurisdiction = document.getElementById('request-jurisdiction');
    const service = document.getElementById('request-service');
    const fields = document.getElementById('request-fields');
    const contact = document.getElementById('request-contact');
    const result = document.getElementById('form-result');
    const names = { michalevic: 'Алесь Михалевич', breski: 'Олег Бреский', krivoi: 'Ярослав Кривой', ilina: 'Анастасия Ильина', dovgal: 'Игорь Довгаль', zabolotna: 'Екатерина Заболотна' };
    const expert = params.get('expert');
    if (Object.hasOwn(names, expert)) {
      document.getElementById('request-title').textContent = 'Вопрос эксперту: ' + names[expert];
      document.getElementById('request-expert').value = expert;
    }
    document.querySelectorAll('[data-service]').forEach(link => {
      link.addEventListener('click', () => { service.value = link.dataset.service; });
    });
    document.querySelector('[data-expert-request]').addEventListener('click', () => {
      document.getElementById('request-expert').value = 'michalevic';
      if (!jurisdiction.value.trim()) {
        jurisdiction.value = document.querySelector('input[name="expert-focus"]:checked').value === 'belarus' ? 'Беларусь' : 'Постсоветские юрисдикции';
      }
    });
    const changeContactMethod = () => {
      const phone = document.querySelector('input[name="contact-method"]:checked').value === 'phone';
      contact.type = phone ? 'tel' : 'email';
      contact.autocomplete = phone ? 'tel' : 'email';
      document.getElementById('contact-label').textContent = phone ? 'Телефон' : 'Email';
      document.getElementById('contact-hint').textContent = phone ? 'Укажите номер с кодом страны.' : 'Укажите адрес для обратной связи.';
      if (phone) contact.setAttribute('pattern', '[+0-9\\(\\) .\\-]{6,30}');
      else contact.removeAttribute('pattern');
      contact.setCustomValidity('');
      result.hidden = true;
    };
    document.querySelectorAll('input[name="contact-method"]').forEach(input => input.addEventListener('change', changeContactMethod));
    form.addEventListener('submit', event => {
      event.preventDefault();
      contact.setCustomValidity(contact.type === 'tel' && contact.value.replace(/\D/g, '').length < 6 ? 'Укажите телефон с кодом страны.' : '');
      jurisdiction.setCustomValidity(jurisdiction.value.trim() ? '' : 'Укажите страну или регион.');
      if (!form.reportValidity()) return;
      result.textContent = 'Форма заполнена. Заявка не отправлена: отправка ещё не подключена. Для обращения используйте email или телефон эксперта.';
      result.hidden = false;
      result.focus();
    });
    contact.addEventListener('input', () => contact.setCustomValidity(''));
    jurisdiction.addEventListener('input', () => jurisdiction.setCustomValidity(''));
    form.addEventListener('input', () => { result.hidden = true; });
    changeContactMethod();
    fields.disabled = false;
  }
  const filters = document.getElementById('directory-filters');
  if (filters) {
    const cards = [...document.querySelectorAll('[data-expert-card]')];
    const reset = document.getElementById('directory-reset');
    const normalize = value => value.toLocaleLowerCase('ru').replaceAll('ё', 'е').trim();
    for (const field of filters.elements) {
      const value = params.get(field.name);
      if (value && field.tagName === 'SELECT' && [...field.options].some(option => option.value === value)) field.value = value;
    }
    const update = () => {
      const country = filters.elements.country.value;
      const topic = filters.elements.topic.value;
      const name = normalize(filters.elements.namedItem('name').value);
      let found = 0;
      for (const card of cards) {
        const visible = (!country || card.dataset.country.split(' ').includes(country))
          && (!topic || card.dataset.topic.split(' ').includes(topic))
          && (!name || normalize(card.querySelector('h2').textContent).includes(name));
        card.hidden = !visible;
        if (visible) found++;
      }
      document.getElementById('directory-count').textContent = 'Найдено экспертов: ' + found;
      document.getElementById('directory-empty').hidden = found > 0;
      document.querySelector('#expert-michalevic a[href*="#expert-name"]').href = 'expertise.html' + (country ? '?focus=' + country : '') + '#expert-name';
      reset.hidden = !country && !topic && !name;
    };
    const clear = () => { filters.reset(); update(); };
    filters.addEventListener('input', update);
    filters.addEventListener('change', update);
    filters.addEventListener('submit', event => { event.preventDefault(); update(); });
    reset.addEventListener('click', clear);
    document.querySelectorAll('[data-clear-filters]').forEach(link => link.addEventListener('click', clear));
    update();
  }
})();
