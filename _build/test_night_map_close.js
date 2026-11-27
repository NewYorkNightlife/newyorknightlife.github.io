/* One tap on a cluster card's Close must hide it within 100ms.
   Run: node _build/test_night_map_close.js
   Needs Chrome and puppeteer or puppeteer-core. Serves the site itself. */
'use strict';

const fs = require('fs');
const http = require('http');
const net = require('net');
const path = require('path');
const { spawn } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const CHROME = [
  process.env.CHROME_PATH,
  '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable',
  '/usr/local/bin/google-chrome',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser'
].filter(Boolean).find(function (file) { return fs.existsSync(file); });

let puppeteer;
try { puppeteer = require('puppeteer'); }
catch (err) {
  try { puppeteer = require('puppeteer-core'); }
  catch (err2) {
    console.log('FAIL puppeteer is not installed');
    process.exit(1);
  }
}

function freePort() {
  return new Promise(function (resolve, reject) {
    const probe = net.createServer();
    probe.once('error', reject);
    probe.listen(0, '127.0.0.1', function () {
      const port = probe.address().port;
      probe.close(function () { resolve(port); });
    });
  });
}

function serve(port) {
  const child = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
    cwd: ROOT,
    stdio: 'ignore',
    env: Object.assign({}, process.env, { PYTHONUNBUFFERED: '1' })
  });
  return new Promise(function (resolve, reject) {
    const started = Date.now();
    function ping() {
      const req = http.get('http://127.0.0.1:' + port + '/', function (res) {
        res.resume();
        resolve(child);
      });
      req.on('error', function () {
        if (Date.now() - started > 8000) reject(new Error('server did not start'));
        else setTimeout(ping, 80);
      });
    }
    ping();
  });
}

async function openCluster(page) {
  await page.waitForSelector('.nmap-pin.is-cluster', { timeout: 8000 });
  for (let i = 0; i < 6; i++) await page.click('[data-zoom="in"]');
  await new Promise(function (r) { setTimeout(r, 800); });
  const pins = await page.$$('.nmap-pin.is-cluster');
  if (!pins.length) throw new Error('no cluster pin after zoom');
  const box = await pins[0].boundingBox();
  return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
}

async function cardState(page) {
  return page.$eval('[data-card]', function (el) {
    const close = el.querySelector('.nmap-close');
    const rect = close ? close.getBoundingClientRect() : null;
    return {
      hidden: el.hidden,
      links: el.querySelectorAll('a').length,
      close: rect ? { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, w: rect.width, h: rect.height } : null
    };
  });
}

async function armTimer(page) {
  await page.evaluate(function () {
    window.__closeMs = null;
    const card = document.querySelector('[data-card]');
    const btn = card.querySelector('.nmap-close');
    btn.addEventListener('pointerup', function () {
      window.__closeT0 = performance.now();
    }, { capture: true, once: true });
    const obs = new MutationObserver(function () {
      if (card.hidden && window.__closeT0 != null && window.__closeMs == null) {
        window.__closeMs = performance.now() - window.__closeT0;
      }
    });
    obs.observe(card, { attributes: true, attributeFilter: ['hidden'] });
  });
}

async function tap(page, x, y, touch) {
  if (!touch) {
    await page.mouse.click(x, y);
    return;
  }
  const client = await page.createCDPSession();
  await client.send('Input.dispatchTouchEvent', {
    type: 'touchStart',
    touchPoints: [{ x: x, y: y, id: 1 }]
  });
  await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await client.detach();
}

