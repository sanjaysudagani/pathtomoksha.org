/* Node 22+ / Chromium, no npm packages. Run after scripts/build.py:
   node tests/frontend_browser.mjs [path/to/dist] [--review] */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createReadStream, existsSync } from 'node:fs';
import { mkdtemp, readFile, rm, stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { dirname, extname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const basedir = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const argumentsList = process.argv.slice(2);
const privateReview = argumentsList.includes('--review');
const dist = resolve(argumentsList.find(value => !value.startsWith('--')) ??
  join(basedir, privateReview ? 'local-translation/review-dist' : 'dist'));
const profile = await mkdtemp(join(basedir, '.reader-test-browser-'));
let browser, cdp;
const mime = new Map([['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'], ['.js', 'text/javascript; charset=utf-8'], ['.jpg', 'image/jpeg'], ['.png', 'image/png']]);
const headers = {};
const test = (name, run) => ({ name, run });
let passed = 0;
const app = createServer(async (request, reply) => {
  for (const [name, value] of Object.entries(headers)) reply.setHeader(name, value);
  try {
    const url = new URL(request.url, 'http://127.0.0.1');
    const path = resolve(dist, '.' + decodeURIComponent(url.pathname));
    if (path !== dist && !path.startsWith(dist + sep)) throw Error('Bad path');
    const file = (await stat(path)).isDirectory() ? join(path, 'index.html') : path;
    const metadata = await stat(file);
    if (!metadata.isFile()) throw Error('Bad file');
    reply.setHeader('Content-Type', mime.get(extname(file)) ?? 'application/octet-stream');
    reply.setHeader('Content-Length', metadata.size);
    createReadStream(file).pipe(reply);
  } catch {
    reply.writeHead(404).end('Not found');
  }
});

function findChrome() {
  if (process.env.CHROME_BIN) return process.env.CHROME_BIN;
  const candidates = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
  ];
  const found = candidates.find(existsSync);
  if (!found) throw Error('Chromium/Google Chrome not found. Set CHROME_BIN to its executable.');
  return found;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
function timeout(promise, duration, message) {
  let timer;
  return Promise.race([promise, new Promise((_, reject) => {
    timer = setTimeout(() => reject(Error(message)), duration);
  })]).finally(() => clearTimeout(timer));
}

try {
  for (const line of (await readFile(join(dist, '_headers'), 'utf8')).split('\n')) {
    const match = /^\s+([\w-]+):\s*(.+)$/.exec(line);
    if (match) headers[match[1]] = match[2];
  }
  assert.match(headers['Content-Security-Policy'], /script-src 'self'/);
  assert.doesNotMatch(headers['Content-Security-Policy'], /unsafe-inline|unsafe-eval/);
  await new Promise((ok, bad) => app.listen(0, '127.0.0.1', ok).once('error', bad));
  const base = 'http://127.0.0.1:' + app.address().port;

  browser = spawn(findChrome(), [
    '--headless=new', '--remote-debugging-port=0', '--disable-background-networking',
    '--disable-component-update', '--disable-sync', '--no-first-run',
    '--no-default-browser-check', '--user-data-dir=' + profile, 'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'], env: { ...process.env, TMPDIR: basedir } });
  let stderr = '';
  browser.on('error', error => { stderr += String(error); });
  browser.stderr.on('data', data => { stderr = (stderr + String(data)).slice(-2500); });
  const exited = new Promise(resolve => { browser.once('exit', resolve); browser.once('error', resolve); });
  let info;
  for (let attempt = 0; attempt < 80 && !info; attempt++) {
    try { info = await readFile(join(profile, 'DevToolsActivePort'), 'utf8'); }
    catch { await sleep(100); }
  }
  assert(info, 'Chrome did not start. ' + stderr);
  const port = info.split('\n')[0];
  const targets = await (await fetch('http://127.0.0.1:' + port + '/json/list')).json();
  cdp = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl);
  await timeout(new Promise((ok, bad) => {
    cdp.addEventListener('open', ok, { once: true });
    cdp.addEventListener('error', bad, { once: true });
  }), 4500, 'Browser socket did not open');
  let id = 0;
  const messages = new Map(), listeners = new Map(), recorded = [];
  cdp.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id && messages.has(message.id)) {
      const { ok, bad } = messages.get(message.id);
      messages.delete(message.id);
      message.error ? bad(Error(JSON.stringify(message.error))) : ok(message.result);
    }
    if (message.method) {
      const listening = listeners.get(message.method);
      if (listening) listening(message.params);
      if (message.method === 'Runtime.exceptionThrown') recorded.push(message.params.exceptionDetails.text);
      if (message.method === 'Log.entryAdded' && message.params.entry.source === 'security') recorded.push(message.params.entry.text);
    }
  });
  const send = (method, params = {}) => timeout(new Promise((ok, bad) => {
    messages.set(++id, { ok, bad });
    cdp.send(JSON.stringify({ id, method, params }));
  }), 8000, 'Timed out: ' + method);
  const evaluate = async expression => {
    const value = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (value.exceptionDetails) throw Error(value.exceptionDetails.exception?.description ?? value.exceptionDetails.text);
    return value.result.value;
  };
  const waitFor = async (expression, label) => {
    for (let attempt = 0; attempt < 30; attempt++) {
      if (await evaluate(expression)) return;
      await sleep(35);
    }
    assert.fail('Timed out waiting for ' + label);
  };
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');
  await send('Log.enable');
  const source = '/mahabharata/sarit/6/section-26/';
  const draft = '/mahabharata/sarit/1/section-4/#adi-1-1-0';
  const storage = 'path-to-moksha:reader-settings:1';
  const bookmark = 'path-to-moksha:bookmark:1';
  const navigate = async route => {
    const loaded = new Promise(ok => listeners.set('Page.loadEventFired', ok));
    const nav = await send('Page.navigate', { url: base + route });
    if (nav.errorText) throw Error(nav.errorText);
    if (nav.loaderId) await timeout(loaded, 10000, 'Page never loaded ' + route);
    listeners.delete('Page.loadEventFired');
    await waitFor('document.readyState === "complete"', route);
    assert.equal(await evaluate('location.pathname + location.hash'), route);
  };
  const setWidth = width => send('Emulation.setDeviceMetricsOverride', {
    width, height: Math.max(720, Math.round(width * .65)), mobile: width < 700, deviceScaleFactor: 1,
  });
  const setTheme = value => send('Emulation.setEmulatedMedia', {
    features: [{ name: 'prefers-color-scheme', value }, { name: 'prefers-reduced-motion', value: 'reduce' }],
  });
  const hasNoOverflow = () => evaluate('document.documentElement.scrollWidth <= (window.visualViewport?.width || innerWidth) + 2');
  const click = selector => evaluate('document.querySelector(' + JSON.stringify(selector) + ').click()');
  const key = async (name, code, virtualKey) => {
    const input = { key: name, code, windowsVirtualKeyCode: virtualKey };
    await send('Input.dispatchKeyEvent', { ...input, type: 'rawKeyDown' });
    await send('Input.dispatchKeyEvent', { ...input, type: 'keyUp' });
  };
  const privateCases = [
    test('Private review index, noindex/no-store and independent chapter filters', async () => {
      await setTheme('light');
      await setWidth(1440);
      await navigate('/');
      const response = await fetch(base + '/');
      assert.match(response.headers.get('x-robots-tag'), /noindex/);
      assert.equal(response.headers.get('cache-control'), 'no-store');
      assert.match(await evaluate('document.querySelector("meta[name=robots]").content'), /noindex/);
      assert.match(await evaluate('document.querySelector(".review-banner").textContent'), /Not for publication/);
      const links = await evaluate('Array.from(document.querySelectorAll(".chapter-grid a")).map(link=>link.getAttribute("href"))');
      assert(links.length > 0, 'private review has no chapters');
      assert(links.every(link => /^\/review\/(?:[1-9]|1[0-8])\/section-[1-9]\d*\/$/.test(link)));
      const filtered = await evaluate('Array.from(document.querySelectorAll(".chapter-filter-input")).map(field=>field.id).length');
      if (filtered > 1) {
        await evaluate('document.querySelectorAll(".chapter-filter-input")[1].focus()');
        await send('Input.insertText', { text: 'not-a-chapter' });
        assert.equal(await evaluate('document.querySelectorAll(".chapter-filter-empty:not([hidden])").length'), 1);
        assert(await evaluate('Array.from(document.querySelector(".chapter-grid").children).some(item=>!item.hidden)'));
        await key('Escape', 'Escape', 27);
      }
    }),
    test('Private source, translation provenance, local links and glossary disclosure', async () => {
      await navigate('/');
      const examples = await evaluate(`Array.from(document.querySelectorAll('.chapter-grid')).flatMap(grid => {
        const links=Array.from(grid.querySelectorAll('a[href]'));
        return Array.from(new Set([links.at(0),links.at(-1)]))
          .filter(Boolean).map(a=>a.getAttribute('href'));
      })`);
      let glossariesTested = 0;
      for(const theme of ['light','dark']) {
        await setTheme(theme);
        for (const width of [320, 390, 768, 1440]) {
          await setWidth(width);
          await navigate('/');
          assert(await hasNoOverflow(), 'Private review index overflows at ' + width);
          for(const route of examples) {
            await navigate(route);
            assert(await hasNoOverflow(), route + ' overflows at ' + width);
            assert(await evaluate('document.querySelector(".review-unit .sanskrit[lang=sa]")'));
            assert(await evaluate('document.querySelector(".review-unit .iast[lang=sa-Latn]")'));
            assert.match(await evaluate('document.querySelector(".review-provenance").textContent'), /Awaiting independent review/);
            assert(await evaluate('Array.from(document.querySelectorAll(".pager a")).every(a=>a.origin===location.origin && (a.pathname==="/" || a.pathname.startsWith("/review/")))'));
            if(await evaluate('document.querySelector(".review-glosses summary")')) {
              await click('.review-glosses summary');
              assert(await evaluate('document.querySelector(".review-glosses").open'));
              assert(await evaluate('document.querySelector(".review-glosses dl dt")'));
              glossariesTested++;
            }
          }
        }
      }
      assert(glossariesTested > 0, 'No word glossary disclosure was covered');
      assert(!recorded.length, 'Browser JS/CSP errors: ' + recorded.join('; '));
    }),
  ];
  const tests = privateReview ? privateCases : [
    test('Desktop and mobile overflow matrix (light and dark)', async () => {
      for (const theme of ['light', 'dark']) {
        await setTheme(theme);
        for (const width of [320, 375, 390, 768, 1024, 1440]) {
          await setWidth(width);
          for (const route of ['/', '/mahabharata/', '/bhagavad-gita/', '/sources/', source, draft]) {
            await navigate(route);
            assert(await hasNoOverflow(), route + ' overflows at ' + width + 'px / ' + theme);
            assert.equal(await evaluate('document.querySelectorAll("main h1").length'), 1, route);
          }
        }
      }
    }),
    test('200% reader text and minimum control contrast', async () => {
      const contrast = (first, second) => {
        const lightness = color => color.match(/\d+(?:\.\d+)?/g).slice(0, 3).map(x => Number(x) / 255)
          .map(x => x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4)
          .reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
        const a = lightness(first), b = lightness(second);
        return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
      };
      for (const theme of ['light', 'dark']) {
        await setTheme(theme);
        await setWidth(320);
        await navigate(source);
        const roles = await evaluate(`(() => {
          const control = getComputedStyle(document.querySelector('.reader-tools button'));
          const page = getComputedStyle(document.documentElement);
          return [control.color, control.backgroundColor, control.borderTopColor, page.backgroundColor];
        })()`);
        assert(contrast(roles[0], roles[1]) >= 4.5, theme + ': body button text contrast');
        assert(contrast(roles[2], roles[3]) >= 3, theme + ': control outline contrast');
        await evaluate('document.documentElement.style.fontSize = "200%"');
        assert(await hasNoOverflow(), theme + ': source chapter overflows at 200% text size');
      }
      await setWidth(1440);
      await setTheme('light');
    }),
    test('Library only links attested books, and source attribution remains discoverable', async () => {
      await navigate('/');
      assert.equal(await evaluate('document.querySelectorAll(".book-grid a.book").length'), 2);
      assert.equal(await evaluate('document.querySelectorAll(".books-planned a").length'), 0);
      assert.equal(await evaluate('document.querySelectorAll(".books-planned .status").length'), 4);
      await navigate('/sources/');
      assert(await evaluate('document.querySelector("main").innerText.includes("Automatic") || document.querySelector("main").innerText.includes("automatically")'));
      assert(await evaluate('document.querySelector("main code").textContent.length === 64'));
    }),
    test('Keyboard access: skip link, filter, escape to clear, and text-switch navigation', async () => {
      await navigate('/');
      await key('Tab', 'Tab', 9);
      assert(await evaluate('document.activeElement.matches("a.skip")'));
      await key('Enter', 'Enter', 13);
      await waitFor('document.activeElement.id === "reading"', 'skip-to-content focus');
      await navigate('/bhagavad-gita/');
      assert.equal(await evaluate('document.querySelectorAll(".chapter-grid a").length'), 18);
      await evaluate('document.querySelector("#chapter-filter").focus()');
      await send('Input.insertText', { text: '०२' });
      assert.equal(await evaluate('document.querySelector(".chapter-grid li:not([hidden]) a").innerText.trim().split("\\n")[0]'), 'Chapter 2');
      assert.equal(await evaluate('document.querySelectorAll(".chapter-grid li:not([hidden])").length'), 1);
      await key('Escape', 'Escape', 27);
      assert.equal(await evaluate('document.querySelectorAll(".chapter-grid li:not([hidden])").length'), 18);
      await send('Input.insertText', { text: 'does not exist' });
      assert.equal(await evaluate('document.querySelector(".chapter-filter-empty").hidden'), false);
      assert.equal(await evaluate('document.querySelector("[role=status]").textContent'), '0 matching entries');
      await click('.chapter-filter button');
      assert(await evaluate('document.activeElement.id === "chapter-filter"'));
      assert.equal(await evaluate('document.querySelector(".chapter-filter-empty").hidden'), true);
      await navigate(source);
      assert(await evaluate('document.querySelector("#show-sa").checked'));
      await evaluate('document.querySelector("#show-sa").focus()');
      await key(' ', 'Space', 32);
      assert(await evaluate('document.querySelector("#show-iast").checked'));
      assert(await evaluate('getComputedStyle(document.querySelector(".verse .iast")).display !== "none"'));
      await key(' ', 'Space', 32);
      assert(await evaluate('getComputedStyle(document.querySelector(".verse .sanskrit")).display !== "none"'));
    }),
    test('Saving, resuming, copying, clearing and validating reading positions', async () => {
      await navigate(draft);
      assert(await evaluate('document.querySelector(":target").id === "adi-1-1-0"'));
      assert(await evaluate('document.querySelector(".verse:target .study")'));
      await click('#show-words');
      assert(await evaluate('getComputedStyle(document.querySelector(".study h3:first-of-type")).display !== "none"'));
      const currentFont = await evaluate('parseFloat(getComputedStyle(document.querySelector(".reading-text")).fontSize)');
      await evaluate('document.querySelector("#reader-text-size").value = "extra-large";document.querySelector("#reader-text-size").dispatchEvent(new Event("change"))');
      assert(await evaluate('parseFloat(getComputedStyle(document.querySelector(".reading-text")).fontSize)') > currentFont);
      await click('.reader-tools [aria-pressed]');
      assert(await evaluate('document.querySelector(".reader-tools [aria-pressed=true]")'));
      assert.equal(await evaluate('JSON.parse(localStorage.getItem(' + JSON.stringify(bookmark) + ')).url'), draft);
      await click('.reader-tools button:nth-of-type(2)');
      await waitFor('document.querySelector(".reader-status").textContent !== "Chapter saved in this browser."', 'clipboard status');
      assert.match(await evaluate('document.querySelector(".reader-status").textContent'), /Reading link copied|Copy the selected reading link/);
      const fallback = await evaluate('document.querySelector(".reader-copy-fallback").hidden ? null : document.querySelector(".reader-copy-fallback").value');
      if (fallback) assert.equal(fallback, base + draft);
      await navigate('/');
      assert.equal(await evaluate('document.querySelector(".saved-reading-link").getAttribute("href")'), draft);
      await navigate(draft);
      assert(await evaluate('document.querySelector("#show-words").checked'));
      assert.equal(await evaluate('document.querySelector("#reader-text-size").value'), 'extra-large');
      await navigate('/');
      await click('.saved-reading button');
      assert.equal(await evaluate('localStorage.getItem(' + JSON.stringify(bookmark) + ')'), null);
      assert(await evaluate('!document.querySelector(".saved-reading-link")'));
      await evaluate('localStorage.setItem(' + JSON.stringify(bookmark) + ', JSON.stringify({title:"Unsafe",url:"//example.invalid/"}))');
      await navigate('/sources/');
      await navigate('/');
      assert(await evaluate('!document.querySelector(".saved-reading-link")'));
      await evaluate('localStorage.removeItem(' + JSON.stringify(bookmark) + ');localStorage.removeItem(' + JSON.stringify(storage) + ')');
    }),
    test('Missing enhancement script and denied storage leave real source available', async () => {
      await send('Network.setBlockedURLs', { urls: ['*reader.js'] });
      await navigate(source);
      assert(await evaluate('!document.querySelector(".reader-tools")'));
      await click('#show-sa');
      assert(await evaluate('getComputedStyle(document.querySelector(".verse .sanskrit")).display !== "none"'));
      await navigate('/bhagavad-gita/');
      assert.equal(await evaluate('document.querySelectorAll(".chapter-grid a").length'), 18);
      assert(await evaluate('!document.querySelector(".chapter-filter")'));
      await send('Network.setBlockedURLs', { urls: [] });
      const stub = await send('Page.addScriptToEvaluateOnNewDocument', {
        source: 'Object.defineProperty(window, "localStorage", {get(){throw Error("unavailable")}})',
      });
      await navigate(source);
      await click('.reader-tools [aria-pressed]');
      assert.equal(await evaluate('document.querySelector(".reader-status").textContent'), 'This browser could not save your chapter.');
      assert(await evaluate('getComputedStyle(document.querySelector(".verse .sanskrit")).display !== "none"'));
      await send('Page.removeScriptToEvaluateOnNewDocument', { identifier: stub.identifier });
      await navigate("/sources/");

    }),
    test('Deep verse links and site payload budgets', async () => {
      await navigate(source + '#bhisma-6-25-1');
      assert(await evaluate('document.querySelector(":target").id === "bhisma-6-25-1"'));
      const lastVerse = await evaluate('Array.from(document.querySelectorAll(".verse[id]")).at(-1).id');
      await evaluate(`localStorage.setItem(${JSON.stringify(storage)},JSON.stringify({size:"extra-large",sa:true,iast:true}))`);
      await navigate('/mahabharata/');
      await navigate(source + '#' + lastVerse);
      await waitFor('document.querySelector(":target").getBoundingClientRect().top < innerHeight && document.querySelector(":target").getBoundingClientRect().bottom > 0', 'target scrolled into view after restoring reader preferences');
      await evaluate('localStorage.removeItem(' + JSON.stringify(storage) + ')');
      assert(!recorded.length, 'Browser JS/CSP errors: ' + recorded.join('; '));
      const response = await fetch(base + '/');
      assert(response.ok);
      assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
      assert((await response.arrayBuffer()).byteLength < 24 * 1024, 'Homepage HTML exceeds 24 KiB');
      assert((await stat(join(dist, 'reader.js'))).size < 13 * 1024, 'Enhancement exceeds 13 KiB raw');
      assert((await stat(join(dist, 'style.css'))).size < 26 * 1024, 'Global stylesheet exceeds 26 KiB raw');
    }),
  ];
  for (const { name, run } of tests) {
    await run();
    passed++;
    console.log('PASS ' + name);
  }
  console.log(passed + ' browser scenarios passed with the deployment CSP enforced.');
  cdp.close();
  cdp = undefined;
  browser.kill();
  await timeout(exited, 3000, 'Chrome did not exit cleanly').catch(() => browser.kill('SIGKILL'));
} finally {
  cdp?.close();
  browser?.kill();
  app.close();
  app.closeAllConnections();
  await rm(profile, { recursive: true, force: true, maxRetries: 8, retryDelay: 100 });
}
