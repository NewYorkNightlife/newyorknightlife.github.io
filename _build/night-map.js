/* Night map. Loaded after the section nears the viewport.
   Pins come from the JSON in the page. Tonight's route comes from
   /data/events.json, and only when an event names a plotted venue.
   No tile library. Reduced motion skips the pulse and the dash. */
(function () {
  'use strict';
  var root = document.getElementById('night-map');
  if (!root || root.getAttribute('data-ready')) return;
  root.setAttribute('data-ready', '1');

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var proj = (root.getAttribute('data-proj') || '').split(',');
  var W = +proj[0], H = +proj[1];
  var minLng = +proj[2], minLat = +proj[3], maxLng = +proj[4], maxLat = +proj[5], lat0 = +proj[6];
  var stage = root.querySelector('.night-map-stage');
  var canvas = root.querySelector('[data-canvas]');
  var pinLayer = root.querySelector('[data-pins]');
  var card = root.querySelector('[data-card]');
  var empty = root.querySelector('[data-empty]');
  var pins = [];
  try {
    pins = JSON.parse(document.getElementById('night-map-pins').textContent || '[]');
  } catch (err) {
    pins = [];
  }
  var svg = null;
  var baseView = null;
  var view = null;
  var activeBoro = 'all';
  var tonight = {};
  var openKey = '';
  var laid = '';

  function cos(n) { return Math.cos(n * Math.PI / 180); }
  function project(lat, lng) {
    var spanX = (maxLng - minLng) * cos(lat0);
    var spanY = maxLat - minLat;
    return {
      vx: (lng - minLng) * cos(lat0) / spanX * W,
      vy: (maxLat - lat) / spanY * H
    };
  }
  function norm(value) {
    return String(value || '').toLowerCase().replace(/&amp;/g, ' and ').replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '');
  }
  function nyParts(date) {
    var fmt = new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
    });
    var o = {};
    fmt.formatToParts(date).forEach(function (p) { if (p.type !== 'literal') o[p.type] = p.value; });
    var hour = parseInt(o.hour, 10);
    if (hour === 24) hour = 0;
    o.hour = hour;
    return o;
  }
  function nyOffset(ms) {
    var p = nyParts(new Date(ms));
    var asUTC = Date.UTC(+p.year, +p.month - 1, +p.day, p.hour, +p.minute, +p.second);
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
    if (p.hour < 5) {
      var prev = nyParts(new Date(nyInstant(y, m, d, 12, 0).getTime() - 86400000));
      y = +prev.year; m = +prev.month; d = +prev.day;
    }
    var begin = nyInstant(y, m, d, 17, 0);
    return { begin: begin, end: new Date(begin.getTime() + 12 * 3600000) };
  }
  function eventEnd(ev) {
    var start = new Date(ev.start);
    if (isNaN(start.getTime())) return null;
    if (ev.end) {
      var end = new Date(ev.end);
      if (!isNaN(end.getTime())) return end;
    }
    return new Date(start.getTime() + 3 * 3600000);
  }
  function bySlug(slug) {
    for (var i = 0; i < pins.length; i++) if (pins[i].slug === slug) return pins[i];
    return null;
  }
  function byName(name) {
    var key = norm(name);
    if (!key) return null;
    for (var i = 0; i < pins.length; i++) if (norm(pins[i].name) === key) return pins[i];
    return null;
  }
  function photoSrc(venue) {
    return /^\/img\/[a-z0-9-]+-thumb\.webp$/.test(venue.photo || '') ? venue.photo : '';
  }

  function fitAspect(x, y, w, h) {
    var aspect = W / H;
    var cx = x + w / 2, cy = y + h / 2;
    if (w / h < aspect) w = h * aspect;
    else h = w / aspect;
    return { x: cx - w / 2, y: cy - h / 2, w: w, h: h };
  }
  function setView(box) {
    view = box;
    svg.setAttribute('viewBox', box.x + ' ' + box.y + ' ' + box.w + ' ' + box.h);
  }
  function boroughBox(slug) {
    var path = svg.querySelector('[data-boro="' + slug + '"]');
    if (!path || !path.getBBox) return baseView;
    var b = path.getBBox();
    var pad = Math.max(b.width, b.height) * 0.08;
    return fitAspect(b.x - pad, b.y - pad, b.width + pad * 2, b.height + pad * 2);
  }
  function paintBoroughs() {
    var paths = svg.querySelectorAll('.night-map-land path');
    for (var i = 0; i < paths.length; i++) {
      paths[i].classList.toggle('is-dim', activeBoro !== 'all' && paths[i].getAttribute('data-boro') !== activeBoro);
      paths[i].classList.toggle('is-on', activeBoro !== 'all' && paths[i].getAttribute('data-boro') === activeBoro);
    }
    var labels = root.querySelectorAll('.night-map-label, .boro-switch button');
    for (var j = 0; j < labels.length; j++) {
      var boro = labels[j].getAttribute('data-boro');
      var on = boro === activeBoro || (boro === 'all' && activeBoro === 'all');
      labels[j].setAttribute('aria-pressed', on ? 'true' : 'false');
    }
  }
  function showBorough(slug) {
    activeBoro = slug || 'all';
    closeCard();
    if (!svg) return;
    setView(activeBoro === 'all' ? baseView : boroughBox(activeBoro));
    paintBoroughs();
    layout();
  }

  function screenPoint(vx, vy) {
    var pt = svg.createSVGPoint();
    pt.x = vx;
    pt.y = vy;
    var ctm = svg.getScreenCTM();
    if (!ctm) return null;
    var sp = pt.matrixTransform(ctm);
    var box = stage.getBoundingClientRect();
    return { x: sp.x - box.left, y: sp.y - box.top };
  }
  function visible(venue) {
    if (activeBoro === 'all') return true;
    return norm(venue.borough) === norm(activeBoro);
  }
  function cluster(items) {
    var groups = [];
    var order = items.slice().sort(function (a, b) {
      return a.sy - b.sy || a.sx - b.sx || (a.slug < b.slug ? -1 : 1);
    });
    order.forEach(function (item) {
      var best = null;
      var bestD = 22;
      groups.forEach(function (group) {
        var d = Math.hypot(item.sx - group.x, item.sy - group.y);
        if (d < bestD) { best = group; bestD = d; }
      });
      if (!best) {
        groups.push({ x: item.sx, y: item.sy, items: [item] });
        return;
      }
      var next = best.items.concat([item]);
      var cx = 0, cy = 0;
      next.forEach(function (entry) { cx += entry.sx; cy += entry.sy; });
      cx /= next.length;
      cy /= next.length;
      var radius = 0;
      next.forEach(function (entry) {
        radius = Math.max(radius, Math.hypot(entry.sx - cx, entry.sy - cy));
      });
      // Keep a cluster geographically tight. A downtown pile may still share
      // one light; rooms a neighborhood apart stay separate.
      if (radius > 26) {
        groups.push({ x: item.sx, y: item.sy, items: [item] });
        return;
      }
      best.items = next;
      best.x = cx;
      best.y = cy;
    });
    return groups;
  }
  function groupSpan(group) {
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    group.items.forEach(function (item) {
      minX = Math.min(minX, item.vx); maxX = Math.max(maxX, item.vx);
      minY = Math.min(minY, item.vy); maxY = Math.max(maxY, item.vy);
    });
    return { x: minX, y: minY, w: Math.max(8, maxX - minX), h: Math.max(8, maxY - minY) };
  }
  function zoomToGroup(group) {
    var b = groupSpan(group);
    var pad = Math.max(36, b.w * 0.45, b.h * 0.45);
    closeCard();
    setView(fitAspect(b.x - pad, b.y - pad, b.w + pad * 2, b.h + pad * 2));
    laid = '';
    layout();
  }
  function groupKey(group) {
    return group.items.map(function (item) { return item.slug; }).sort().join('+');
  }

  function closeCard(restore) {
    openKey = '';
    card.hidden = true;
    card.textContent = '';
    if (restore && restore.focus) restore.focus();
  }
  function rowLink(venue) {
    var link = document.createElement('a');
    link.href = venue.url;
    var img = document.createElement('img');
    var src = photoSrc(venue);
    img.alt = '';
    img.width = 176;
    img.height = 176;
    img.decoding = 'async';
    if (!src) return null;
    img.src = src;
    img.addEventListener('error', function () {
      if (img.getAttribute('data-tried')) {
        var dead = img.closest('a');
        if (dead) dead.remove();
        if (!card.querySelector('a')) closeCard();
        return;
      }
      img.setAttribute('data-tried', '1');
      img.src = src.replace(/-thumb\.webp$/, '-thumb.jpg');
    });
    var text = document.createElement('span');
    text.className = 'nmap-copy';
    var name = document.createElement('strong');
    name.textContent = venue.name;
    var hood = document.createElement('em');
    hood.textContent = venue.hood || venue.borough || '';
    text.appendChild(name);
    text.appendChild(hood);
    link.appendChild(img);
    link.appendChild(text);
    return link;
  }
  function openCard(group, from) {
    var key = groupKey(group);
    if (openKey === key && !card.hidden && card.querySelector('a')) return;
    var venues = group.items.map(function (item) { return item.venue; }).filter(photoSrc);
    if (!venues.length) return;
    openKey = key;
    card.hidden = false;
    card.textContent = '';
    card.classList.toggle('is-stack', venues.length > 1);
    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'nmap-close';
    close.setAttribute('aria-label', 'Close');
    close.textContent = 'Close';
    close.addEventListener('click', function () { closeCard(from); });
    venues.forEach(function (venue) {
      var link = rowLink(venue);
      if (link) card.appendChild(link);
    });
    if (!card.querySelector('a')) {
      closeCard();
      return;
    }
    card.appendChild(close);
    card.setAttribute('aria-label', venues.length === 1 ? venues[0].name : venues.length + ' rooms');
  }

  function layout() {
    if (!svg) return;
    var placed = [];
    pins.forEach(function (venue) {
      if (!visible(venue)) return;
      var p = project(venue.lat, venue.lng);
      var s = screenPoint(p.vx, p.vy);
      if (!s) return;
      placed.push({ slug: venue.slug, venue: venue, sx: s.x, sy: s.y, vx: p.vx, vy: p.vy });
    });
    var groups = cluster(placed);
    groups.sort(function (a, b) {
      var ak = groupKey(a), bk = groupKey(b);
      return ak < bk ? -1 : ak > bk ? 1 : 0;
    });
    var sig = activeBoro + '|' + groups.map(groupKey).join('|');
    var focusSlug = document.activeElement && document.activeElement.getAttribute
      ? document.activeElement.getAttribute('data-slug') : '';
    if (sig !== laid) {
      laid = sig;
      pinLayer.textContent = '';
      groups.forEach(function (group, index) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'nmap-pin';
        var live = group.items.some(function (item) { return tonight[item.slug]; });
        if (live) btn.classList.add('is-live');
        if (group.items.length > 1) btn.classList.add('is-cluster');
        btn.style.left = group.x + 'px';
        btn.style.top = group.y + 'px';
        var names = group.items.map(function (item) { return item.venue.name; });
        var label = names.length === 1
          ? names[0] + (group.items[0].venue.hood ? ', ' + group.items[0].venue.hood : '')
          : names.length + ' rooms: ' + names.join(', ');
        btn.setAttribute('aria-label', label);
        btn.setAttribute('data-slug', group.items[0].slug);
        btn.setAttribute('data-key', groupKey(group));
        var dot = document.createElement('i');
        dot.setAttribute('aria-hidden', 'true');
        if (!reduce) dot.style.animationDelay = (index * 0.17) + 's';
        btn.appendChild(dot);
        if (group.items.length > 1) {
          var count = document.createElement('b');
          count.textContent = String(group.items.length);
          btn.appendChild(count);
        }
        btn.addEventListener('click', function (event) {
          var spread = groupSpan(group);
          if (group.items.length > 1 && (spread.w > 28 || spread.h > 28)) {
            zoomToGroup(group);
            return;
          }
          openCard(group, btn);
          if (event.detail === 0) {
            var link = card.querySelector('a');
            if (link) link.focus();
          }
        });
        btn.addEventListener('focus', function () {
          var spread = groupSpan(group);
          if (group.items.length > 1 && (spread.w > 28 || spread.h > 28)) return;
          openCard(group, btn);
        });
        pinLayer.appendChild(btn);
      });
      if (focusSlug) {
        var again = pinLayer.querySelector('[data-slug="' + focusSlug + '"]');
        if (again) again.focus();
      }
    } else {
      var buttons = pinLayer.querySelectorAll('.nmap-pin');
      groups.forEach(function (group, index) {
        if (!buttons[index]) return;
        buttons[index].style.left = group.x + 'px';
        buttons[index].style.top = group.y + 'px';
      });
    }
    var shown = placed.length;
    empty.hidden = shown !== 0;
    if (!shown) {
      var nice = {
        manhattan: 'Manhattan', brooklyn: 'Brooklyn', queens: 'Queens',
        bronx: 'the Bronx', 'staten-island': 'Staten Island'
      };
      empty.textContent = 'No checked room in ' + (nice[activeBoro] || 'this view') + '.';
    }
    drawRoute(placed);
  }

  function drawRoute(placed) {
    var route = svg.querySelector('#night-route');
    var glow = svg.querySelector('#night-route-glow');
    if (!route) return;
    var stops = [];
    placed.forEach(function (item) {
      if (!tonight[item.slug]) return;
      if (stops.some(function (stop) { return stop.slug === item.slug; })) return;
      stops.push(item);
    });
    stops.sort(function (a, b) { return (tonight[a.slug] || 0) - (tonight[b.slug] || 0); });
    if (stops.length < 2) {
      route.setAttribute('d', '');
      if (glow) glow.setAttribute('d', '');
      return;
    }
    var d = stops.map(function (stop, i) {
      return (i ? 'L' : 'M') + stop.vx.toFixed(1) + ' ' + stop.vy.toFixed(1);
    }).join('');
    route.setAttribute('d', d);
    if (glow) glow.setAttribute('d', d);
  }

  function applyTonight(events) {
    var now = new Date();
    var bounds = nightBounds(now);
    var rows = (events || []).filter(function (ev) {
      if (!ev || !ev.start) return false;
      var start = new Date(ev.start);
      if (isNaN(start.getTime())) return false;
      if (start < bounds.begin || start >= bounds.end) return false;
      var end = eventEnd(ev);
      return end && end > now;
    }).sort(function (a, b) { return String(a.start).localeCompare(String(b.start)); });
    tonight = {};
    rows.forEach(function (ev, index) {
      var venue = (ev.venue_slug && bySlug(ev.venue_slug)) || byName(ev.venue_name);
      if (!venue || tonight[venue.slug]) return;
      tonight[venue.slug] = index + 1;
    });
    laid = '';
    layout();
  }

  function loadEvents() {
    var host = document.querySelector('[data-night-events]');
    var url = host ? host.getAttribute('data-events') : '/data/events.json';
    fetch(url || '/data/events.json', { cache: 'no-cache' }).then(function (res) {
      if (!res.ok) throw new Error('events');
      return res.json();
    }).then(function (data) {
      applyTonight((data && data.events) || []);
    }).catch(function () { applyTonight([]); });
  }

  function bindFilters() {
    var buttons = root.querySelectorAll('.boro-switch button, .night-map-label');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener('click', function (event) {
        var slug = event.currentTarget.getAttribute('data-boro');
        showBorough(slug);
      });
    }
    root.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        var current = pinLayer.querySelector('[data-key="' + openKey + '"]');
        closeCard(current);
      }
    });
  }

  function boot(text) {
    canvas.innerHTML = text;
    svg = canvas.querySelector('svg');
    if (!svg) return;
    var box = (svg.getAttribute('viewBox') || '0 0 800 811').split(/\s+/).map(Number);
    baseView = { x: box[0], y: box[1], w: box[2], h: box[3] };
    view = baseView;
    bindFilters();
    if (window.matchMedia('(min-width: 900px)').matches) {
      var list = root.querySelector('.night-map-list');
      if (list) list.open = true;
    }
    layout();
    loadEvents();
    if ('ResizeObserver' in window) {
      var ro = new ResizeObserver(function () { laid = ''; layout(); });
      ro.observe(stage);
    } else {
      window.addEventListener('resize', function () { laid = ''; layout(); });
    }
  }

  var svgUrl = root.getAttribute('data-svg');
  fetch(svgUrl).then(function (res) {
    if (!res.ok) throw new Error('svg');
    return res.text();
  }).then(boot).catch(function () {
    empty.hidden = false;
    empty.textContent = 'The map did not load. The room list below still works.';
  });
})();