async function scenario(browser, name, viewport, touch) {
  const page = await browser.newPage();
  await page.setViewport(viewport);
  const base = process.env.MAP_URL || ('http://127.0.0.1:' + serverPort + '/');
  await page.goto(base + '?close=' + encodeURIComponent(name), { waitUntil: 'networkidle0', timeout: 60000 });
  await page.$eval('#night-map', function (el) { el.scrollIntoView({ block: 'center' }); });
  await page.waitForSelector('#night-map .night-map-canvas svg', { timeout: 15000 });
  const spot = await openCluster(page);
  await page.mouse.click(spot.x, spot.y);
  await new Promise(function (r) { setTimeout(r, 300); });
  let state = await cardState(page);
  if (state.hidden || state.links < 2) {
    await page.mouse.click(spot.x, spot.y);
    await new Promise(function (r) { setTimeout(r, 300); });
    state = await cardState(page);
  }
  if (state.hidden || state.links < 2 || !state.close) {
    throw new Error(name + ' did not open a cluster card ' + JSON.stringify(state));
  }
  if (state.close.w < 44 || state.close.h < 44) {
    throw new Error(name + ' close hit area is ' + state.close.w + 'x' + state.close.h);
  }
  await armTimer(page);
  await tap(page, state.close.x, state.close.y, touch);
  await new Promise(function (r) { setTimeout(r, 120); });
  const result = await page.evaluate(function () {
    const card = document.querySelector('[data-card]');
    return { hidden: card.hidden, ms: window.__closeMs, links: card.querySelectorAll('a').length };
  });
  if (!result.hidden) throw new Error(name + ' card still open after one tap');
  if (result.ms == null || result.ms > 100) throw new Error(name + ' closed in ' + result.ms + 'ms');
  await new Promise(function (r) { setTimeout(r, 200); });
  const stayed = await page.$eval('[data-card]', function (el) { return el.hidden; });
  if (!stayed) throw new Error(name + ' card reopened');
  console.log('PASS', name, result.ms.toFixed(1) + 'ms', 'links', state.links);

  await new Promise(function (r) { setTimeout(r, 450); });
  const single = await page.evaluate(function () {
    const stage = document.querySelector('.night-map-stage').getBoundingClientRect();
    const pins = document.querySelectorAll('.nmap-pin:not(.is-cluster)');
    for (let i = 0; i < pins.length; i++) {
      const r = pins[i].getBoundingClientRect();
      const x = r.x + r.width / 2;
      const y = r.y + r.height / 2;
      if (x < stage.left + 8 || x > stage.right - 8 || y < stage.top + 8 || y > stage.bottom - 70) continue;
      const hit = document.elementFromPoint(x, y);
      if (hit && hit.closest && hit.closest('.nmap-pin') === pins[i]) return { x: x, y: y };
    }
    return null;
  });
  if (!single) throw new Error(name + ' found no visible single pin');
  await page.mouse.click(single.x, single.y);
  await new Promise(function (r) { setTimeout(r, 200); });
  const one = await cardState(page);
  if (one.hidden || one.links < 1 || !one.close) throw new Error(name + ' single pin did not open ' + JSON.stringify(one));
  await armTimer(page);
  await tap(page, one.close.x, one.close.y, touch);
  await new Promise(function (r) { setTimeout(r, 120); });
  const done = await page.evaluate(function () {
    return { hidden: document.querySelector('[data-card]').hidden, ms: window.__closeMs };
  });
  if (!done.hidden || done.ms == null || done.ms > 100) {
    throw new Error(name + ' single-pin card ' + JSON.stringify(done));
  }
  console.log('PASS', name, 'single-pin', done.ms.toFixed(1) + 'ms');
  if (name === 'desktop-mouse') {
    const again = await page.evaluate(function () {
      const pin = document.querySelector('.nmap-pin.is-cluster');
      if (!pin) return null;
      const r = pin.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    });
    await page.mouse.click(again.x, again.y);
    await new Promise(function (r) { setTimeout(r, 250); });
    await page.keyboard.press('Escape');
    await new Promise(function (r) { setTimeout(r, 80); });
    const escaped = await page.$eval('[data-card]', function (el) { return el.hidden; });
    if (!escaped) throw new Error('escape did not close the card');
    console.log('PASS escape');
    await page.mouse.click(again.x, again.y);
    await new Promise(function (r) { setTimeout(r, 250); });
    const bg = await page.evaluate(function () {
      const stage = document.querySelector('.night-map-stage').getBoundingClientRect();
      const map = document.querySelector('#night-map .night-map-canvas');
      for (let y = 16; y < stage.height - 16; y += 14) {
        for (let x = 16; x < stage.width - 70; x += 14) {
          const hit = document.elementFromPoint(stage.left + x, stage.top + y);
          if (hit && map.contains(hit)) return { x: stage.left + x, y: stage.top + y };
        }
      }
      return null;
    });
    if (!bg) throw new Error('no empty map background');
    await page.mouse.click(bg.x, bg.y);
    await new Promise(function (r) { setTimeout(r, 80); });
    const cleared = await page.$eval('[data-card]', function (el) { return el.hidden; });
    if (!cleared) throw new Error('background click did not close the card');
    console.log('PASS background');
  }
  await page.close();
}

let serverPort = 0;
let serverChild = null;

(async function main() {
  if (!process.env.MAP_URL) {
    serverPort = await freePort();
    serverChild = await serve(serverPort);
  }
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: CHROME || undefined,
    args: ['--no-sandbox', '--disable-dev-shm-usage']
  });
  try {
    await scenario(browser, 'desktop-mouse', { width: 1280, height: 900, deviceScaleFactor: 1 }, false);
    await scenario(browser, 'desktop-touch', { width: 1280, height: 900, deviceScaleFactor: 1, hasTouch: true, isMobile: false }, true);
    await scenario(browser, 'phone-mouse', { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true }, false);
    await scenario(browser, 'phone-touch', { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true }, true);
  } finally {
    await browser.close();
    if (serverChild) serverChild.kill();
  }
  console.log('ALL PASS');
})().catch(function (err) {
  console.log('FAIL', err && err.stack ? err.stack : err);
  if (serverChild) serverChild.kill();
  process.exit(1);
});
