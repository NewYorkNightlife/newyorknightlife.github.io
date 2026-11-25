/* Every sentence Nyla can say out loud, for _build/nyla_audio.py.
   Run after a build:  node _build/nyla_lines.js <built-site-folder>  -> JSON on stdout
   It runs the real js/concierge.js rules engine (in a tiny fake DOM, like test_nyla.js)
   over a corpus built from data/venues.json: every venue x every question type, every
   category x area, plans, guides, the fixed lines, and "what's on tonight" at every
   moment its answer can change (each event ending, each 5pm/5am edge) from now until
   the end of the events feed. Each spoken reply goes through the real speechText() and
   segments() from js/nyla-voice.js, so the sentences are exactly what the browser hashes.
   A question outside the corpus still gets its text answer; if one of its sentences
   has no file, Nyla answers that one in text only. */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const V = require('./nyla-voice.js');

const site = path.resolve(process.argv[2] || path.join(__dirname, '..'));
const data = JSON.parse(fs.readFileSync(path.join(site, 'data', 'venues.json'), 'utf8'));
const CODE = fs.readFileSync(path.join(__dirname, 'concierge.js'), 'utf8');
const DAYS_AHEAD = +(process.env.NYLA_AUDIO_DAYS || 8);

function makeEl() {
  const kids = {};
  return {
    children: [], style: {}, attrs: {}, listeners: {}, value: '', className: '', innerHTML: '', textContent: '',
    classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); } },
    setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k] || null; },
    appendChild(c) { this.children.push(c); return c; },
    addEventListener(n, f) { this.listeners[n] = f; },
    querySelector(s) { return kids[s] || (kids[s] = makeEl()); },
    focus() {}, get scrollHeight() { return 0; }
  };
}

// A Date whose "now" we set, so "tonight" can be asked at any moment.
let NOW = Date.now();
const RealDate = Date;
function FakeDate(...a) { return a.length ? new RealDate(...a) : new RealDate(NOW); }
FakeDate.prototype = RealDate.prototype;
FakeDate.now = () => NOW; FakeDate.UTC = RealDate.UTC; FakeDate.parse = RealDate.parse;

function session(pathname) {
  const replies = [];
  const timers = [];
  const body = makeEl();
  const doc = {
    readyState: 'complete', body, currentScript: { src: 'https://nynightlife.com/js/concierge.js' },
    createElement() { return makeEl(); }, querySelector() { return null; }, addEventListener() {}
  };
  const ctx = {
    document: doc, location: { pathname }, console,
    Image: function () { return {}; }, localStorage: { getItem() { return String(RealDate.now()); }, setItem() {} },
    fetch: () => Promise.resolve({ json: () => Promise.resolve(JSON.parse(JSON.stringify(data))) }),
    setTimeout: (f) => { timers.push(f); return timers.length; }, clearTimeout() {},
    Date: FakeDate, Intl, Math, String, RegExp, Array, Object, JSON, Promise
  };
  ctx.window = ctx;
  ctx.__nylaOnReply = html => replies.push(html);
  vm.runInNewContext(CODE, ctx);
  const panel = body.children[1];
  const form = panel.querySelector('.nyb-inrow');
  const input = panel.querySelector('.nyb-in');
  async function drain() {
    for (let i = 0; i < 50; i++) {
      await new Promise(r => setImmediate(r));
      if (!timers.length) { await new Promise(r => setImmediate(r)); if (!timers.length) return; }
      const run = timers.splice(0); run.forEach(f => { try { f(); } catch (e) {} });
    }
  }
  return async function ask(q) {
    replies.length = 0;
    input.value = q;
    form.listeners.submit({ preventDefault() {} });
    await drain();
    return replies.slice();
  };
}

const sentences = new Map(); // normalized sentence -> how many corpus answers use it
let answers = 0;
function keep(htmls) {
  htmls.forEach(h => {
    const segs = V.segments(V.speechText(h));
    if (!segs.length) return;
    answers++;
    segs.forEach(s => sentences.set(s, (sentences.get(s) || 0) + 1));
  });
}

function areasOf(venues) {
  const out = new Set();
  venues.forEach(v => String((v.hood || '') + ' / ' + (v.borough || '')).split(/\s*[\/()]\s*/).forEach(a => { a = a.trim(); if (a) out.add(a.toLowerCase()); }));
  ['harlem', 'soho', 'bronx', 'staten island', 'astoria', 'upper east side', 'tribeca', 'park slope', 'long island city'].forEach(a => out.add(a));
  return [...out];
}

