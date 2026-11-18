/* Re-slice the week snapshot for the visitor's New York night.

The HTML is the no-JS fallback for the night of the build. This script does not
trust that clock. America/New_York comes from Intl. The night is 5pm to 5am;
from midnight until 5am it is still the previous evening. Events that have
already ended (real end, or three hours after the start) are hidden.

The route line stays the 5pm-to-4am Night Signal. js/signal.js lights the stop
from the same New York clock. "Updated" stays the feed's own timestamp.
*/
(function () {
  'use strict';
  var section = document.querySelector('[data-night-events]');
  if (!section) return;
  var SRC = (document.currentScript && document.currentScript.src) || '';
  var ROOT = /js\/tonight\.js/.test(SRC) ? SRC.replace(/js\/tonight\.js.*$/, '') : '/';
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var LONG = { Sun: 'Sunday', Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday' };
  var MARK = { music: 'M', comedy: 'C', club: 'K', nightlife: 'N', theatre: 'A', parks: 'P', festival: 'F', tour: 'T', cruise: 'B' };
  var LABEL = { music: 'Music', comedy: 'Comedy', club: 'Dance', nightlife: 'Nightlife', theatre: 'Theatre', parks: 'Parks', festival: 'Festival', tour: 'Tour', cruise: 'Cruise' };
  var THREE_H = 3 * 60 * 60 * 1000;

  function R(p) { return ROOT + String(p || '').replace(/^\//, ''); }
  function get(url) {
    return fetch(R(url), { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error('bad');
      return r.json();
    }).catch(function () { return null; });
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function clear(node) {
    while (node.children && node.children.length) node.removeChild(node.children[0]);
  }
  function nyParts(date) {
    var fmt = new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      weekday: 'short', hourCycle: 'h23'
    });
    var o = {};
    fmt.formatToParts(date).forEach(function (p) { if (p.type !== 'literal') o[p.type] = p.value; });
    var hour = parseInt(o.hour, 10);
    if (hour === 24) hour = 0;
    o.hour = String(hour);
    o.weekday = String(o.weekday || '').replace(/\./g, '');
    return o;
  }
  function nyOffset(ms) {
    var p = nyParts(new Date(ms));
    var asUTC = Date.UTC(+p.year, +p.month - 1, +p.day, parseInt(p.hour, 10) % 24, +p.minute, +p.second);
    return asUTC - ms;
  }
  function nyInstant(y, m, d, hh, mm) {
    var utc = Date.UTC(y, m - 1, d, hh, mm, 0);
    var guess = utc - nyOffset(utc);
    return new Date(utc - nyOffset(guess));
  }
  function nightBounds(now) {
    var p = nyParts(now);
    var y = +p.year, m = +p.month, d = +p.day;
    if ((parseInt(p.hour, 10) % 24) < 5) {
      var prev = nyParts(new Date(nyInstant(y, m, d, 12, 0).getTime() - 24 * 60 * 60 * 1000));
      y = +prev.year; m = +prev.month; d = +prev.day;
    }
    var begin = nyInstant(y, m, d, 17, 0);
    return { begin: begin, end: new Date(begin.getTime() + 12 * 60 * 60 * 1000) };
  }
  function factsFrom(begin) {
    var p = nyParts(begin);
    return {
      short: p.weekday,
      long: LONG[p.weekday] || p.weekday,
      mon: MONTHS[+p.month - 1] || '',
      day: parseInt(p.day, 10),
      iso: p.year + '-' + p.month + '-' + p.day
    };
  }
  function eventEnd(ev) {
    var start = new Date(ev.start);
    if (isNaN(start.getTime())) return null;
    if (ev.end) {
      var end = new Date(ev.end);
      if (!isNaN(end.getTime())) return end;
    }
    return new Date(start.getTime() + THREE_H);
  }
  function ended(ev, now) {
    var end = eventEnd(ev);
    return !end || end.getTime() <= now.getTime();
  }
  function partition(events, now) {
    var bounds = nightBounds(now);
    var tonight = [], upcoming = [], earlier = [];
    (events || []).forEach(function (ev) {
      if (!ev || !ev.start) return;
      var start = new Date(ev.start);
      if (isNaN(start.getTime()) || ended(ev, now)) return;
      if (start >= bounds.begin && start < bounds.end) tonight.push(ev);
      else if (start >= bounds.end) upcoming.push(ev);
      else earlier.push(ev);
    });
    function byStart(a, b) { return new Date(a.start) - new Date(b.start); }
    tonight.sort(byStart);
    upcoming.sort(byStart);
    earlier.sort(byStart);
    return { bounds: bounds, tonight: tonight, week: upcoming.concat(earlier) };
  }
  function heroLine(facts, tonightN, weekN, lateN) {
    var bits = [facts.short + ' ' + facts.iso];
    bits.push(tonightN ? (tonightN + ' tonight') : 'Nothing listed tonight');
    if (weekN) bits.push(weekN + ' this week');
    if (lateN) bits.push(lateN + ' open past midnight');
    return bits.join(' · ');
  }
  function homeShort(nVenues, tonightN, lateN, facts) {
    var base = 'Tonight in New York, this site lists ' + nVenues + ' checked bars and clubs and the public events we could pull for this week. ';
    var mid;
    if (tonightN && lateN) {
      mid = tonightN + " of those events fall in tonight's 5pm to 5am window, and " + lateN + ' venues list hours past midnight on ' + facts.long + '. ';
    } else if (tonightN) {
      mid = tonightN + " of those events fall in tonight's 5pm to 5am window. ";
    } else {
      mid = "None of those events start in tonight's 5pm to 5am window. The next listings are below, with the venues that stay open past midnight" + (lateN ? (' on ' + facts.long) : '') + '. ';
    }
    return base + mid + 'Dress code, age, and cover stay on each venue page with the date we checked them.';
  }
  function tonightShort(facts, tonightN, moreN) {
    var phrase = facts.long + ' ' + facts.mon + ' ' + facts.day;
    var lead;
    if (tonightN && moreN) {
      lead = 'On ' + phrase + ', the feeds we checked list ' + tonightN + ' events between 5pm and 5am New York time, and ' + moreN + ' more through the coming week. ';
    } else if (tonightN) {
      lead = 'On ' + phrase + ', the feeds we checked list ' + tonightN + ' events between 5pm and 5am New York time. ';
    } else {
      lead = 'On ' + phrase + ', no listing in the feeds starts between 5pm and 5am New York time and is still ahead. The next events are below, with the venues that list hours past midnight. ';
    }
    return lead + "Below that, the open-now list uses each venue's checked weekly hours. Bar service in the city still stops at 4am under state law. A missing listing means the feed did not include it, not that the night is empty.";
  }
  function refreshStamp(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    var p = nyParts(d);
    var hour = parseInt(p.hour, 10) % 24;
    var ap = hour < 12 ? 'am' : 'pm';
    var h12 = hour % 12 || 12;
    return p.year + '-' + p.month + '-' + p.day + ' ' + h12 + ':' + p.minute + ap + ' ET';
  }
  function whenLabel(date) {
    var p = nyParts(date);
    var hour = parseInt(p.hour, 10) % 24;
    var min = parseInt(p.minute, 10) || 0;
    var ap = hour < 12 ? 'am' : 'pm';
    var h12 = hour % 12 || 12;
    var day = parseInt(p.day, 10);
    return p.weekday + ' ' + (MONTHS[+p.month - 1] || '') + ' ' + day + ' · ' + h12 + (min ? ':' + (min < 10 ? '0' : '') + min : '') + ap;
  }
  function safeHref(url) {
    if (!url) return R('tonight/');
    if (url.charAt(0) === '/' && url.charAt(1) !== '/') return R(url);
    if (/^https:\/\/[a-z0-9.-]+(\/|$)/i.test(url)) return url;
    return R('tonight/');
  }
  function safeImage(ev) {
    var local = ev.image_local || '';
    if (local.charAt(0) === '/' && local.indexOf('//') !== 0 && local.indexOf('\\') < 0) return R(local);
    var remote = ev.image_url || '';
    if (!/^https:\/\//i.test(remote)) return '';
    var host = '';
    try { host = new URL(remote).hostname.toLowerCase(); } catch (err) { return ''; }
    if (host === 'ticketm.net' || host.slice(-11) === '.ticketm.net' || host === 'ticketmaster.com' || host.slice(-16) === '.ticketmaster.com' || host === 'nycgovparks.org' || host.slice(-16) === '.nycgovparks.org') return remote;
    return '';
  }
  function initial(name) {
    var s = String(name || '').replace(/^(the|a|an)\s+/i, '');
    for (var i = 0; i < s.length; i++) if (/[a-z0-9]/i.test(s.charAt(i))) return s.charAt(i).toUpperCase();
    return 'N';
  }
  function eventCard(ev) {
    var cat = ev.category || 'parks';
    var a = el('a', 'pcard');
    a.setAttribute('data-cat', cat);
    a.href = safeHref(ev.url);
    if (/^https:\/\//i.test(a.href)) { a.rel = 'noopener'; a.target = '_blank'; }
    var media = el('span', 'pcard-media cat-' + cat);
    var src = safeImage(ev);
    if (src) {
      var img = el('img');
      img.src = src;
      img.alt = (ev.title || 'Event') + (ev.venue_name ? ' at ' + ev.venue_name : '');
      img.width = ev.image_w || 640;
      img.height = ev.image_h || 360;
      img.setAttribute('loading', 'lazy');
      img.setAttribute('decoding', 'async');
      media.appendChild(img);
    } else {
      media.appendChild(el('span', 'mark', MARK[cat] || 'P'));
    }
    var body = el('span', 'pcard-body');
    var start = new Date(ev.start);
    var kicker = [LABEL[cat] || 'Event'];
    if (!isNaN(start.getTime())) kicker.push(whenLabel(start));
    body.appendChild(el('span', 'kicker', kicker.filter(Boolean).join(' · ')));
    body.appendChild(el('span', 't', ev.title || 'Event'));
    var where = [ev.venue_name, ev.borough].filter(Boolean).join(' · ');
    if (where) body.appendChild(el('span', 'm', where));
    if (ev.price_min != null && isFinite(+ev.price_min)) {
      var price = +ev.price_min;
      var width = Math.max(4, Math.min(100, price / 150 * 100));
      var bar = el('span', 'pbar');
      bar.setAttribute('role', 'img');
      bar.setAttribute('aria-label', 'from $' + Math.round(price) + ' on a $0 to $150 scale');
      var tick = el('i');
      tick.style.width = width.toFixed(1) + '%';
      bar.appendChild(tick);
      body.appendChild(bar);
      body.appendChild(el('span', 'price', 'from $' + Math.round(price)));
    } else if (ev.source === 'nyc_parks') {
      body.appendChild(el('span', 'price', 'NYC Parks listing'));
    }
    if (ev.source === 'ticketmaster') body.appendChild(el('span', 'price', 'Tickets via Ticketmaster'));
    a.appendChild(media);
    a.appendChild(body);
    return a;
  }
  function tlabel(hm) {
    if (hm === 'late') return 'late';
    var bits = String(hm || '0:0').split(':');
    var h = parseInt(bits[0], 10);
    var m = parseInt(bits[1], 10) || 0;
    if (isNaN(h)) return '';
    h %= 24;
    if (h === 0 && m === 0) return 'midnight';
    var ap = h < 12 ? 'am' : 'pm';
    var hh = h % 12 === 0 ? 12 : h % 12;
    return hh + (m ? ':' + (m < 10 ? '0' : '') + m : '') + ap;
  }
  function spanText(span) {
    var parts = String(span).split('-');
    return tlabel(parts[0]) + '–' + tlabel(parts[1]);
  }
  function closeMins(span) {
    var b = String(span).split('-')[1];
    if (b === 'late') return 9999;
    var bits = String(b || '').split(':');
    return parseInt(bits[0], 10) * 60 + (parseInt(bits[1], 10) || 0);
  }
  function lateVenues(doc, begin) {
    var day = String(nyParts(begin).weekday || '').toLowerCase().slice(0, 3);
    var out = [];
    ((doc && doc.venues) || []).forEach(function (v) {
      if (!v || v.status === 'closed' || v.hours_kind === 'event') return;
      var span = v.week && v.week[day];
      if (!span) return;
      var mins = closeMins(span);
      if (mins >= 24 * 60) out.push({ v: v, mins: mins, span: span });
    });
    out.sort(function (a, b) {
      return b.mins - a.mins || String(a.v.name || '').localeCompare(String(b.v.name || ''));
    });
    return out;
  }
  function venueCard(row) {
    var v = row.v;
    var a = el('a', 'pcard');
    a.setAttribute('data-cat', 'nightlife');
    a.href = safeHref(v.url ? ('/' + String(v.url).replace(/^\//, '')) : ('/venues/' + v.slug + '.html'));
    var media = el('span', 'pcard-media cat-nightlife');
    media.appendChild(el('span', 'mark', initial(v.name)));
    var body = el('span', 'pcard-body');
    body.appendChild(el('span', 'kicker', 'Open past midnight'));
    body.appendChild(el('span', 't', v.name || 'Venue'));
    var where = [v.hood || v.neighborhood, spanText(row.span)].filter(Boolean).join(' · ');
    if (where) body.appendChild(el('span', 'm', where));
    a.appendChild(media);
    a.appendChild(body);
    return a;
  }
  function grid(nodes) {
    var d = el('div', 'pcards');
    nodes.forEach(function (n) { d.appendChild(n); });
    return d;
  }
  function fillEvents(node, heading, note, rows, emptyText) {
    clear(node);
    node.appendChild(el('h2', null, heading));
    if (!rows.length) {
      node.appendChild(el('p', null, emptyText));
      node.appendChild(el('p', 'small', note));
      return;
    }
    node.appendChild(el('p', 'small', note));
    node.appendChild(grid(rows.map(eventCard)));
  }
  function fillEmpty(node, nextRows, venues, note) {
    clear(node);
    node.appendChild(el('h2', null, 'Tonight'));
    node.appendChild(el('p', null, 'Nothing in the 5pm–5am window is still ahead in the latest feed.'));
    node.appendChild(el('p', 'small', note));
    if (nextRows.length) {
      node.appendChild(el('h2', 'as-h3', 'Next up'));
      node.appendChild(grid(nextRows.map(eventCard)));
    }
    if (venues.length) {
      node.appendChild(el('h2', 'as-h3', 'Open past midnight'));
      node.appendChild(grid(venues.slice(0, 8).map(venueCard)));
    }
  }
  function feedNote(iso, home) {
    var day = String(iso || '').slice(0, 10) || 'the last build';
    if (home) {
      return 'NYC Parks events and permitted street festivals are from NYC Open Data. Music, comedy, theatre, and nightlife are added from Ticketmaster when that key is set. Ticketmaster images sit only beside that event, and the link is the event page. Feed checked ' + day + '.';
    }
    return 'Listings come from NYC Open Data (Parks events and permitted street festivals) and, when a key is configured, Ticketmaster Discovery for music, comedy, theatre, and nightlife. Ticketmaster links are the event URL, with no affiliate tag. Images from Ticketmaster are loaded beside that event only. Feed checked ' + day + '.';
  }
  function bareZero(text) {
    return /(^|[^\d])0 (events|tonight|of those)\b/.test(text) || /\b(list|lists) 0\b/.test(text);
  }
  function apply(feed, venuesDoc) {
    var now = new Date();
    var part = partition(feed.events || [], now);
    var facts = factsFrom(part.bounds.begin);
    var late = lateVenues(venuesDoc, part.bounds.begin);
    var active = part.tonight.length + part.week.length;
    var line = heroLine(facts, part.tonight.length, active, late.length);
    var lineNode = document.querySelector('[data-night-line]');
    if (lineNode && !bareZero(line)) lineNode.textContent = line;
    var summary = document.querySelector('[data-night-summary]');
    var kind = summary ? summary.getAttribute('data-night-summary') : '';
    var home = (section.getAttribute('data-night-page') || kind) !== 'tonight';
    var note = feedNote(feed.fetched_at, home);
    if (summary && summary.children && summary.children.length) {
      var nVenues = venuesDoc ? 0 : parseInt(summary.getAttribute('data-checked') || '', 10);
      if (venuesDoc) ((venuesDoc.venues) || []).forEach(function (v) { if (v && v.status !== 'closed') nVenues++; });
      if (!venuesDoc) nVenues = parseInt(summary.getAttribute('data-checked') || '', 10);
      var text = '';
      if (kind === 'tonight') text = tonightShort(facts, part.tonight.length, part.week.length);
      else if (nVenues) text = homeShort(nVenues, part.tonight.length, late.length, facts);
      if (text && !bareZero(text)) summary.children[summary.children.length - 1].textContent = text;
    }
    var stamp = document.querySelector('[data-feed-updated]');
    var refresh = refreshStamp(feed.fetched_at);
    if (stamp && refresh) stamp.textContent = 'Updated ' + refresh;
    var weekNote = 'The next listings after tonight, from the same feeds.';
    var weekSection = document.querySelector('[data-week-events]');
    if (home) {
      if (part.tonight.length) {
        fillEvents(section, "What's on in NYC tonight / this week", note, part.tonight.concat(part.week).slice(0, 6), 'No evening parks, festival, or ticketed listings are in the latest feed.');
      } else {
        fillEmpty(section, part.week.slice(0, 6), late, note);
      }
    } else if (part.tonight.length) {
      fillEvents(section, 'Tonight', note, part.tonight.slice(0, 24), 'Nothing in the 5pm–5am window is still ahead in the latest feed.');
      if (weekSection) fillEvents(weekSection, 'This week', weekNote, part.week.slice(0, 24), 'No later listings in this feed.');
    } else {
      fillEmpty(section, part.week.slice(0, 6), late, note);
      if (weekSection) fillEvents(weekSection, 'Later this week', weekNote, part.week.slice(6, 30), 'No later listings in this feed.');
    }
  }

  var eventsUrl = section.getAttribute('data-events') || '/data/events.json';
  var venuesUrl = section.getAttribute('data-venues') || '/data/venues.json';
  Promise.all([get(eventsUrl), get(venuesUrl)]).then(function (pair) {
    if (!pair[0] || !pair[0].events) return;
    apply(pair[0], pair[1]);
  });
})();
