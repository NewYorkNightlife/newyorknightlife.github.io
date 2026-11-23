/* Client night window. Run: node _build/test_tonight.js
   Fakes America/New_York via a fixed Date and a tiny DOM. No browser, no deps. */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const code = fs.readFileSync(path.join(__dirname, 'tonight.js'), 'utf8');
let fails = 0;
function check(name, cond) {
  if (!cond) { fails++; console.log('FAIL', name); }
}

function makeEl(tag) {
  const style = {};
  style.setProperty = function (k, v) { this[k] = String(v); };
  const node = {
    tag, tagName: String(tag || '').toUpperCase(), children: [], attrs: {}, className: '', href: '', rel: '', target: '', src: '', alt: '',
    width: 0, height: 0, style, parent: null, parentNode: null, _text: '', listeners: {},
    setAttribute(k, v) { this.attrs[k] = String(v); },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; },
    addEventListener(type, fn) { (this.listeners[type] || (this.listeners[type] = [])).push(fn); },
    appendChild(c) { this.children.push(c); c.parent = this; c.parentNode = this; return c; },
    removeChild(c) {
      const i = this.children.indexOf(c);
      if (i >= 0) this.children.splice(i, 1);
      c.parent = null;
      c.parentNode = null;
      return c;
    }
  };
  Object.defineProperty(node, 'textContent', {
    get() { return this._text; },
    set(v) { this._text = String(v); }
  });
  return node;
}

function walk(node, sel, out) {
  if (node.attrs && node.getAttribute && match(node, sel)) out.push(node);
  (node.children || []).forEach(c => walk(c, sel, out));
}
function match(node, sel) {
  const m = /^\[([a-z0-9-]+)\]$/.exec(sel);
  return !!(m && node.getAttribute(m[1]) != null);
}
function texts(node, cls) {
  const out = [];
  (function rec(n) {
    if (n.className === cls && n.textContent) out.push(n.textContent);
    (n.children || []).forEach(rec);
  })(node);
  return out;
}
function allText(node) {
  let s = node._text || '';
  (node.children || []).forEach(c => { s += ' ' + allText(c); });
  return s;
}

function clock(iso) {
  const fixed = new Date(iso).getTime();
  const Real = Date;
  class FakeDate extends Real {
    constructor(...args) {
      if (args.length === 0) super(fixed);
      else super(...args);
    }
    static now() { return fixed; }
  }
  FakeDate.UTC = Real.UTC;
  FakeDate.parse = Real.parse;
  return FakeDate;
}

const FEED = {
  fetched_at: '2026-11-17T23:18:00-05:00',
  events: [
    { title: 'Ten Oclock Show', start: '2026-11-17T22:00:00-05:00', end: '2026-11-18T01:30:00-05:00', venue_name: 'Hall', category: 'music', url: 'https://www.ticketmaster.com/event/ten', source: 'ticketmaster' },
    { title: 'Seven Ended', start: '2026-11-17T19:00:00-05:00', end: '2026-11-17T22:00:00-05:00', venue_name: 'Hall', category: 'music', url: 'https://www.ticketmaster.com/event/seven', source: 'ticketmaster' },
    { title: 'Next Evening', start: '2026-11-18T19:00:00-05:00', venue_name: 'Hall', category: 'comedy', url: 'https://www.ticketmaster.com/event/next', source: 'ticketmaster' },
    { title: 'Friday Late', start: '2026-11-20T20:00:00-05:00', end: '2026-11-20T23:00:00-05:00', venue_name: 'Hall', category: 'music', url: 'https://www.ticketmaster.com/event/fri', source: 'ticketmaster' },
    { title: 'Saturday Show', start: '2026-11-21T19:00:00-05:00', venue_name: 'Hall', category: 'music', url: 'https://www.ticketmaster.com/event/sat', source: 'ticketmaster' }
  ]
};
const VENUES = {
  venues: [
    { slug: 'attaboy', name: 'Attaboy', hood: 'Lower East Side', status: 'open', hours_kind: 'fixed', url: 'venues/attaboy.html', week: { fri: '17:00-27:00', tue: '17:00-27:00' } },
    { slug: 'house-of-yes', name: 'House of Yes', status: 'open', hours_kind: 'event', week: {} }
  ]
};

