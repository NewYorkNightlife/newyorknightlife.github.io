/* NYBot v3 — the NY Nightlife concierge cast. Rules-based, answers only from site data.
   v2: speech bubble above avatar (4s delay, page-aware lines, re-shows after 45 min), multi-pose avatar.
   v3: per-page mascot routing — neighbourhood pages get their own mascot, everything else gets Nyla.
   v4 (2026-10 rebuild): answers come from /data/venues.json, generated from the verified venue files;
   no live feed or newsletter; links work from any folder depth (preview or live). */
(function () {
  'use strict';
  var VENUES = null, PLANS = [];

  // Site root, taken from this script's own URL, so links and art resolve on
  // nynightlife.com and in a relative-link preview alike.
  var SRC = (document.currentScript && document.currentScript.src) || '';
  var ROOT = /js\/concierge\.js/.test(SRC) ? SRC.replace(/js\/concierge\.js.*$/, '') : '/';
  function R(p) { return ROOT + String(p).replace(/^\//, ''); }

  // ---------- mascot cast ----------
  // Full-body 3D renders, transparent PNG so she stands free on the page.
  // Art lives at /assets/mascots/<slug>.png (full body) + <slug>-head.png (256² crop).
  // Nyla is the default and the ONLY cast member whose files are guaranteed to
  // exist — her two originals predate the mascots folder, so she doubles as the
  // fallback for every mascot whose PNGs have not been produced yet.
  var DEFAULT_SLUG = 'nyla';
  function mascot(slug, name) {
    return { name: name, body: R('assets/mascots/' + slug + '.png'), head: R('assets/mascots/' + slug + '-head.png') };
  }
  var MASCOTS = {
    'nyla':              { name: 'Nyla', body: R('assets/nyla-full-welcome.png'), head: R('assets/nyla-head.png') },
    'bushwick':          mascot('bushwick', 'Nika'),
    'williamsburg':      mascot('williamsburg', 'Frankie'),
    'meatpacking':       mascot('meatpacking', 'Simone'),
    'upper-east-side':   mascot('upper-east-side', 'Margot'),
    'upper-west-side':   mascot('upper-west-side', 'Eleanor'),
    'harlem':            mascot('harlem', 'Josephine'),
    'east-village':      mascot('east-village', 'Joan'),
    'west-village':      mascot('west-village', 'Colette'),
    'hells-kitchen':     mascot('hells-kitchen', 'Birdie'),
    'midtown':           mascot('midtown', 'Sloane'),
    'astoria':           mascot('astoria', 'Thea'),
    'flushing':          mascot('flushing', 'June'),
    'jackson-heights':   mascot('jackson-heights', 'Alma'),
    'long-island-city':  mascot('long-island-city', 'Iris'),
    'park-slope':        mascot('park-slope', 'Nora'),
    'bed-stuy':          mascot('bed-stuy', 'Zora'),
    'red-hook':          mascot('red-hook', 'Quinn'),
    'bronx':             mascot('bronx', 'Lena'),
    'downtown-brooklyn': mascot('downtown-brooklyn', 'Robin'),
    // Borough-level mascots. These stand for a whole borough rather than one
    // neighbourhood, so they are deliberately broader in character than the
    // neighbourhood cast and never duplicate one of them.
    'manhattan':         mascot('manhattan', 'Ava'),
    'brooklyn':          mascot('brooklyn', 'Sadie'),
    'queens':            mascot('queens', 'Winnie'),
    'staten-island':     mascot('staten-island', 'Marlowe')
  };

  // Path pattern -> slug, per MASCOT-ROSTER.md "Pages served". Anchored and
  // tested in order; anything that matches nothing falls through to Nyla.
  var ROUTES = [
    [/^\/neighborhoods\/(bushwick|ridgewood)-nightlife\.html$/,             'bushwick'],
    [/^\/neighborhoods\/(williamsburg|greenpoint)-nightlife\.html$/,        'williamsburg'],
    [/^\/neighborhoods\/(meatpacking|chelsea)-nightlife\.html$/,            'meatpacking'],
    [/^\/neighborhoods\/upper-east-side-nightlife\.html$/,                  'upper-east-side'],
    [/^\/neighborhoods\/upper-west-side-nightlife\.html$/,                  'upper-west-side'],
    [/^\/neighborhoods\/harlem-nightlife\.html$/,                           'harlem'],
    [/^\/neighborhoods\/(east-village|lower-east-side)-nightlife\.html$/,   'east-village'],
    [/^\/neighborhoods\/(west-village|soho)-nightlife\.html$/,              'west-village'],
    [/^\/neighborhoods\/hells-kitchen-nightlife\.html$/,                    'hells-kitchen'],
    [/^\/neighborhoods\/(midtown|financial-district)-nightlife\.html$/,     'midtown'],
    [/^\/neighborhoods\/astoria-nightlife\.html$/,                          'astoria'],
    [/^\/neighborhoods\/flushing-nightlife\.html$/,                         'flushing'],
    [/^\/neighborhoods\/jackson-heights-nightlife\.html$/,                  'jackson-heights'],
    [/^\/neighborhoods\/(long-island-city|dumbo)-nightlife\.html$/,         'long-island-city'],
    [/^\/neighborhoods\/(park-slope|cobble-hill|forest-hills)-nightlife\.html$/, 'park-slope'],
    [/^\/neighborhoods\/(bed-stuy|crown-heights)-nightlife\.html$/,         'bed-stuy'],
    [/^\/neighborhoods\/red-hook-nightlife\.html$/,                         'red-hook'],
    [/^\/neighborhoods\/bronx-nightlife-guide\.html$/,                      'bronx'],
    [/^\/boroughs\/bronx-nightlife\.html$/,                                 'bronx'],
    [/^\/neighborhoods\/downtown-brooklyn-nightlife\.html$/,                'downtown-brooklyn'],
    [/^\/neighborhoods\/staten-island-nightlife-guide\.html$/,              'staten-island'],
    [/^\/boroughs\/staten-island-nightlife\.html$/,                         'staten-island'],
    // Borough hubs
    [/^\/boroughs\/manhattan-nightlife\.html$/,                             'manhattan'],
    [/^\/boroughs\/brooklyn-nightlife\.html$/,                              'brooklyn'],
    [/^\/boroughs\/queens-nightlife\.html$/,                                'queens']
  ];

  function pickMascot() {
    var p = String(location.pathname || '').toLowerCase();
    for (var i = 0; i < ROUTES.length; i++) {
      if (ROUTES[i][0].test(p) && MASCOTS[ROUTES[i][1]]) return ROUTES[i][1];
    }
    return DEFAULT_SLUG;
  }

  // ART is what the widget actually renders. It starts as Nyla — the one cast
  // member we know is on disk — and only upgrades to the routed mascot once both
  // of her PNGs have genuinely loaded. A 404 therefore costs nothing: no broken
  // image, no name/face mismatch, just Nyla. Drop bushwick.png + bushwick-head.png
  // into site/assets/mascots/ and Nika lights up on the next page view.
  var SLUG = pickMascot();
  var WANTED = MASCOTS[SLUG] || MASCOTS[DEFAULT_SLUG];
  var ART = MASCOTS[DEFAULT_SLUG];
  window.__nybMascot = DEFAULT_SLUG;

  // Same preload-then-commit pattern as poseOk below, but all-or-nothing across
  // the pair so the head crop and the body are never from different mascots.
  function preloadAll(srcs, cb) {
    var left = srcs.length, ok = true;
    if (!left) return cb(false);
    srcs.forEach(function (src) {
      var t = new Image();
      t.onload = function () { if (!--left) cb(ok); };
      t.onerror = function () { ok = false; if (!--left) cb(ok); };
      t.src = src;
    });
  }

  // Poses for the active mascot. Only `welcome` (the body render) exists today;
  // add more here as they are produced — missing files fall back to POSES[0].
  var POSES = [ART.body];
  var poseOk = [true];
  function pose(i) { return (POSES[i] && poseOk[i]) ? POSES[i] : POSES[0]; }

  var AVATAR_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><radialGradient id="nybg" cx="50%" cy="35%" r="80%"><stop offset="0%" stop-color="#232746"/><stop offset="100%" stop-color="#0d0f1c"/></radialGradient></defs><rect width="100" height="100" fill="url(#nybg)"/><g><path d="M50 18c-14 0-23 9-24 21-1 9 1 15-3 22-2 4 1 6 3 6h48c2 0 5-2 3-6-4-7-2-13-3-22-1-12-10-21-24-21z" fill="#2a2136"/><ellipse cx="50" cy="44" rx="13" ry="15" fill="#b07d52"/><path d="M37 40c0-9 6-15 13-15s13 6 13 15c-2-6-6-8-13-8s-11 2-13 8z" fill="#231a2e"/><path d="M32 88c2-14 9-20 18-20s16 6 18 20z" fill="#191325"/><circle cx="41" cy="58" r="1.6" fill="#d4af37"/><circle cx="59" cy="58" r="1.6" fill="#d4af37"/></g></svg>';

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function track(n) { try { if (window.posthog && posthog.capture) posthog.capture(n, { mascot: window.__nybMascot }); } catch (e) {} }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // ---------- UI ----------
  var bubble = el('button', 'nyb-bubble');
  bubble.setAttribute('aria-label', 'Chat with ' + ART.name + ', the nightlife concierge');
  var bubbleImg = new Image();
  bubbleImg.src = POSES[0];
  bubbleImg.alt = '';
  bubbleImg.onerror = function () { bubble.innerHTML = AVATAR_SVG; bubbleImg = null; };
  bubble.appendChild(bubbleImg);

  var panel = el('div', 'nyb-panel');
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-label', 'Nightlife concierge chat');
  panel.innerHTML =
    '<div class="nyb-head">' +
      // the header always uses the HEAD crop — a full-body render is unreadable at 44px
      '<div class="nyb-head-ava"><img data-src="' + ART.head + '" alt="" onerror="this.parentNode.innerHTML=window.__nybSvg"></div>' +
      '<div><div class="nyb-head-name">' + esc(ART.name) + '</div><div class="nyb-head-sub"><span class="nyb-dot"></span>NYC night concierge</div></div>' +
      '<button class="nyb-close" aria-label="Close chat">&times;</button>' +
    '</div>' +
    '<div class="nyb-msgs" aria-live="polite"></div>' +
    '<div class="nyb-typing">' + esc(ART.name) + ' is typing…</div>' +
    '<div class="nyb-chips"></div>' +
    '<form class="nyb-inrow"><input class="nyb-in" type="text" placeholder="Ask about a venue, dress codes, covers…" aria-label="Message" /><button class="nyb-send" type="submit">Ask</button></form>';
  window.__nybSvg = AVATAR_SVG;

  // Commit the routed mascot only if her art really loaded (see ART above).
  function applyMascot(m) {
    ART = m;
    window.__nybMascot = SLUG;
    POSES[0] = m.body;
    if (bubbleImg) bubbleImg.src = m.body;
    bubble.setAttribute('aria-label', 'Chat with ' + m.name + ', the nightlife concierge');
    var headImg = panel.querySelector('.nyb-head-ava img');
    if (headImg) headImg.src = m.head;
    var nameEl = panel.querySelector('.nyb-head-name');
    if (nameEl) nameEl.textContent = m.name;
    if (typing) typing.textContent = m.name + ' is typing…';
  }
  if (WANTED !== ART) {
    preloadAll([WANTED.body, WANTED.head], function (ok) {
      if (ok) applyMascot(WANTED);
    });
  }

  var msgs, chipsEl, input, typing;

  function say(html, who) {
    var m = el('div', 'nyb-m ' + (who || 'bot'), html);
    msgs.appendChild(m); msgs.scrollTop = msgs.scrollHeight;
  }
  function botSay(html, delay) {
    typing.style.display = 'block';
    setTimeout(function () { typing.style.display = 'none'; say(html, 'bot'); }, delay || 450);
  }
  function setChips(list) {
    chipsEl.innerHTML = '';
    list.forEach(function (c) {
      var b = el('button', 'nyb-chip', esc(c));
      b.type = 'button';
      b.addEventListener('click', function () { handle(c); });
      chipsEl.appendChild(b);
    });
  }
  var DEFAULT_CHIPS = ['Dress codes', 'No cover', 'Rooftops', 'Cocktail bars', 'Bachelorette for 10'];

  // ---------- data ----------
  // /data/venues.json is generated by _build/nyla.py from the same verified
  // venue files the pages are built from, so her answers match the pages.
  // A failed or old-format load leaves VENUES null so the next question retries.
  function loadVenues(cb) {
    if (VENUES) return cb(true);
    fetch(R('data/venues.json')).then(function (r) { return r.json(); }).then(function (d) {
      var ok = !!(d && d.schema === 2 && d.venues && d.venues.length && Array.isArray(d.venues[0].tags));
      if (ok) { VENUES = d.venues; PLANS = d.plans || []; }
      return ok;
    }, function () { return false; }).then(function (ok) {
      setTimeout(function () { cb(ok); }, 0); // outside the promise, so an answer bug can't pose as a network error
    });
  }
  function live() { return (VENUES || []).filter(function (v) { return v.status !== 'closed'; }); }
  function has(v, tag) { return v.tags.indexOf(tag) !== -1; }
  function ALL_LINK() { return '<a href="' + R('venues/index.html') + '">All venue fact pages →</a>'; }

  // ---------- matching ----------
  // Lower-case, drop apostrophes, "&" -> "and", punctuation -> spaces.
  function norm(s) {
    return ' ' + String(s).toLowerCase().replace(/[’']/g, '').replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim() + ' ';
  }
  // Plural/possessive "s" dropped from longer words ("pdts" -> "pdt").
  function singular(q) { return q.replace(/([a-z]{3,})s(?= )/g, '$1'); }
  function lev(a, b) {
    var m = a.length, n = b.length, d = [], i, j;
    for (i = 0; i <= m; i++) d[i] = [i];
    for (j = 0; j <= n; j++) d[0][j] = j;
    for (i = 1; i <= m; i++) for (j = 1; j <= n; j++)
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    return d[m][n];
  }
  // Names a visitor might type for a venue. "!word" = an everyday word that only
  // counts with a venue cue ("at elsewhere", "is nowadays open") or at the start.
  function namesOf(v) {
    // a venue named with an everyday word ("Elsewhere") is strict under every spelling
    var everyday = v.aliases.some(function (a) { return a.charAt(0) === '!'; });
    var out = [{ s: norm(v.name).trim(), strict: everyday }, { s: v.slug.replace(/-/g, ' '), strict: everyday }];
    v.aliases.forEach(function (a) {
      var strict = a.charAt(0) === '!';
      out.push({ s: norm(strict ? a.slice(1) : a).trim(), strict: strict });
    });
    return out;
  }
  var CUES = ['at', 'to', 'into', 'about', 'is', 'does', 'for', 'in', 'of', 'inside'];
  // Returns { v: venue, said: matched text } or null.
  function findVenue(q) {
    var qs = [norm(q), singular(norm(q))], best = null;
    (VENUES || []).forEach(function (v) {
      namesOf(v).forEach(function (n) {
        if (!n.s) return;
        qs.forEach(function (x) {
          if (x.indexOf(' ' + n.s + ' ') === -1) return;
          if (n.strict && x.indexOf(' ' + n.s + ' ') !== 0 &&
              !CUES.some(function (c) { return x.indexOf(' ' + c + ' ' + n.s + ' ') !== -1; })) return;
          if (!best || n.s.length > best.said.length) best = { v: v, said: n.s };
        });
      });
    });
    if (best) return best;
    // small typos on longer names ("hosue of yes"); short names must be exact
    var words = norm(q).trim().split(' ');
    (VENUES || []).forEach(function (v) {
      namesOf(v).forEach(function (n) {
        if (n.strict || n.s.length < 7) return;
        var k = n.s.split(' ').length;
        for (var i = 0; i + k <= words.length; i++) {
          var w = words.slice(i, i + k).join(' ');
          if (!best && Math.abs(w.length - n.s.length) <= 2 && lev(w, n.s) <= (n.s.length >= 11 ? 2 : 1)) best = { v: v, said: w };
        }
      });
    });
    return best;
  }
  // A word that is close to, but not, a venue name: ask instead of guessing.
  var COMMON = ' tonight people friday saturday sunday monday tuesday thursday rooftop rooftops weekend outside dancing cocktail cocktails parties birthday brooklyn manhattan bachelorette ';
  function nearVenue(q) {
    var words = norm(q).trim().split(' '), hit = null;
    (VENUES || []).forEach(function (v) {
      namesOf(v).forEach(function (n) {
        if (n.strict || n.s.length < 7 || n.s.indexOf(' ') !== -1) return;
        words.forEach(function (w) {
          if (!hit && w.length >= 5 && COMMON.indexOf(' ' + w + ' ') === -1 && Math.abs(w.length - n.s.length) <= 3 && lev(w, n.s) <= 3) hit = v;
        });
      });
    });
    return hit;
  }
  // Neighborhood + borough names, read from the venue data itself.
  var AREA_ALIAS = { les: 'lower east side', fidi: 'financial district', 'times sq': 'times square', bk: 'brooklyn', ues: 'upper east side', uws: 'upper west side', lic: 'long island city', ktown: 'koreatown', bedstuy: 'bed stuy' };
  // asking for the wider area also finds the venues listed under its parts
  var AREA_GROUP = { midtown: ['midtown', 'times square', 'garment district', 'turtle bay', 'beekman'], village: ['village'] };
  var OTHER_AREAS = ['harlem', 'soho', 'bronx', 'staten island', 'astoria', 'upper east side', 'upper west side', 'tribeca', 'bed stuy', 'park slope', 'long island city', 'flushing', 'jackson heights', 'nolita', 'chinatown', 'hudson yards', 'murray hill', 'gramercy', 'kips bay', 'koreatown'];
  function areaKey(a) { return norm(a).trim(); }
  function findArea(q) {
    var t = norm(q);
    Object.keys(AREA_ALIAS).forEach(function (a) { if (t.indexOf(' ' + a + ' ') !== -1) t += AREA_ALIAS[a] + ' '; });
    var areas = {};
    (VENUES || []).forEach(function (v) {
      (v.hood + ' / ' + v.borough).split(/\s*[\/()]\s*/).forEach(function (a) {
        var k = areaKey(a);
        if (k.length > 3 && !/border/.test(k)) areas[k] = a.trim();
      });
    });
    var hit = Object.keys(areas).filter(function (k) { return t.indexOf(' ' + k + ' ') !== -1; })
      .sort(function (a, b) { return b.length - a.length; })[0];
    if (hit) return { key: hit, label: areas[hit] };
    if (/ village /.test(t)) return { key: 'village', label: 'the Village' };
    var other = OTHER_AREAS.filter(function (a) { return t.indexOf(' ' + a + ' ') !== -1; })[0];
    return other ? { key: other, label: title(other), none: true } : null;
  }
  function inArea(area) {
    var keys = area ? AREA_GROUP[area.key] || [area.key] : [];
    return function (v) {
      var a = ' ' + areaKey(v.hood + ' ' + v.borough) + ' ';
      return !area || keys.some(function (k) { return a.indexOf(' ' + k + ' ') !== -1; });
    };
  }

  // ---------- answers ----------
  function flag(v) {
    if (v.status === 'closed') return '<b>Closed.</b> ' + esc(v.status_note) + '<br>';
    if (v.status === 'unclear') return '<b>Heads up:</b> we could not confirm it is operating normally. ' + esc(v.status_note) + '<br>';
    return '';
  }
  function skipList(v) {
    return v.skip.length ? '<b>Skip it if:</b><ul>' + v.skip.map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') + '</ul>' : '<b>Skip it if:</b> nothing flagged yet.';
  }
  function venueCard(v, focus) {
    var rows = [];
    if (focus === 'dress') rows.push('<b>Dress code:</b> ' + esc(v.dress));
    else if (focus === 'age') rows.push('<b>Age &amp; ID:</b> ' + esc(v.age));
    else if (focus === 'hours') rows.push('<b>Hours:</b> ' + esc(v.hours));
    else if (focus === 'howto') rows.push('<b>How to get in:</b> ' + esc(v.howto));
    else if (focus === 'price') rows.push('<b>Drink prices:</b> ' + esc(v.price));
    else if (focus === 'subway') rows.push('<b>Subway:</b> ' + esc(v.subway));
    else if (focus === 'honest') rows.push(skipList(v));
    else if (focus === 'group') { rows.push('<b>How to get in:</b> ' + esc(v.howto)); rows.push(skipList(v)); }
    else rows.push('<b>Cover:</b> ' + esc(v.cover));
    if (!focus) { rows.push('<b>Dress:</b> ' + esc(v.dress)); rows.push('<b>Age:</b> ' + esc(v.age)); }
    return '<b>' + esc(v.name) + '</b> (' + esc(v.hood) + ')<br>' + flag(v) + rows.join('<br>') +
      '<br><a href="' + esc(R(v.url)) + '">Sources &amp; full facts, checked ' + esc(v.verified) + ' →</a>';
  }
  // field: show that fact inline (with its label) so caveats are never hidden.
  function listVenues(filter, heading, field, more) {
    var all = live().filter(filter);
    var max = field ? 6 : 10, hits = all.slice(0, max);
    if (!hits.length) return null;
    return '<b>' + heading + '</b><ul>' + hits.map(function (v) {
      return '<li><a href="' + esc(R(v.url)) + '">' + esc(v.name) + '</a> (' + esc(v.hood) + ')' +
        (v.status === 'unclear' ? ' · <i>status unclear</i>' : '') + (field ? ': ' + esc(v[field]) : '') + '</li>';
    }).join('') + '</ul>' + (all.length > hits.length ? (all.length - hits.length) + ' more. ' : '') + (more || ALL_LINK());
  }
  function listOrNone(filter, heading, field, area, more) {
    var out = listVenues(function (v) { return filter(v) && inArea(area)(v); }, heading + (area ? ' in ' + esc(area.label) : '') + ':', field, more);
    if (out) return out;
    var near = area && listVenues(inArea(area), 'What I have checked in ' + esc(area.label) + ':', null);
    return 'I don’t have a checked venue like that' + (area ? ' in ' + esc(area.label) : '') + ' yet. ' + (near || ALL_LINK());
  }
  function money(n) { return '$' + n; }
  function planLink() {
    var p = PLANS[0];
    return p ? ' Planning for a group? <a href="' + esc(R(p.url)) + '">' + esc(p.title) + ', priced per person →</a>' : '';
  }
  function answerPlan(t) {
    var p = PLANS[0];
    if (!p) return botSay('Browse ' + ALL_LINK());
    var opts = p.options.map(function (o) {
      return '<li>' + esc(o.name) + ': ' + money(o.low) + '–' + money(o.high) + ' per person' +
        (o.label ? ' ' + esc(o.label) : '') + (o.tag ? ' <b>' + esc(o.tag) + '</b>' : '') + '</li>';
    }).join('');
    var n = (t.match(/\b(\d{1,2})\b/) || [])[1];
    var size = n && +n !== p.group ? ' These are priced for ' + p.group + '; with ' + n + ' people the bus and yacht cost more (or less) per head, the cruise doesn’t change.' : '';
    botSay('<b>' + esc(p.title) + '</b>, priced for ' + p.group + ' people:<ul>' + opts + '</ul>' +
      (p.combo ? esc(p.combo.label) + ' together: about ' + money(p.combo.low) + '–' + money(p.combo.high) + ' per person. ' : '') + size +
      ' <a href="' + esc(R(p.url)) + '">Prices, sources &amp; how to book →</a>');
    setChips(['Rooftops', 'Cocktail bars', 'Dress codes', 'No cover']);
  }
  var lastVenue = null;
  function pageVenue() {
    var m = location.pathname.match(/\/venues\/([a-z0-9-]+)\.html/);
    return m ? (VENUES || []).filter(function (v) { return v.slug === m[1]; })[0] || null : null;
  }
  function focusOf(t) {
    if (/subway|train|get there|get to|closest stop|nearest stop|directions|address|where is/.test(t)) return 'subway';
    if (/drinks?\b|cocktails? cost|how much (are|is a) (drink|cocktail|beer)|beer|menu price/.test(t)) return 'price';
    if (/dress|wear|outfit|sneaker|shoes|jeans|attire/.test(t)) return 'dress';
    if (/\bage\b|\b1[5-9]\b|\b2[01]\b|year.?olds?|\bid\b|how old|under ?21|underage|all ages|foreign|passport|international/.test(t)) return 'age';
    if (/cover|price|cost|much|ticket|fee|charge/.test(t)) return 'cover';
    if (/\bhours?\b|\bopen\b|\bclos(e|ed|es|ing)\b|what time|\blate\b|monday|tuesday|wednesday|thursday|friday|saturday|sunday/.test(t)) return 'hours';
    if (/get in|door|entry|line|queue|reserv|book|table|guest ?list|bouncer/.test(t)) return 'howto';
    if (/worth|honest|good\b|review|skip|overrated|any good/.test(t)) return 'honest';
    return null;
  }
  // Category words -> venue tags (several can combine: "clubs with no cover in Brooklyn").
  var TAG_NAME = { rooftop: 'Rooftops', club: 'Clubs', cocktail: 'Cocktail bars', live: 'Live music &amp; shows' };
  function wantTags(t) {
    var w = [];
    if (/rooftop|\bviews?\b|skyline|outdoor/.test(t)) w.push('rooftop');
    if (/live music|jazz|\bband\b|concert|\bshows?\b|cabaret/.test(t)) w.push('live');
    else if (/club|danc|techno|house music|rave|disco/.test(t)) w.push('club');
    else if (!w.length && /speakeasy|cocktail|\bdate\b|romantic|quiet|\bbars?\b|whiskey|drinks/.test(t)) w.push('cocktail');
    if (/free|no cover|without (a )?cover|cheap|budget|broke|\$\d/.test(t)) w.push('no_cover');
    return w;
  }
  function tagHeading(w) {
    var base = w.filter(function (x) { return TAG_NAME[x]; }).map(function (x) { return TAG_NAME[x]; }).join(' &amp; ') || 'Venues';
    return w.indexOf('no_cover') !== -1 ? base + ' with no cover for walk-ins' : base;
  }
  function hasAll(w) { return function (v) { return w.every(function (x) { return has(v, x); }); }; }
  var GROUPW = /bachelorette|bachelor|\bhen\b|\bstag\b|birthday|\bgroup\b|friends|\bcrew\b|celebrat|party of/;
  var PLANW = /bachelorette|bachelor|\bhen\b|\bstag\b|party bus|cruise|yacht|\bboat\b/;

  function handle(q) {
    say(esc(q), 'user');
    input.value = '';
    track('nybot_message');
    var t = q.toLowerCase();

    loadVenues(function (ok) {
      if (!ok) return botSay('I can’t reach the venue list right now. Try again in a moment, or browse ' + ALL_LINK());
      var found = findVenue(t), v = found && found.v;
      // the venue's own name ("Magic Hour") must not decide what is being asked
      var focus = focusOf(found ? norm(t).replace(' ' + found.said + ' ', ' ') : t);
      var tags = wantTags(found ? norm(t).replace(' ' + found.said + ' ', ' ') : t);
      var area = findArea(t);
      var group = GROUPW.test(t);
      if (!v) {
        var near = (focus || group) && !area && !tags.length && nearVenue(t);
        if (near) {
          botSay('Did you mean <b>' + esc(near.name) + '</b>?');
          return setChips(['Cover at ' + near.name, 'Dress code at ' + near.name, 'How to get in at ' + near.name]);
        }
        var general = /\b(codes|venues|places|bars|clubs|spots|rooftops|all|city|best|any|which|where|nyc)\b/.test(t.replace('all ages', ''));
        var here = /\b(here|this|it|there|they|place|spot)\b/.test(t);
        // "what's the cover?" on a venue page, or a follow-up about the venue just discussed
        if ((focus && !general && !area && !tags.length) || (group && here)) v = lastVenue || pageVenue();
      }
      if (v) {
        if (group && !focus) focus = 'group';
        lastVenue = v;
        botSay(venueCard(v, focus) + (focus === 'group' ? '<br>' + planLink() : ''));
        if (v.status === 'closed') return setChips(DEFAULT_CHIPS);
        var n = v.name;
        return setChips(['Dress code at ' + n, 'How to get in at ' + n, 'Hours at ' + n, 'Skip ' + n + '?'].filter(function (c, i) {
          return ['dress', 'howto', 'hours', 'honest'][i] !== focus;
        }).slice(0, 3));
      }
      setChips(DEFAULT_CHIPS);
      // "how much?" on the playbook page means the playbook
      if (/\/plans\//.test(location.pathname) && (focus === 'cover' || focus === 'price' || /how much|split|per person/.test(t)) && !tags.length) return answerPlan(t);
      if (area && area.none) return botSay('I don’t have checked venues in ' + esc(area.label) + ' yet. Everything I’ve checked is here: ' + ALL_LINK());
      var extra = group ? planLink() : '';

      if (/[^\s@]+@[^\s@]+\.[^\s@]{2,}/.test(t)) return botSay('I can’t sign you up for anything. There’s no newsletter right now. To reach a person, use the <a href="' + R('contact.html') + '">contact page</a>.');
      if (/source|how do you (check|know)|accura|verif|up to date|outdated|\bwrong\b|\bstale\b|\bupdated?\b/.test(t)) return botSay('Each fact is checked against the venue’s own site or two independent sources, and shows the date it was checked. Spot something out of date? Tell us on the <a href="' + R('contact.html') + '">contact page</a>. <a href="' + R('how-we-check.html') + '">How we check →</a>');
      if (/tonight|right now|happening|weekend|\bevents?\b|lineup|playing|\bdj\b/.test(t) && !focus) {
        botSay('I don’t track tonight’s lineups. I only know the checked facts about each venue. These sell tickets night by night, and their own pages show who’s playing:');
        return setTimeout(function () { botSay(listOrNone(function (v) { return has(v, 'ticketed') && hasAll(tags)(v); }, 'Ticketed clubs &amp; venues', 'cover', area)); }, 500);
      }
      if (focus === 'age') {
        var idq = /foreign|passport|international|\bid\b/.test(t) && !/\b1[5-9]\b|\b2[01]\b|under|year/.test(t);
        if (idq) return botSay('Bring a physical government photo ID. Several venues here say a non-US ID must be a passport. Each venue’s “Age & ID” line has its exact rule; just ask, e.g. “ID at Elsewhere”.');
        return botSay('Almost every venue here is 21+ at night, so bring a physical ID.<br>' +
          listOrNone(function (v) { return has(v, 'under21') && hasAll(tags)(v); }, 'Where under-21s can get in (read the conditions)', 'age', area));
      }
      if (focus === 'dress') {
        return botSay(listOrNone(function (v) { return has(v, 'dress_rule') && hasAll(tags)(v); }, (tags.length ? tagHeading(tags) + ' with' : 'Venues with') + ' a stated dress rule', 'dress', area,
          'Every venue in one table: <a href="' + R('guides/nyc-dress-codes.html') + '">NYC dress codes →</a>') + extra);
      }
      if (/gay|lgbt|queer|karaoke|comedy|strip|casino|hookah|hotel bar|sports bar|dive bar|wine bar/.test(t)) return botSay('I don’t have checked venues for that yet. Here’s everything I have checked: ' + ALL_LINK());
      if (focus === 'price' || /cheap drinks?|drinks? under|bars? under|cheap bars?/.test(t)) {
        return botSay(listOrNone(function (v) { return (has(v, 'cocktail') || has(v, 'rooftop')) && !/^Not found/.test(v.price) && hasAll(tags.filter(function (x) { return x !== 'no_cover' && x !== 'cocktail'; }))(v); }, 'Drink prices', 'price', area));
      }
      if (/how late|open late|late.?night|after (midnight|[1-5] ?am)|latest|till [2-5]|until [2-5]/.test(t)) {
        return botSay(listOrNone(function (v) { return /\b[2-6](:\d\d)?\s?am\b|4am|late/i.test(v.hours) && hasAll(tags)(v); }, 'Open late (check the hours)', 'hours', area));
      }
      if (tags.length) return botSay(listOrNone(hasAll(tags), tagHeading(tags), tags.indexOf('no_cover') !== -1 ? 'cover' : null, area) + extra);
      if (PLANW.test(t)) return answerPlan(t);
      if (group) {
        botSay('Our group playbook is built for a bachelorette of 10, but the math works for any group night:');
        return setTimeout(function () { answerPlan(t); }, 500);
      }
      if (area) return botSay(listOrNone(function () { return true; }, 'Checked venues', null, area));
      if (focus === 'hours') return botSay('Hours differ a lot by venue and night. Name one and I’ll give you its checked hours, e.g. “hours at Le Bain”.');
      if (focus) return botSay('Which venue? Name one, e.g. “cover at House of Yes”. Or browse ' + ALL_LINK());
      if (/happy hour|food|dinner|\beat\b|restaurant/.test(t)) return botSay('I don’t cover food or happy hours, just door facts: cover, dress code, age and how to get in. ' + ALL_LINK());
      if (/safe|safety|scam|pickpocket/.test(t)) return botSay('Stick to venues’ official ticket links, keep your ID and phone close, and agree a meet-up spot with your group. For each venue I can tell you the cover and how to get in.');
      if (/subscribe|newsletter|email|brief/.test(t)) return botSay('There’s no newsletter right now. Everything I know is on the site: ' + ALL_LINK());
      if (/\b(hi|hello|hey|yo|sup|hiya)\b/.test(t)) return botSay('Hey 🥂 I’m ' + esc(ART.name) + '. Ask me what a venue costs, its dress code, rooftops, no-cover spots, or how to plan a group night. Anything on this site, I know it.');
      if (/thank|thanks|\bty\b|cheers/.test(t)) return botSay('Anytime. Have a great night out, and pace yourself. 😉');
      botSay('I answer from this site’s checked facts. Try a venue name (“cover at House of Yes”), <b>rooftops</b>, <b>no cover</b>, <b>dress codes</b>, a neighborhood like <b>Bushwick</b>, or <b>bachelorette for 10</b>. Or browse ' + ALL_LINK());
    });
  }
  function title(s) { return s.replace(/(^|[\s-])([a-z])/g, function (m, a, c) { return a + c.toUpperCase(); }); }

  // ---------- teaser (speech bubble above Nyla) ----------
  function teaserLine() {
    var p = location.pathname;
    var m = p.match(/\/venues\/([a-z0-9-]+)\.html/);
    if (m && m[1] !== 'index' && document.querySelector('.stamp')) {
      var h1 = document.querySelector('h1');
      var name = h1 ? h1.textContent.split(/[—:]/)[0].trim() : 'this spot';
      return 'psst — want the short version for ' + esc(name) + '? just ask';
    }
    if (/\/venues\//.test(p)) return 'ask me any venue’s cover, dress code, or door rules';
    if (/\/guides\//.test(p)) return 'tell me where you’re going and I’ll tell you what to wear';
    if (/\/plans\//.test(p)) return 'planning for the whole group? I can do the math';
    var pool = [
      'psst — want to know what to wear tonight?',
      'planning a night out? I know every venue on this site',
      'covers, dress codes, door rules — ask me anything'
    ];
    return pool[Math.floor(Math.random() * pool.length)];
  }

  var teaser;
  function teaserGone() {
    if (teaser && teaser.parentNode) teaser.parentNode.removeChild(teaser);
    teaser = null;
    if (bubbleImg) bubbleImg.src = pose(0);
  }
  function showTeaser() {
    if (panel.classList.contains('open') || teaser) return;
    teaser = el('div', 'nyb-teaser',
      '<span class="nyb-teaser-txt">' + teaserLine() + '</span>' +
      '<span class="nyb-teaser-cta">Tap me to ask anything &rarr;</span>');
    teaser.setAttribute('role', 'status');
    teaser.addEventListener('click', function () { open(); });
    document.body.appendChild(teaser);
    if (bubbleImg) bubbleImg.src = pose(1); // she perks up while "talking"
    lsSet('nyb_teased_at', String(Date.now()));
    setTimeout(teaserGone, 20000);
  }

  // ---------- boot ----------
  function open() {
    var hi = panel.querySelector('.nyb-head-ava img');
    if (hi && !hi.getAttribute('src')) hi.src = ART.head;
    panel.classList.add('open');
    bubble.style.display = 'none';
    teaserGone();
    // header keeps the head crop — a full-body render would be unreadable at 44px
    if (!msgs.children.length) {
      botSay('Hey, I’m <b>' + esc(ART.name) + '</b> — the night concierge. Every answer comes from this site’s checked, dated facts. What kind of night are we planning?', 250);
      setChips(DEFAULT_CHIPS);
    }
    track('nybot_open');
    setTimeout(function () { input.focus(); }, 300);
  }
  function close() {
    if (!panel.classList.contains('open')) return;
    panel.classList.remove('open'); bubble.style.display = '';
    bubble.focus();
  }

  function init() {
    document.body.appendChild(bubble);
    document.body.appendChild(panel);
    msgs = panel.querySelector('.nyb-msgs');
    chipsEl = panel.querySelector('.nyb-chips');
    input = panel.querySelector('.nyb-in');
    typing = panel.querySelector('.nyb-typing');
    typing.textContent = ART.name + ' is typing…';
    bubble.addEventListener('click', open);
    panel.querySelector('.nyb-close').addEventListener('click', close);
    panel.querySelector('.nyb-inrow').addEventListener('submit', function (e) {
      e.preventDefault();
      var q = input.value.trim();
      if (q) handle(q);
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

    // speech bubble: 4s delay, re-shows if 45+ minutes since last time
    var last = parseInt(lsGet('nyb_teased_at') || '0', 10);
    if (Date.now() - last > 45 * 60 * 1000) {
      setTimeout(showTeaser, 4000);
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
