/* Small, optional enhancements. The corpus and chapter links work without JS. */
(() => {
  'use strict';

  const SETTINGS_KEY = 'path-to-moksha:reader-settings:1';
  const BOOKMARK_KEY = 'path-to-moksha:bookmark:1';
  const sizes = ['standard', 'large', 'extra-large'];
  const labels = ['Standard', 'Large', 'Extra large'];
  const chapterPath = /^\/mahabharata\/sarit\/(?:[1-9]|1[0-8])\/section-[1-9]\d*\/$/;

  function element(tag, attrs = {}, text) {
    const node = document.createElement(tag);
    for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function readLocal(key) {
    try { return JSON.parse(window.localStorage.getItem(key)); }
    catch { return null; }
  }

  function writeLocal(key, value) {
    try {
      if (value === null) window.localStorage.removeItem(key);
      else window.localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch { return false; }
  }

  function validatedBookmark() {
    const data = readLocal(BOOKMARK_KEY);
    if (!data || typeof data.title !== 'string' || !data.title || data.title.length > 180
        || typeof data.url !== 'string' || !data.url.startsWith('/') || data.url.length > 360) return null;
    try {
      const url = new URL(data.url, location.origin);
      return url.origin === location.origin && !url.search && chapterPath.test(url.pathname)
        ? { title: data.title, url: url.pathname + url.hash }
        : null;
    } catch { return null; }
  }

  function normalize(text) {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
      .replace(/[०-९]/g, digit => String(digit.charCodeAt(0) - 0x0966))
      .replace(/\s+/g, ' ').trim();
  }

  function enhanceChapterIndex(grid, index, single) {
    const entries = Array.from(grid.children).filter(entry => entry.querySelector(':scope > a[href]'));
    if (entries.length < 5) return;
    const titles = entries.map(entry => {
      const link = entry.querySelector('a').cloneNode(true);
      link.querySelectorAll('[aria-hidden="true"], small').forEach(node => node.remove());
      return normalize(link.textContent);
    });
    const suffix = index === 0 ? '' : '-' + (index + 1);
    const filterID = 'chapter-filter' + suffix;
    const statusID = 'chapter-filter-status' + suffix;
    const section = grid.closest('section');
    const name = single ? '' : section?.querySelector('h2')?.textContent?.trim() || '';
    const numberOf = value => value.match(/^(?:chapter\s+)?0*([1-9]\d*)$/)?.[1];
    const field = element('input', {
      id: filterID, type: 'search', spellcheck: 'false', autocomplete: 'off',
      placeholder: 'e.g. 25', class: 'chapter-filter-input', 'aria-describedby': statusID,
    });
    const clear = element('button', { type: 'button', class: 'reader-action' }, 'Clear');
    clear.disabled = true;
    const group = element('div', { class: 'chapter-filter', role: 'search', 'aria-label': name ? name + ' chapter index' : 'Chapter index' });
    const controls = element('div', { class: 'chapter-filter-controls' });
    const status = element('p', { id: statusID, role: 'status' }, entries.length + ' entries');
    const empty = element('p', { class: 'chapter-filter-empty', hidden: '' }, 'No chapters match. Try a chapter number or clear the filter.');
    group.append(element('label', { for: field.id }, name ? 'Find a chapter in ' + name : 'Find a chapter'), controls, status);
    controls.append(field, clear);
    grid.before(group, empty);
    function update() {
      const query = normalize(field.value);
      const chapter = numberOf(query);
      let shown = 0;
      entries.forEach((entry, index) => {
        const number = numberOf(titles[index]);
        const match = !query || (chapter !== undefined
          ? (number === chapter || (number === undefined && titles[index].includes(query)))
          : titles[index].includes(query));
        entry.hidden = !match;
        if (match) shown++;
      });
      /* Front matter is not a chapter and should not hide the no-results state. */
      grid.querySelectorAll('.chapter-frontmatter').forEach(entry => { entry.hidden = Boolean(query); });
      clear.disabled = !field.value;
      empty.hidden = shown !== 0;
      status.textContent = query ? shown + (shown === 1 ? ' matching entry' : ' matching entries') : entries.length + ' entries';
    }
    field.addEventListener('input', update);
    clear.addEventListener('click', () => { field.value = ''; update(); field.focus(); });
    field.addEventListener('keydown', event => {
      if (event.key === 'Escape' && field.value) {
        event.preventDefault(); field.value = ''; update();
      }
    });
    update();
  }

  function enhanceHomepage() {
    const actions = document.querySelector('.library-intro .actions');
    if (!actions) return;
    const initial = validatedBookmark();
    if (!initial) return;
    const container = element('div', { class: 'saved-reading' });
    const link = element('a', { href: initial.url, class: 'saved-reading-link' }, 'Resume ' + initial.title);
    const clear = element('button', { type: 'button', class: 'reader-action' }, 'Clear saved chapter');
    const status = element('span', { class: 'reader-status', role: 'status' });
    container.append(link, clear, status);
    actions.after(container);
    clear.addEventListener('click', () => {
      if (!writeLocal(BOOKMARK_KEY, null)) {
        status.textContent = 'Could not clear the saved chapter.';
        return;
      }
      const primary = actions.querySelector('.primary');
      if (primary) primary.focus();
      link.remove();
      clear.remove();
      status.textContent = 'Saved chapter cleared.';
    });
  }

  function enhanceReader() {
    const reader = document.querySelector('.chapter-reader');
    const layers = reader?.querySelector('.layers');
    if (!reader || !layers || !chapterPath.test(location.pathname)) return;
    const heading = reader.querySelector('.reader-title h1')?.textContent?.trim();
    const parva = reader.querySelector('.crumbs a:last-of-type')?.textContent?.trim();
    const title = [parva, heading].filter(Boolean).join(' · ').slice(0, 180);
    const isSourceOnly = !reader.querySelector('.reading-text .study');
    const switches = {};
    for (const key of ['sa', 'iast', 'words']) {
      const field = layers.querySelector('#show-' + key);
      if (field instanceof HTMLInputElement) switches[key] = field;
    }
    const initial = readLocal(SETTINGS_KEY);
    const saved = initial && typeof initial === 'object' ? initial : {};
    for (const [key, field] of Object.entries(switches)) {
      if (typeof saved[key] === 'boolean') field.checked = saved[key];
    }
    let currentSize = sizes.includes(saved.size) ? saved.size : sizes[0];

    const toolbar = element('div', { class: 'reader-tools', role: 'group', 'aria-label': 'Reading tools' });
    const font = element('select', { id: 'reader-text-size' });
    sizes.forEach((value, index) => font.append(element('option', { value }, labels[index])));
    const fontControl = element('label', { class: 'reader-tool-font', for: font.id }, 'Text size');
    const save = element('button', { type: 'button', class: 'reader-action' }, 'Save chapter');
    const copy = element('button', { type: 'button', class: 'reader-action' }, 'Copy reading link');
    const status = element('p', { class: 'reader-status', role: 'status' });
    const fallback = element('input', {
      type: 'url', class: 'reader-copy-fallback', readonly: '', hidden: '', 'aria-label': 'Reading link',
    });
    fontControl.append(font);
    toolbar.append(fontControl, save, copy, status, fallback);
    layers.after(toolbar);
    font.value = currentSize;
    reader.dataset.textSize = currentSize;
    const currentURL = () => location.pathname + location.hash;
    const updateSavedUI = () => {
      const entry = validatedBookmark();
      save.setAttribute('aria-pressed', String(Boolean(entry && entry.url === currentURL())));
    };
    updateSavedUI();
    window.addEventListener('hashchange', updateSavedUI);
    window.addEventListener('storage', event => {
      if (event.key === BOOKMARK_KEY) updateSavedUI();
    });
    function ensureContent(changed) {
      /* With no English or source layer selected, keep one usable reading mode. */
      if (isSourceOnly && switches.sa && switches.iast && !switches.sa.checked && !switches.iast.checked) {
        const fallbackLayer = changed === switches.sa ? switches.iast : switches.sa;
        fallbackLayer.checked = true;
        if (changed) status.textContent = 'Kept ' + (fallbackLayer === switches.sa ? 'Sanskrit' : 'Roman transliteration') + ' visible.';
      }
    }
    ensureContent();
    function storeSettings() {
      const value = { ...saved, size: currentSize };
      for (const [key, field] of Object.entries(switches)) value[key] = field.checked;
      writeLocal(SETTINGS_KEY, value);
    }
    for (const control of Object.values(switches)) {
      control.addEventListener('change', () => {
        status.textContent = '';
        ensureContent(control);
        storeSettings();
      });
    }
    font.addEventListener('change', () => {
      if (!sizes.includes(font.value)) return;
      currentSize = font.value;
      reader.dataset.textSize = currentSize;
      storeSettings();
    });
    save.addEventListener('click', () => {
      const entry = validatedBookmark();
      const isSaved = entry?.url === currentURL();
      if (!title || !writeLocal(BOOKMARK_KEY, isSaved ? null : { title, url: currentURL() })) {
        status.textContent = 'This browser could not save your chapter.';
        return;
      }
      updateSavedUI();
      status.textContent = isSaved ? 'Saved chapter removed.' : 'Chapter saved in this browser.';
    });
    copy.addEventListener('click', async () => {
      const url = location.origin + currentURL();
      try {
        await navigator.clipboard.writeText(url);
        fallback.hidden = true;
        status.textContent = 'Reading link copied.';
      } catch {
        fallback.value = url;
        fallback.hidden = false;
        fallback.focus();
        fallback.select();
        status.textContent = 'Copy the selected reading link.';
      }
    });
  }

  const chapterGrids = document.querySelectorAll('.chapter-grid');
  chapterGrids.forEach((grid, index) => enhanceChapterIndex(grid, index, chapterGrids.length === 1));
  enhanceHomepage();
  enhanceReader();
})();
