/* Intent tests for Nyla (js/concierge.js) against a built data/venues.json.
   Run after a build:  node _build/test_nyla.js <built-site-folder>
   Uses a tiny fake DOM, so no browser is needed. Exit code 1 on any failure. */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const site = path.resolve(process.argv[2] || path.join(__dirname, '..'));
const data = JSON.parse(fs.readFileSync(path.join(site, 'data', 'venues.json'), 'utf8'));
const code = fs.readFileSync(path.join(__dirname, 'concierge.js'), 'utf8');

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

async function session(pathname) {
  const body = makeEl();
  const doc = {
    readyState: 'complete', body, currentScript: { src: 'https://nynightlife.com/js/concierge.js' },
    createElement() { return makeEl(); }, querySelector() { return null; }, addEventListener() {}
  };
  const ctx = {
    document: doc, location: { pathname }, window: {}, console,
    Image: function () { return {}; }, localStorage: { getItem() { return String(Date.now()); }, setItem() {} },
    fetch: () => Promise.resolve({ json: () => Promise.resolve(JSON.parse(JSON.stringify(data))) }),
    setTimeout: (f, ms) => setTimeout(f, Math.min(ms || 0, 5)), Date, Math, String, RegExp, Array, Object, JSON
  };
  ctx.window = ctx;
  vm.runInNewContext(code, ctx);
  const panel = body.children[1];
  const msgs = panel.querySelector('.nyb-msgs');
  const form = panel.querySelector('.nyb-inrow');
  const input = panel.querySelector('.nyb-in');
  return async function ask(q) {
    const n = msgs.children.length;
    input.value = q;
    form.listeners.submit({ preventDefault() {} });
    await new Promise(r => setTimeout(r, 120));
    return msgs.children.slice(n + 1).map(m => m.innerHTML).join(' || ');
  };
}