(async () => {
  const ask = session('/');
  const venues = data.venues || [];
  const areas = areasOf(venues);
  const fixed = [
    'hi', 'thanks', 'is it safe', 'newsletter', 'me@example.com', 'how do you check your facts',
    'what should I wear', 'dress codes', 'how old do you have to be', 'can under 21 get in', 'do I need a passport for foreign id',
    'what are the hours', 'what is the cover', 'food', 'karaoke', 'gay bars', 'asdf qwerty',
    'open late', 'cheap drinks', 'drink prices', 'what is good', 'where is it',
    'No cover', 'Rooftops', 'Cocktail bars', 'Bachelorette for 10', 'clubs', 'live music', 'speakeasy', 'date night',
    'bachelor party', 'boat party', 'dinner cruise', 'yacht', 'party bus', 'group night out', 'birthday',
    // no cover / free entry phrasings (2026-11-23) and other common asks
    'show me bars with no cover', 'bars with no cover', 'no cover bars', 'free entry bars tonight', 'free entry', 'free bars',
    'no cover tonight', 'free events tonight', 'free things to do tonight', 'where can I dance for free', 'no cover clubs',
    'cheap bars', 'bars', 'show me bars', 'show me rooftops', 'show me clubs', 'live shows', 'happy hour', 'happy hour near me',
    'bars near me', 'clubs near me', 'rooftops near me', 'what is near me', 'karaoke', 'karaoke bars', 'dancing', 'dance clubs',
    'rooftop bars', 'rooftop bars with no cover', 'bars with no cover near me'
  ];
  for (let n = 2; n <= 30; n++) fixed.push('birthday with ' + n + ' friends', 'bachelorette for ' + n);
  for (const q of fixed) keep(await ask(q));

  const FOCUS = ['', 'cover at ', 'dress code at ', 'age at ', 'is 21+ ', 'hours at ', 'how do I get into ', 'drink prices at ',
    'closest subway to ', 'skip ', 'is it worth it ', 'bachelorette group at '];
  for (const v of venues) {
    for (const f of FOCUS) keep(await ask(f + v.name));
    keep(await ask('Dress code at ' + v.name)); keep(await ask('How to get in at ' + v.name));
    keep(await ask('Hours at ' + v.name)); keep(await ask('Skip ' + v.name + '?'));
    keep(await ask('Cover at ' + v.name));
  }
  const CATS = ['', 'rooftops', 'clubs', 'cocktail bars', 'live music', 'no cover', 'rooftops with no cover', 'clubs with no cover',
    'cocktail bars with no cover', 'live music with no cover', 'bars', 'bars with no cover', 'dress codes', 'drink prices', 'open late', 'under 21', 'venues'];
  for (const c of CATS) for (const a of [''].concat(areas)) {
    const q = (c + (a ? ' in ' + a : '')).trim();
    if (q) keep(await ask(q));
  }
  for (const g of data.guides || []) {
    keep(await ask(g.title));
    for (const al of g.aliases || []) keep(await ask(al));
    for (const k of ['comedy', 'speakeasy', 'new year', 'closing time', 'under 21', 'dress code']) keep(await ask(g.title + ' ' + k));
  }
  for (const p of ['/plans/', '/plans/nyc-bachelorette.html']) {
    const ap = session(p);
    for (const q of ['how much', 'how much per person', 'split for 8', 'how much for 12']) keep(await ap(q));
  }

  // "what's on tonight": ask at every moment the answer can change.
  const evs = (data.events || []).filter(e => e && e.start);
  const start = RealDate.now(), stop = start + DAYS_AHEAD * 864e5;
  const moments = new Set([start]);
  evs.forEach(e => {
    const s = new RealDate(e.start).getTime();
    if (isNaN(s)) return;
    let end = e.end ? new RealDate(e.end).getTime() : NaN;
    if (isNaN(end)) end = s + 3 * 3600e3;
    if (end > start && end < stop) moments.add(end + 1000);
  });
  // 5pm and 5am New York edges: probe every hour boundary, the answer only changes at those
  for (let t = Math.ceil(start / 3600e3) * 3600e3; t < stop; t += 3600e3) {
    const h = +new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hour: 'numeric', hourCycle: 'h23' }).format(new RealDate(t));
    if (h === 17 || h === 5) moments.add(t + 1000);
  }
  const TONIGHT = ['what’s on tonight', 'comedy tonight', 'live music tonight', 'dj tonight', 'comedy clubs tonight', 'speakeasy events tonight',
    'rooftop events tonight', 'what’s happening this weekend', 'tonight in brooklyn', 'tonight in manhattan'];
  const sorted = [...moments].sort((a, b) => a - b);
  for (const m of sorted) {
    NOW = m;
    for (const q of TONIGHT) keep(await ask(q));
  }
  NOW = RealDate.now();

  const out = {
    generated: new RealDate().toISOString(),
    answers, moments: sorted.length,
    sentences: [...sentences.keys()].sort()
  };
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack); process.exit(1); });
