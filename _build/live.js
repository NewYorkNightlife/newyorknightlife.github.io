/* NY Nightlife "tonight" data: open tonight (from checked weekly hours), NWS weather,
   nightlife headlines and new liquor licenses. Fills #tonight-box (home) and #tonight (Tonight page).
   Data comes from /data/venues.json (build) and the live-data branch (scheduled job, see _build/live.py).
   Everything from outside is inserted as text, never as HTML. */
(function () {
  'use strict';
  var SRC = (document.currentScript && document.currentScript.src) || '';
  var ROOT = /js\/live\.js/.test(SRC) ? SRC.replace(/js\/live\.js.*$/, '') : '/';
  function R(p) { return ROOT + String(p).replace(/^\//, ''); }
  var box = document.getElementById('tonight-box'), full = document.getElementById('tonight');
  if (!box && !full) return;

  var DAYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
  var DAYNAME = { sun: 'Sunday', mon: 'Monday', tue: 'Tuesday', wed: 'Wednesday', thu: 'Thursday', fri: 'Friday', sat: 'Saturday' };
  var HOURS_LABEL = { likely: 'hours: 1 source', unconfirmed: 'hours unconfirmed' };

  function get(p) { return fetch(R(p), { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw r.status; return r.json(); }).catch(function () { return null; }); }
  // The scheduled job publishes to the repo's live-data branch (main only takes pull requests);
  // if GitHub's raw file host fails, use the copy that ships with the site.
  var LIVE = 'https://raw.githubusercontent.com/NewYorkNightlife/newyorknightlife.github.io/live-data/data/live/';
  function getLive(name) {
    return fetch(LIVE + name, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw r.status; return r.json(); })
      .catch(function () { return get('data/live/' + name); });
  }
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function link(href, text, ext) {
    var a = el('a', null, text); a.href = href;
    if (ext) { a.rel = 'noopener'; a.target = '_blank'; }
    return a;
  }
  function safeExt(u) { return /^https:\/\/[a-z0-9.-]+\//i.test(u || '') ? u : null; }

  // New York wall-clock time, whatever the visitor's own timezone.
  function nyNow() {
    var parts = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', weekday: 'short', hour: 'numeric', minute: 'numeric', hour12: false })
      .formatToParts(new Date()).reduce(function (o, p) { o[p.type] = p.value; return o; }, {});
    var h = parseInt(parts.hour, 10) % 24, m = parseInt(parts.minute, 10);
    return { day: parts.weekday.toLowerCase().slice(0, 3), mins: h * 60 + m };
  }
  // Before 6am counts as last night ("tonight" for someone still out at 2am).
  function nightOf(now) {
    if (now.mins < 360) return { day: DAYS[(DAYS.indexOf(now.day) + 6) % 7], mins: now.mins + 1440 };
    return now;
  }
  function toMins(t) { var a = t.split(':'); return parseInt(a[0], 10) * 60 + parseInt(a[1], 10); }
  function fmt(mins) {
    var h = Math.floor(mins / 60) % 24, m = mins % 60, ap = h < 12 ? 'am' : 'pm';
    var hh = h % 12 === 0 ? 12 : h % 12;
    if (h === 0 && m === 0) return 'midnight';
    return hh + (m ? ':' + (m < 10 ? '0' : '') + m : '') + ap;
  }

  function openTonight(venues) {
    var n = nightOf(nyNow()), open = [], events = [];
    venues.forEach(function (v) {
      if (v.status === 'closed') return;
      if (v.hours_kind === 'event') { events.push(v); return; }
      var span = (v.week || {})[n.day];
      if (!span) return;
      var p = span.split('-'), from = toMins(p[0]), late = p[1] === 'late', to = late ? 26 * 60 : toMins(p[1]);
      if (n.mins >= to) return;            // already closed for the night ('late' counts as 2am)
      open.push({ v: v, from: from, to: to, late: late, now: n.mins >= from });
    });
    open.sort(function (a, b) { return b.to - a.to; });
    return { day: n.day, open: open, events: events };
  }

  function venueRow(o) {
    var li = el('li');
    li.appendChild(link(R(o.v.url), o.v.name));
    var bits = ' (' + o.v.hood + ') · ' + (o.now ? 'open' : 'opens ' + fmt(o.from)) + ' till ' + (o.late ? 'late' : fmt(o.to));
    li.appendChild(document.createTextNode(bits));
    if (HOURS_LABEL[o.v.hours_status]) li.appendChild(el('span', 'chip', HOURS_LABEL[o.v.hours_status]));
    if (o.v.status === 'unclear') li.appendChild(el('span', 'chip', 'status unclear'));
    if (o.v.hours_note) li.appendChild(el('span', 'small', ' · ' + o.v.hours_note));
    return li;
  }

  function weatherLine(w) {
    if (!w || !w.issued || !w.end) return null;
    var issued = new Date(w.issued), end = new Date(w.end), now = new Date();
    if (isNaN(issued) || now - issued > 12 * 3600 * 1000 || now > end) return null;   // never show a stale forecast
    var p = el('p', 'weather');
    var t = (w.period || 'Tonight') + ': low ' + Math.round(w.temp_f) + '°F, ' + (w.short || '').toLowerCase();
    if (w.rain_pct != null) t += ', ' + w.rain_pct + '% chance of rain';
    if (w.wind) t += ', wind ' + w.wind;
    p.appendChild(el('b', null, t + '.'));
    var when = issued.toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour: 'numeric', minute: '2-digit' });
    p.appendChild(el('span', 'small', ' Forecast: National Weather Service (weather.gov), issued ' + when + '.'));
    if (w.rain_pct != null && w.rain_pct >= 50) p.appendChild(el('span', 'small tip', ' Our tip: rooftops can close their terraces in rain, so check before you go.'));
    return p;
  }

  function day(iso) {
    var d = new Date(String(iso).slice(0, 10) + 'T12:00:00Z');
    return isNaN(d) ? String(iso) : d.toLocaleDateString('en-US', { timeZone: 'UTC', month: 'short', day: 'numeric' });
  }
  function section(parent, title) { var s = el('section', 'live-sec'); s.appendChild(el('h2', null, title)); parent.appendChild(s); return s; }

  function renderNews(parent, news, venues) {
    var cutoff = new Date(Date.now() - 14 * 864e5).toISOString().slice(0, 10);
    var items = ((news && news.items) || []).filter(function (i) { return String(i.date) >= cutoff; });
    if (!items.length) return;                       // nothing recent: no section at all
    var s = section(parent, 'Recent nightlife headlines');
    s.appendChild(el('p', 'small', 'From other publishers, matched by keyword. Not checked by us.'));
    var bySlugName = {}; venues.forEach(function (v) { bySlugName[v.name.replace(/\s*\(.*?\)/, '')] = v; });
    var ul = el('ul', 'clean news');
    items.slice(0, 12).forEach(function (i) {
      var u = safeExt(i.url); if (!u) return;
      var li = el('li'); li.appendChild(el('span', 'small', day(i.date) + ' · ')); li.appendChild(link(u, i.title, true));
      li.appendChild(el('span', 'small', ' · ' + i.source));
      (i.venues || []).forEach(function (n) {
        var v = bySlugName[n]; if (!v) return;
        var t = el('span', 'small', ' · Mentions '); t.appendChild(link(R(v.url), v.name)); li.appendChild(t);
      });
      ul.appendChild(li);
    });
    s.appendChild(ul);
  }

  function renderLicenses(parent, lic) {
    var s = section(parent, 'New liquor licenses (not openings)');
    var items = (lic && lic.items) || [];
    s.appendChild(el('p', 'small', 'On-premises licenses first issued in the last 5 weeks in Manhattan, Brooklyn and Queens. ' +
      'A new license can mean a new bar or restaurant, or a new owner at an existing one. Mostly restaurants.'));
    if (!items.length) { s.appendChild(el('p', null, 'No new licenses in the latest data.')); return; }
    var counts = {}; items.forEach(function (i) { counts[i.borough] = (counts[i.borough] || 0) + 1; });
    s.appendChild(el('p', null, Object.keys(counts).map(function (b) { return b + ': ' + counts[b]; }).join(' · ')));
    var ul = el('ul', 'clean lic');
    items.slice(0, 15).forEach(function (i) {
      var li = el('li'); li.appendChild(el('b', null, i.name));
      li.appendChild(document.createTextNode(' · ' + i.type + ' · ' + [i.address, i.borough, i.zip].filter(Boolean).join(', ') + ' · issued ' + day(i.issued)));
      ul.appendChild(li);
    });
    s.appendChild(ul);
    var src = el('p', 'small', 'Source: '); var u = safeExt(lic.source_url);
    if (u) src.appendChild(link(u, 'NYS Liquor Authority via data.ny.gov', true)); else src.appendChild(document.createTextNode('NYS Liquor Authority via data.ny.gov'));
    src.appendChild(document.createTextNode('. Errors? Tell us on the contact page.'));
    s.appendChild(src);
  }

  Promise.all([get('data/venues.json'), getLive('weather.json'), getLive('news.json'), getLive('licenses.json'), getLive('status.json')])
    .then(function (r) {
      var venues = (r[0] && r[0].venues) || [];
      if (!venues.length) return;
      var t = openTonight(venues), w = weatherLine(r[1]);
      if (box) {
        box.textContent = '';
        box.appendChild(el('h2', null, 'Tonight in NYC'));
        if (w) box.appendChild(w);
        var ul = el('ul', 'clean tonight-list');
        t.open.slice(0, 5).forEach(function (o) { ul.appendChild(venueRow(o)); });
        if (t.open.length) { box.appendChild(el('p', null, 'Latest open tonight (' + DAYNAME[t.day] + '), from our checked hours:')); box.appendChild(ul); }
        box.appendChild(link(R('tonight/'), 'Everything open tonight, headlines and new licenses →'));
      }
      if (full) {
        full.textContent = '';
        if (w) full.appendChild(w);
        var s = section(full, 'Open tonight (' + DAYNAME[t.day] + ')');
        s.appendChild(el('p', 'small', 'From each venue\'s checked weekly hours, latest closing first. Hours change for holidays and events, so check before you go.'));
        var ul2 = el('ul', 'clean tonight-list');
        t.open.forEach(function (o) { ul2.appendChild(venueRow(o)); });
        if (t.open.length) s.appendChild(ul2); else s.appendChild(el('p', null, 'None of our checked venues list hours for the rest of tonight.'));
        if (t.events.length) {
          var ev = el('p', null, 'Event nights only, check their listings: ');
          t.events.forEach(function (v, i) {
            if (i) ev.appendChild(document.createTextNode(', '));
            ev.appendChild(link(R(v.url), v.name));
            if (v.status === 'unclear') ev.appendChild(el('span', 'chip', 'status unclear'));
          });
          s.appendChild(ev);
        }
        renderNews(full, r[2], venues);
        renderLicenses(full, r[3]);
        var upd = r[4] && r[4].checked;
        if (upd) full.appendChild(el('p', 'small', 'Forecast, headlines and licenses last checked ' +
          new Date(upd).toLocaleString('en-US', { timeZone: 'America/New_York', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) + ' (New York time).'));
      }
    });
})();