const V = slug => data.venues.find(v => v.slug === slug);
// [page, question, must contain (string or RegExp, all), must NOT contain]
const CASES = [
  ['/', 'hi', ['I’m Nyla'], []],
  ['/', 'cover at House of Yes', ['House of Yes', V('house-of-yes').cover.split(';')[0]], []],
  ['/', 'death and co dress code', ['Death &amp; Co', 'Dress code:'], []],
  ['/', "pdt's dress code", ['Please Don', 'None published (not found yet)'], []],
  ['/', 'knockdown dress code', ['Knockdown Center', '(not found yet)'], []],
  ['/', 'is pdt 21+', ['Age &amp; ID:', 'Not found yet'], []],
  ['/', 'brooklyn mirage', ['<b>Closed.</b>'], []],
  ['/', 'is musica open saturday', ['Heads up', 'Hours:'], []],
  ['/', 'how do I get into Magic Hour', ['Magic Hour', 'How to get in:'], ['Hours:']],
  ['/', 'Skip Magic Hour Rooftop Bar & Lounge?', ['Skip it if'], ['Hours:']],
  ['/', 'closest subway to le bain', ['Subway:'], ['Hours:']],
  ['/', 'how much are cocktails at westlight', ['Drink prices:'], ['Cover:']],
  ['/', 'hosue of yes cover', ['House of Yes', 'Cover:'], []],
  ['/', 'bossa nova', ['Bossa Nova Civic Club'], []],
  ['/', 'whats popular nowadays', [], ['Nowadays</b>']],
  ['/', 'anything elsewhere', [], ['Elsewhere</b>']],
  ['/', 'is elsewhere 18+', ['Elsewhere', 'Age &amp; ID:'], []],
  ['/', 'best rooftop lounge', ['Rooftops:'], ['PHD Rooftop Lounge</b> (']],
  ['/', 'rooftops', ['Le Bain', 'Westlight'], []],
  ['/', 'chelsea rooftops', ['Rooftops in Chelsea', 'PHD Rooftop Lounge'], ['Westlight']],
  ['/', 'bushwick clubs', ['in Bushwick', 'House of Yes'], ['Marquee']],
  ['/', 'live music', ['Public Records'], ['Musica Club NYC</a> (Hell']],
  ['/', '18+ clubs', ['21+ at night', 'Elsewhere', '16+'], []],
  ['/', 'what should i wear to a club', ['stated dress rule', 'Nebula'], ['Attaboy']],
  ['/', 'dress codes', ['stated dress rule', 'nyc-dress-codes.html'], ['Westlight</a>', 'House of Yes</a>']],
  ['/', 'no cover', ['no cover for walk-ins', 'Attaboy'], ['Marquee']],
  ['/', "what's on tonight", ['Tonight in NYC', 'Ticketed'], []],
  ['/', 'bachelorette for 10', ['Bachelorette', '(1 source)', 'Pick for 10'], []],
  ['/', 'where to go for a birthday with 6 friends', ['group playbook', 'with 6 people'], []],
  ['/', 'is the info up to date', ['How we check'], ['Cocktail']],
  ['/', 'reviews', [], ['Rooftops']],
  ['/', 'harlem', ['don’t have checked venues in Harlem'], []],
  ['/', 'hells kitchen', ['Musica'], []],
  ['/', 'les bars', ['Lower East Side', 'Attaboy'], []],
  ['/', 'newsletter', ['weekly email is planned', 'feed.xml'], []],
  ['/', 'me@example.com', ['can’t sign you up'], []],
  ['/', 'asdfgh', ['I answer from this site'], []],
  ['/venues/westlight.html', 'dress code?', ['Westlight', 'Dress code:'], []],
  ['/venues/westlight.html', "what's the cover", ['Westlight', 'Cover:'], []],
  ['/venues/westlight.html', 'is it worth it?', ['Westlight', 'Skip it if'], []],
  ['/venues/westlight.html', 'dress codes', ['stated dress rule'], []],
  ['/venues/westlight.html', 'is it all ages?', ['Westlight', 'All ages until 6pm'], []],
  ['/venues/westlight.html', 'can i bring my 19 year old sister', ['Westlight', 'Age &amp; ID:'], []],
  ['/venues/the-back-room.html', 'can we do a bachelorette here?', ['The Back Room', 'How to get in:', 'achelor'], ['Party bus']],
  ['/venues/le-bain.html', 'westlite cover?', ['Westlight', 'Cover:'], ['Le Bain</b>']],
  ['/venues/le-bain.html', 'atabboy cover', ['Did you mean <b>Attaboy'], []],
  ['/plans/bachelorette-night.html', 'how much?', ['priced for 10'], []],
  ['/', '230 5th cover saturday', ['Cover:', '$20 Sat'], ['Hours:']],
  ['/', 'rooftop bars in midtown', ['Magic Hour', 'Ophelia'], []],
  ['/', 'jazz bars', ['Live music', 'Public Records'], ['Cocktail bars']],
  ['/', 'lgbtq bars', ['don’t have checked venues for that'], ['Cocktail bars']],
  ['/', 'clubs with no cover', ['Le Bain'], ['Attaboy']],
  ['/', 'cheap drinks', ['Drink prices', 'Cocktails'], ['Marquee']],
  ['/', 'bachelorette rooftop', ['Rooftops', 'priced per person'], []],
  ['/', 'anywhere open late', [], ['Did you mean']],
  ['/', 'bachelorette for 10', [], ['((']],
];

(async () => {
  let fail = 0;
  const hrefs = new Set();
  for (const [page, q, want, nope] of CASES) {
    const ask = await session(page);
    const a = await ask(q);
    (a.match(/href="([^"]+)"/g) || []).forEach(h => hrefs.add(h.slice(6, -1)));
    const miss = want.filter(w => !a.includes(w));
    const bad = nope.filter(w => a.includes(w));
    if (!a || miss.length || bad.length) {
      fail++;
      console.log('FAIL', page, JSON.stringify(q), miss.length ? 'missing ' + JSON.stringify(miss) : '', bad.length ? 'unwanted ' + JSON.stringify(bad) : '');
      console.log('     ', a.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 300));
    }
  }
  // every link she produced must exist in the built site
  for (const h of hrefs) {
    if (!h.startsWith('https://nynightlife.com/')) { fail++; console.log('FAIL non-site link', h); continue; }
    let p = path.join(site, h.slice('https://nynightlife.com/'.length));
    if (h.endsWith('/')) p = path.join(p, 'index.html');
    if (!fs.existsSync(p)) { fail++; console.log('FAIL broken link', h); }
  }
  console.log(`${CASES.length - (fail > CASES.length ? CASES.length : fail)}/${CASES.length} intent cases, ${hrefs.size} links checked, ${fail} failures`);
  process.exit(fail ? 1 : 0);
})();
