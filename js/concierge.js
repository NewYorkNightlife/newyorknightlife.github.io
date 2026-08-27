/* NYBot v3 — the NY Nightlife concierge cast. Rules-based, answers only from site data.
   v2: speech bubble above avatar (4s delay, page-aware lines, re-shows after 45 min), multi-pose avatar.
   v3: per-page mascot routing — neighbourhood pages get their own mascot, everything else gets Nyla. */
(function () {
  'use strict';
  var VENUES = null, FEED = null;

  // ---------- mascot cast ----------
  // Full-body 3D renders, transparent PNG so she stands free on the page.
  // Art lives at /assets/mascots/<slug>.png (full body) + <slug>-head.png (256² crop).
  // Nyla is the default and the ONLY cast member whose files are guaranteed to
  // exist — her two originals predate the mascots folder, so she doubles as the
  // fallback for every mascot whose PNGs have not been produced yet.
  var DEFAULT_SLUG = 'nyla';
  function mascot(slug, name) {
    return { name: name, body: '/assets/mascots/' + slug + '.png', head: '/assets/mascots/' + slug + '-head.png' };
  }
  var MASCOTS = {
    'nyla':              { name: 'Nyla', body: '/assets/nyla-full-welcome.png', head: '/assets/nyla-head.png' },
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
  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function track(n) { try { if (window.gtag) gtag('event', n, { event_category: 'nybot', event_label: window.__nybMascot }); } catch (e) {} }
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
      '<div class="nyb-head-ava"><img src="' + ART.head + '" alt="" onerror="this.parentNode.innerHTML=window.__nybSvg"></div>' +
      '<div><div class="nyb-head-name">' + esc(ART.name) + '</div><div class="nyb-head-sub"><span class="nyb-dot"></span>NYC night concierge</div></div>' +
      '<button class="nyb-close" aria-label="Close chat">&times;</button>' +
    '</div>' +
    '<div class="nyb-msgs" aria-live="polite"></div>' +
    '<div class="nyb-typing">' + esc(ART.name) + ' is typing…</div>' +
    '<div class="nyb-chips"></div>' +
    '<form class="nyb-inrow"><input class="nyb-in" type="text" placeholder="Ask about tonight, a venue, covers…" aria-label="Message" /><button class="nyb-send" type="submit">Ask</button></form>';
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
  var DEFAULT_CHIPS = ["What's on tonight?", 'Cover charges', 'Rooftops', 'Free & cheap', 'This weekend'];

  // ---------- data ----------
  function loadVenues(cb) {
    if (VENUES) return cb();
    fetch('/data/venues.json').then(function (r) { return r.json(); }).then(function (d) { VENUES = d.venues || []; cb(); }).catch(function () { VENUES = []; cb(); });
  }
  function loadFeed(cb) {
    if (FEED) return cb();
    fetch('/data/tonight-feed.json', { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (d) { FEED = d; cb(); }).catch(function () { FEED = null; cb(); });
  }

  // ---------- intents ----------
  function venueCard(v, focus) {
    var rows = [];
    if (focus === 'dress') rows.push('<b>Dress code:</b> ' + esc(v.dress));
    else if (focus === 'age') rows.push('<b>Age policy:</b> ' + esc(v.age));
    else if (focus === 'hours') rows.push('<b>Nights &amp; hours:</b> ' + esc(v.hours));
    else if (focus === 'howto') rows.push('<b>How to get in:</b> ' + esc(v.howto));
    else if (focus === 'honest') rows.push('<b>Honest take:</b> ' + esc(v.honest));
    else rows.push('<b>Cover:</b> ' + esc(v.cover));
    if (!focus) { rows.push('<b>Dress:</b> ' + esc(v.dress)); rows.push('<b>Age:</b> ' + esc(v.age)); }
    return '<b>' + esc(v.name) + '</b> (' + esc(v.hood) + ')<br>' + rows.join('<br>') +
      '<br><a href="' + v.url + '">Full facts — verified ' + esc(v.verified) + ' →</a>';
  }
  function findVenue(q) {
    q = q.toLowerCase();
    var best = null;
    (VENUES || []).forEach(function (v) {
      var n = v.name.toLowerCase();
      if (q.indexOf(n) !== -1 || q.indexOf(v.slug.replace(/-/g, ' ')) !== -1) { best = v; return; }
      var words = n.split(/[^a-z0-9]+/).filter(function (w) { return w.length > 3; });
      var hits = words.filter(function (w) { return q.indexOf(w) !== -1; }).length;
      if (words.length && hits >= Math.max(1, words.length - 1) && (!best || hits > best._h)) { v._h = hits; best = v; }
    });
    return best;
  }
  function listVenues(filter, title, empty) {
    var hits = (VENUES || []).filter(filter).slice(0, 6);
    if (!hits.length) return empty || 'Nothing matched — browse <a href="/venues/">all venue facts</a>.';
    return '<b>' + title + '</b><ul>' + hits.map(function (v) {
      return '<li><a href="' + v.url + '">' + esc(v.name) + '</a> — ' + esc((v.cover || '').split('.')[0]).slice(0, 70) + '</li>';
    }).join('') + '</ul><a href="/venues/">All 30 venue fact pages →</a>';
  }

  function answerTonight() {
    loadFeed(function () {
      if (!FEED) return botSay('The live feed is napping — check <a href="/tonight/">Tonight</a> directly.');
      var w = FEED.weather || {};
      var head = (w.summary ? esc((w.icon || '') + ' ' + w.summary + (w.temp_f != null ? ', ' + w.temp_f + '°F' : '')) + '. ' : '');
      var picks = (FEED.picks_from_sources || []).filter(function (p) {
        var t = ((p.title || '') + ' ' + (p.venue || '')).toLowerCase();
        var cat = String(p.category || '').toLowerCase();
        return (p.url || p.source_url) && cat !== 'theater' && !/theatre|theater/.test(t);
      }).slice(0, 3);
      var list = picks.length ? '<ul>' + picks.map(function (p) {
        return '<li><a href="' + esc(p.url || p.source_url) + '" target="_blank" rel="noopener">' + esc(p.title) + '</a>' + (p.venue ? ' — ' + esc(p.venue) : '') + '</li>';
      }).join('') + '</ul>' : '';
      botSay(head + 'Here’s what’s real tonight:' + list + '<a href="/tonight/">Full tonight feed →</a>');
      setChips(['Free & cheap', 'Rooftops', 'This weekend', 'Cover charges']);
    });
  }

  var exchanges = 0, offeredMail = false;
  function maybeOfferMail() {
    exchanges++;
    if (exchanges === 3 && !offeredMail && !lsGet('nyb_subscribed')) {
      offeredMail = true;
      setTimeout(function () {
        botSay('By the way — I send the best of the weekend (with real prices) every Thursday. Type your email if you want it. No spam, promise.');
      }, 1800);
    }
  }
  function trySubscribe(q) {
    var m = q.match(/[^\s@]+@[^\s@]+\.[^\s@]{2,}/);
    if (!m) return false;
    fetch('https://formsubmit.co/ajax/a650e221f3f7706184623e4558d53fdd', {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ email: m[0], source: 'nybot:' + location.pathname })
    }).then(function () {
      lsSet('nyb_subscribed', '1');
      botSay('Done — you’re on the list. First brief lands Thursday. 🥂');
      track('nybot_subscribe');
    }).catch(function () { botSay('Hmm, that didn’t go through — try the form in the footer.'); });
    return true;
  }

  function handle(q) {
    say(esc(q), 'user');
    input.value = '';
    track('nybot_message');
    var t = q.toLowerCase();
    maybeOfferMail();

    if (trySubscribe(q)) return;

    loadVenues(function () {
      var v = findVenue(t);
      var focus = /dress|wear|outfit/.test(t) ? 'dress' : /age|18|21|id\b|old/.test(t) ? 'age' : /hour|open|close|when/.test(t) ? 'hours' : /get in|door|entry|line|queue/.test(t) ? 'howto' : /worth|honest|good\?|review/.test(t) ? 'honest' : (/cover|price|cost|much/.test(t) ? '' : null);
      if (v) return botSay(venueCard(v, focus === null ? '' : focus));

      if (/tonight|now|happening/.test(t)) return answerTonight();
      if (/weekend|saturday|friday|sunday/.test(t)) return botSay('The weekend page has real events with real prices, refreshed every Thursday: <a href="/weekend/nyc-nightlife-this-weekend.html">NYC nightlife this weekend →</a>');
      if (/free|cheap|broke|budget under|\$20/.test(t)) return botSay(listVenues(function (v) { return /no cover|free/i.test(v.cover); }, 'No-cover spots (verified):'));
      if (/rooftop|view|skyline/.test(t)) return botSay(listVenues(function (v) { return /rooftop|penthouse/i.test(v.type + ' ' + v.name); }, 'Rooftops with verified facts:'));
      if (/speakeasy|cocktail|date|romantic/.test(t)) return botSay(listVenues(function (v) { return /speakeasy|cocktail/i.test(v.type); }, 'Cocktail dens &amp; speakeasies:'));
      if (/club|dance|techno|house music|dj|rave/.test(t)) return botSay(listVenues(function (v) { return /club/i.test(v.type) && !/cocktail/i.test(v.type); }, 'Real dance floors:'));
      if (/budget|cost|spend|money|price/.test(t)) return botSay('Rough NYC math: lean night $60–$120, balanced $120–$250, premium $250+. Price your exact night with the <a href="/tools/budget-planner.html">Budget Planner →</a>');
      if (/bushwick|williamsburg|ridgewood|greenpoint|manhattan|brooklyn|queens|village|midtown|chelsea|harlem|les|lower east/.test(t)) return botSay('Neighborhood first is the right instinct. Browse the <a href="/neighborhoods/">neighborhood guides</a> — each lists its verified venues, prices, and late-night logistics.');
      if (/subscribe|newsletter|email|brief/.test(t)) return botSay('Drop your email right here in the chat and I’ll add you to the Thursday brief.');
      if (/hi|hello|hey|yo\b|sup/.test(t)) return botSay('Hey 🥂 I’m ' + esc(ART.name) + '. Ask me what’s on tonight, what a venue costs, dress codes, rooftops — anything on this site, I know it.');
      if (/thank|thanks|ty\b/.test(t)) return botSay('Anytime. Have a great night out — and pace yourself. 😉');
      botSay('I answer from this site’s verified data — try a venue name ("cover at House of Yes"), <b>tonight</b>, <b>rooftops</b>, <b>free &amp; cheap</b>, or <b>this weekend</b>. Or browse <a href="/venues/">all venue facts</a>.');
    });
  }

  // ---------- teaser (speech bubble above Nyla) ----------
  function teaserLine() {
    var p = location.pathname;
    var m = p.match(/^\/venues\/([a-z0-9-]+)\.html/);
    if (m && m[1] !== 'index') {
      var h1 = document.querySelector('h1');
      var name = h1 ? h1.textContent.split('—')[0].trim() : 'this spot';
      return 'psst — I know the door secrets for ' + esc(name) + '. wanna hear?';
    }
    if (p.indexOf('/venues') === 0) return 'ask me any venue’s cover, dress code, or door odds';
    if (p.indexOf('/weekend') === 0) return 'want my weekend shortlist? real prices only';
    if (p.indexOf('/tonight') === 0) return 'I can tell you what’s actually good tonight';
    if (p.indexOf('/tools') === 0) return 'need help doing the math on tonight?';
    if (p.indexOf('/blog') === 0) return 'want the short version? just ask me';
    if (p.indexOf('/neighborhoods') === 0) return 'I know every one of these blocks after dark 😉';
    var pool = [
      'psst — want to know what’s actually good tonight?',
      'planning a night out? I know all 30 venues cold',
      'covers, dress codes, door odds — ask me anything'
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
    panel.classList.add('open');
    bubble.style.display = 'none';
    teaserGone();
    // header keeps the head crop — a full-body render would be unreadable at 44px
    if (!msgs.children.length) {
      botSay('Hey, I’m <b>' + esc(ART.name) + '</b> — the night concierge. Every answer comes from this site’s verified, dated facts. What kind of night are we planning?', 250);
      setChips(DEFAULT_CHIPS);
    }
    track('nybot_open');
    setTimeout(function () { input.focus(); }, 300);
  }
  function close() { panel.classList.remove('open'); bubble.style.display = ''; }

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