function page(kind) {
  const body = makeEl('body');
  const stamp = makeEl('p');
  stamp.setAttribute('data-feed-updated', FEED.fetched_at);
  stamp.textContent = 'Updated 2026-11-17';
  const line = makeEl('p');
  line.className = 'hero-live';
  line.setAttribute('data-night-line', '');
  line.textContent = 'Tue 2026-11-17 · 0 tonight';
  const summary = makeEl('aside');
  summary.setAttribute('data-night-summary', kind);
  summary.setAttribute('data-checked', '29');
  const label = makeEl('p');
  label.textContent = 'Short answer';
  const copy = makeEl('p');
  copy.textContent = 'On Tuesday Nov 17, the feeds we checked list 0 events between 5pm and 5am.';
  summary.appendChild(label);
  summary.appendChild(copy);
  const section = makeEl('section');
  section.setAttribute('data-night-events', '');
  section.setAttribute('data-night-page', kind);
  section.setAttribute('data-events', '/data/events.json');
  section.setAttribute('data-venues', '/data/venues.json');
  const week = makeEl('section');
  week.setAttribute('data-week-events', '');
  [stamp, line, summary, section, week].forEach(n => body.appendChild(n));
  return { body, stamp, line, summary, section, week, copy };
}

function classes(node) {
  return String(node.className || '').split(/\s+/).filter(Boolean);
}
function byClass(node, cls) {
  const out = [];
  (function rec(n) {
    if (classes(n).includes(cls)) out.push(n);
    (n.children || []).forEach(rec);
  })(node);
  return out;
}
function mediaFilled(node) {
  const media = byClass(node, 'pcard-media');
  return media.every((m) => m.children.some((c) => c.tagName === 'IMG' || classes(c).includes('poster')));
}

async function run(iso, kind, feed) {
  const dom = page(kind);
  const doc = {
    currentScript: { src: 'https://nynightlife.com/js/tonight.js?v=test' },
    createElement: makeEl,
    querySelector(sel) {
      const found = [];
      walk(dom.body, sel, found);
      return found[0] || null;
    }
  };
  const ctx = {
    document: doc,
    Intl, URL, Promise, Math, String, RegExp, Array, Object, JSON, isFinite, parseInt,
    Date: clock(iso),
    fetch(url) {
      const u = String(url);
      const payload = u.includes('venues.json') ? VENUES : (feed || FEED);
      return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(payload))) });
    }
  };
  ctx.window = ctx;
  vm.runInNewContext(code, ctx);
  await new Promise(r => setTimeout(r, 30));
  return dom;
}

function bareZero(text) {
  return /(^|[^\d])0 (events|tonight|of those)\b/.test(text) || /\b(list|lists) 0\b/.test(text);
}

function walkHtml(dir, out) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ent.name === '_build' || ent.name === '.git' || ent.name === 'node_modules') continue;
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walkHtml(p, out);
    else if (ent.name.endsWith('.html')) out.push(p);
  }
}
function elementInner(html, openEnd) {
  const re = /<\/?(span|div)\b[^>]*>|<img\b[^>]*>/gi;
  re.lastIndex = openEnd;
  let depth = 1;
  let m;
  while ((m = re.exec(html))) {
    const tok = m[0];
    if (/^<img\b/i.test(tok)) continue;
    if (tok.startsWith('</')) {
      depth -= 1;
      if (depth === 0) return html.slice(openEnd, m.index);
    } else depth += 1;
  }
  return '';
}
function checkBuiltMedia() {
  const root = path.join(__dirname, '..');
  const files = [];
  walkHtml(root, files);
  let seen = 0;
  for (const file of files) {
    const html = fs.readFileSync(file, 'utf8');
    const openRe = /<(span|div)\b([^>]*\bclass="[^"]*"[^>]*)>/gi;
    let m;
    while ((m = openRe.exec(html))) {
      const classM = /\bclass="([^"]*)"/.exec(m[2]);
      if (!classM) continue;
      const cls = classM[1].split(/\s+/);
      const card = cls.includes('pcard-media');
      const pattern = (cls.includes('vthumb') || cls.includes('plate')) && cls.includes('pattern');
      if (!card && !pattern) continue;
      seen += 1;
      const inner = elementInner(html, m.index + m[0].length);
      const ok = /<img\b/i.test(inner) || /\bclass="poster[\s"]/.test(inner);
      if (!ok) {
        const rel = path.relative(root, file);
        check(rel + ' media has an img or a poster', false);
      }
    }
  }
  check('built card media was scanned', seen > 0);
}

(async () => {
  const one = await run('2026-11-18T01:00:00-05:00', 'tonight');
  check('1am date is still Tuesday night', one.line.textContent.startsWith('Tue 2026-11-17 · 1 tonight'));
  check('1am updated stamp is the feed time', one.stamp.textContent === 'Updated 2026-11-17 11:18pm ET');
  const tonightTitles = texts(one.section, 't');
  const weekTitles = texts(one.week, 't');
  check('1am tonight card is the 10pm show', tonightTitles.indexOf('Ten Oclock Show') === 0 && tonightTitles.indexOf('Seven Ended') < 0);
  check('1am hides the ended 7pm show entirely', allText(one.section).indexOf('Seven Ended') < 0 && allText(one.week).indexOf('Seven Ended') < 0);
  check('1am keeps the next evening out of tonight', tonightTitles.indexOf('Next Evening') < 0 && weekTitles.indexOf('Next Evening') >= 0);
  check('1am summary names Tuesday and not a bare zero',
    one.copy.textContent.indexOf('Tuesday Nov 17') >= 0 && one.copy.textContent.indexOf('1 events') >= 0 && !bareZero(one.copy.textContent));

  const later = await run('2026-11-20T18:00:00-05:00', 'home');
  check('later-day home date is Friday', later.line.textContent.startsWith('Fri 2026-11-20 · 1 tonight'));
  check('later-day card is Friday night', texts(later.section, 't').indexOf('Friday Late') >= 0);
  check('later-day does not keep the baked Tuesday line', later.line.textContent.indexOf('2026-11-17') < 0);
  check('later-day updated stamp is still the refresh', later.stamp.textContent === 'Updated 2026-11-17 11:18pm ET');

  const emptyFeed = { fetched_at: FEED.fetched_at, events: [FEED.events[4]] };
  const saved = FEED.events;
  FEED.events = emptyFeed.events;
  const empty = await run('2026-11-20T18:00:00-05:00', 'tonight');
  FEED.events = saved;
  check('empty night has no bare zero', empty.line.textContent.startsWith('Fri 2026-11-20 · Nothing listed tonight') && !bareZero(empty.line.textContent) && !bareZero(allText(empty.section)));
  check('empty night shows the next event', texts(empty.section, 't').indexOf('Saturday Show') >= 0);
  check('empty night shows the late venue', texts(empty.section, 't').indexOf('Attaboy') >= 0);
  check('empty night does not invent a zero count', allText(empty.section).indexOf('0 events') < 0 && empty.copy.textContent.indexOf('list 0') < 0);

  const midweek = await run('2026-11-18T18:00:00-05:00', 'weekend');
  check('wednesday weekend is Fri Nov 20 through Sun Nov 22',
    midweek.line.textContent === 'Fri\u2013Sun Nov 20\u201322 \u00b7 2 events');
  check('wednesday weekend shows friday and saturday',
    texts(midweek.section, 't').indexOf('Friday Late') >= 0 && texts(midweek.section, 't').indexOf('Saturday Show') >= 0);
  check('wednesday weekend leaves out tuesday', allText(midweek.section).indexOf('Ten Oclock Show') < 0);
  check('wednesday weekend summary names the days and not a bare zero',
    midweek.copy.textContent.indexOf('Friday Nov 20 through Sunday Nov 22') >= 0 && !bareZero(midweek.copy.textContent));
  check('saturday night stays on sunday', allText(midweek.section).indexOf('Saturday Nov 21') >= 0);

  const mondayNight = await run('2026-11-23T01:00:00-05:00', 'weekend');
  check('monday 1am is still the Nov 20 weekend',
    mondayNight.line.textContent.indexOf('Nov 20\u201322') >= 0 && mondayNight.line.textContent.indexOf('Nothing listed') >= 0);
  check('monday 1am summary does not roll to the next friday',
    mondayNight.copy.textContent.indexOf('November 27') < 0 && mondayNight.copy.textContent.indexOf('Nov 27') < 0);

  const mondayDay = await run('2026-11-23T10:00:00-05:00', 'weekend');
  check('monday morning rolls to the next weekend',
    mondayDay.line.textContent === 'Fri\u2013Sun Nov 27\u201329 \u00b7 Nothing listed');
  check('rolled weekend has no bare zero', !bareZero(mondayDay.line.textContent) && !bareZero(mondayDay.copy.textContent));

  for (const [name, dom] of [['1am', one], ['later-day', later], ['empty', empty], ['weekend', midweek], ['monday-night', mondayNight], ['monday-day', mondayDay]]) {
    check(name + ' card media has a photo or a poster', mediaFilled(dom.section) && mediaFilled(dom.week));
  }
  const late = byClass(empty.section, 'pcard').find((c) => texts(c, 't').includes('Attaboy'));
  const latePoster = late && byClass(late, 'poster')[0];
  check('open-past-midnight card is a poster, not a letter', latePoster && byClass(late, 'mark').length === 0 && classes(byClass(late, 'pcard-media')[0]).includes('is-poster'));
  check('open-past-midnight poster names the venue and neighborhood',
    latePoster && texts(latePoster, 'poster-cat').includes('Nightlife') && texts(latePoster, 'poster-t').includes('Attaboy') && texts(latePoster, 'poster-m').includes('Lower East Side'));
  check('poster variant is pv0-pv5 with anchors',
    latePoster && classes(latePoster).some((c) => /^pv[0-5]$/.test(c)) && /^\d+%$/.test(latePoster.style['--px']) && /^\d+%$/.test(latePoster.style['--py']));

  const shotFeed = {
    fetched_at: FEED.fetched_at,
    events: [
      { title: 'Ticketm Photo', start: '2026-11-17T22:00:00-05:00', end: '2026-11-18T01:30:00-05:00', venue_name: 'Hall', category: 'music', url: 'https://www.ticketmaster.com/event/a', source: 'ticketmaster', image_url: 'https://s1.ticketm.net/x.jpg', image_w: 640, image_h: 360 },
      { title: 'Ticketmaster Photo', start: '2026-11-17T22:30:00-05:00', end: '2026-11-18T02:00:00-05:00', venue_name: 'Garden', category: 'comedy', url: 'https://www.ticketmaster.com/event/b', source: 'ticketmaster', image_url: 'https://www.ticketmaster.com/x.jpg' },
      { title: 'Parks Photo', start: '2026-11-17T21:00:00-05:00', end: '2026-11-18T01:30:00-05:00', venue_name: 'Lawn', category: 'parks', url: 'https://www.nycgovparks.org/events/1', source: 'nyc_parks', image_url: 'https://www.nycgovparks.org/x.jpg' },
      { title: 'Evil Host', start: '2026-11-17T23:00:00-05:00', venue_name: 'Nowhere', category: 'music', url: 'https://www.ticketmaster.com/event/c', source: 'ticketmaster', image_url: 'https://evilticketm.net/x.jpg' },
      { title: 'No Picture', start: '2026-11-17T23:15:00-05:00', venue_name: 'Park', category: 'parks', url: '/tonight/', source: 'nyc_parks' }
    ]
  };
  const shots = await run('2026-11-18T01:00:00-05:00', 'tonight', shotFeed);
  function cardNamed(title) {
    return byClass(shots.section, 'pcard').find((c) => texts(c, 't').includes(title));
  }
  function imgOf(card) {
    const media = card && byClass(card, 'pcard-media')[0];
    return media && media.children.find((c) => c.tagName === 'IMG');
  }
  const tm = cardNamed('Ticketm Photo');
  const tcom = cardNamed('Ticketmaster Photo');
  const parks = cardNamed('Parks Photo');
  const evil = cardNamed('Evil Host');
  const none = cardNamed('No Picture');
  check('safeImage accepts https://s1.ticketm.net/x.jpg', imgOf(tm) && imgOf(tm).src === 'https://s1.ticketm.net/x.jpg');
  check('safeImage accepts https://www.ticketmaster.com/x.jpg', imgOf(tcom) && imgOf(tcom).src === 'https://www.ticketmaster.com/x.jpg');
  check('safeImage accepts a nycgovparks.org image', imgOf(parks) && imgOf(parks).src === 'https://www.nycgovparks.org/x.jpg');
  check('safeImage rejects https://evilticketm.net/x.jpg',
    evil && imgOf(evil) && imgOf(evil).src.indexOf('evilticketm') < 0 && /img\/home-640\.webp$/.test(imgOf(evil).src) && byClass(evil, 'poster').length === 0);
  check('event without a photo gets a real category photo, not a poster',
    none && imgOf(none) && /img\/event-parks-640\.webp$/.test(imgOf(none).src)
    && classes(byClass(none, 'pcard-media')[0]).includes('has-place-photo') && byClass(none, 'poster').length === 0);
  check('shot cards all have a photo or a poster', mediaFilled(shots.section));
  const broken = imgOf(tm);
  (broken.listeners.error || []).forEach((fn) => fn());
  const brokenMedia = byClass(tm, 'pcard-media')[0];
  check('a broken photo is swapped for a poster',
    brokenMedia && !brokenMedia.children.some((c) => c.tagName === 'IMG') && byClass(brokenMedia, 'poster').length === 1 && classes(brokenMedia).includes('is-poster'));

  // With a photo in /data/venues.json, the late venue card and that venue's
  // events use the venue photo, and no poster is drawn.
  const savedVenues = VENUES.venues[0].photo;
  VENUES.venues[0].photo = 'img/attaboy-640.webp';
  const photoFeed = { fetched_at: FEED.fetched_at, events: [
    { title: 'At Attaboy', start: '2026-11-17T23:30:00-05:00', venue_name: 'Attaboy', venue_slug: 'attaboy', category: 'nightlife', url: '/tonight/', source: 'nyc_parks' },
    { title: 'Merchant Show', start: '2026-11-17T23:40:00-05:00', venue_name: "Merchant's House Museum", category: 'parks', url: '/tonight/', source: 'nyc_parks' }
  ] };
  const withPhoto = await run('2026-11-18T01:00:00-05:00', 'tonight', photoFeed);
  const atCard = byClass(withPhoto.section, 'pcard').find((c) => texts(c, 't').includes('At Attaboy'));
  check('event at a venue uses the venue photo', atCard && imgOf(atCard) && /img\/attaboy-640\.webp$/.test(imgOf(atCard).src));
  const mhCard = byClass(withPhoto.section, 'pcard').find((c) => texts(c, 't').includes('Merchant Show'));
  check('event at a named place uses that place photo', mhCard && imgOf(mhCard) && /img\/merchants-house-museum-640\.webp$/.test(imgOf(mhCard).src));
  const emptyPhoto = await run('2026-11-20T18:00:00-05:00', 'tonight', { fetched_at: FEED.fetched_at, events: [FEED.events[4]] });
  const lateP = byClass(emptyPhoto.section, 'pcard').find((c) => texts(c, 't').includes('Attaboy'));
  check('open-past-midnight card uses the venue photo when there is one',
    lateP && imgOf(lateP) && /img\/attaboy-640\.webp$/.test(imgOf(lateP).src) && byClass(lateP, 'poster').length === 0);
  VENUES.venues[0].photo = savedVenues;

  checkBuiltMedia();

  console.log(fails ? fails + ' FAILED' : 'OK: tonight client');
  process.exit(fails ? 1 : 0);
})().catch(err => {
  console.error(err);
  process.exit(1);
});
