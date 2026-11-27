/* Night map. Loaded after the section nears the viewport.
   Pins come from the JSON in the page. Tonight's route comes from
   /data/events.json, and only when an event names a plotted venue.
   The camera is the SVG viewBox (1x to 6x). Pins and borough labels are
   HTML in screen space, so they stay sharp and the same size as you zoom.
   One finger and a plain wheel still scroll the page. */
(function () {
  'use strict';
  var root = document.getElementById('night-map');
  if (!root || root.getAttribute('data-ready')) return;
  root.setAttribute('data-ready', '1');

  var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  var reduce = motionQuery.matches;
  if (motionQuery.addEventListener) {
    motionQuery.addEventListener('change', function () { reduce = motionQuery.matches; });
  }
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
  var animId = 0;
  var goal = null;
  var suppressClick = false;
  var swallowClick = false;
  var skipOpenOnFocus = false;
  var closedAt = 0;
  var MIN_ZOOM = 1;
  var MAX_ZOOM = 6;
  var mac = (navigator.userAgentData && navigator.userAgentData.platform === 'macOS')
    || /Mac|iPhone|iPad/.test(navigator.userAgent || '');
  var wheelHint = mac ? 'Use \u2318 + scroll to zoom the map' : 'Use Ctrl + scroll to zoom the map';
  var touchHint = 'Use two fingers to move the map';

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
  function clampView(box) {
    var aspect = baseView.w / baseView.h;
    var w = box.w;
    var h = box.h;
    if (!(w > 0) || !(h > 0)) {
      return { x: baseView.x, y: baseView.y, w: baseView.w, h: baseView.h };
    }
    var cx = box.x + w / 2;
    var cy = box.y + h / 2;
    if (Math.abs(w / h - aspect) > 0.001) {
      if (w / h < aspect) w = h * aspect;
      else h = w / aspect;
    }
    var minW = baseView.w / MAX_ZOOM;
    var maxW = baseView.w / MIN_ZOOM;
    if (w < minW) { w = minW; h = w / aspect; }
    if (w > maxW) { w = maxW; h = w / aspect; }
    var x = cx - w / 2;
    var y = cy - h / 2;
    var minX = baseView.x;
    var maxX = baseView.x + baseView.w - w;
    var minY = baseView.y;
    var maxY = baseView.y + baseView.h - h;
    if (x < minX) x = minX;
    if (x > maxX) x = maxX;
    if (y < minY) y = minY;
    if (y > maxY) y = maxY;
    return { x: x, y: y, w: w, h: h };
  }
  function cancelAnim() {
    if (animId) { cancelAnimationFrame(animId); animId = 0; }
  }
  function setView(box) {
    view = clampView(box);
    if (!svg) return;
    svg.setAttribute('viewBox', view.x + ' ' + view.y + ' ' + view.w + ' ' + view.h);
  }
  function zoomLevel() {
    var box = goal || view;
    return baseView && box ? baseView.w / box.w : 1;
  }
  function syncZoom() {
    var z = zoomLevel();
    var inn = root.querySelector('[data-zoom="in"]');
    var out = root.querySelector('[data-zoom="out"]');
    if (inn) inn.disabled = z >= MAX_ZOOM - 0.02;
    if (out) out.disabled = z <= MIN_ZOOM + 0.02;
  }
  function animateTo(target) {
    target = clampView(fitAspect(target.x, target.y, target.w, target.h));
    goal = target;
    cancelAnim();
    syncZoom();
    if (reduce || !window.requestAnimationFrame) {
      goal = null;
      setView(target);
      layout();
      syncZoom();
      return;
    }
    var from = { x: view.x, y: view.y, w: view.w, h: view.h };
    var t0 = performance.now();
    function step(now) {
      var t = Math.min(1, (now - t0) / 420);
      var e = 1 - Math.pow(1 - t, 3);
      var w = from.w + (target.w - from.w) * e;
      var h = from.h + (target.h - from.h) * e;
      var cx = from.x + from.w / 2 + ((target.x + target.w / 2) - (from.x + from.w / 2)) * e;
      var cy = from.y + from.h / 2 + ((target.y + target.h / 2) - (from.y + from.h / 2)) * e;
      setView({ x: cx - w / 2, y: cy - h / 2, w: w, h: h });
      layout();
      if (t < 1) animId = requestAnimationFrame(step);
      else { animId = 0; goal = null; syncZoom(); }
    }
    animId = requestAnimationFrame(step);
  }
  function zoomAbout(factor, sx, sy, animate) {
    var rect = stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    var basis = (animate && goal) ? goal : view;
    var fx = sx / rect.width;
    var fy = sy / rect.height;
    var w = basis.w / factor;
    var h = basis.h / factor;
    var vx = basis.x + fx * basis.w;
    var vy = basis.y + fy * basis.h;
    var next = { x: vx - fx * w, y: vy - fy * h, w: w, h: h };
    if (animate) animateTo(next);
    else {
      cancelAnim();
      goal = null;
      setView(next);
      layout();
      syncZoom();
    }
  }
  function panBy(dx, dy) {
    cancelAnim();
    goal = null;
    var rect = stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    setView({
      x: view.x - dx / rect.width * view.w,
      y: view.y - dy / rect.height * view.h,
      w: view.w,
      h: view.h
    });
    layout();
    syncZoom();
  }
  function panFrom(origin, dx, dy) {
    cancelAnim();
    goal = null;
    var rect = stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    setView({
      x: origin.x - dx / rect.width * origin.w,
      y: origin.y - dy / rect.height * origin.h,
      w: origin.w,
      h: origin.h
    });
    layout();
  }
  function homeBox() {
    return activeBoro === 'all' || !svg ? baseView : boroughBox(activeBoro);
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
    paintBoroughs();
    animateTo(activeBoro === 'all' ? baseView : boroughBox(activeBoro));
  }

  function screenPoint(vx, vy) {
    var box = stage.getBoundingClientRect();
    if (!box.width || !box.height || !view) return null;
    return {
      x: (vx - view.x) / view.w * box.width,
      y: (vy - view.y) / view.h * box.height
    };
  }
  function rememberLabels() {
    var labels = root.querySelectorAll('.night-map-label');
    for (var i = 0; i < labels.length; i++) {
      var el = labels[i];
      if (el._vx != null) continue;
      if (el.hasAttribute('data-vx')) {
        el._vx = +el.getAttribute('data-vx');
        el._vy = +el.getAttribute('data-vy');
        continue;
      }
      el._vx = baseView.x + (parseFloat(el.style.left) / 100) * baseView.w;
      el._vy = baseView.y + (parseFloat(el.style.top) / 100) * baseView.h;
    }
  }
  function placeLabels() {
    var labels = root.querySelectorAll('.night-map-label');
    for (var i = 0; i < labels.length; i++) {
      var el = labels[i];
      if (el._vx == null) continue;
      var s = screenPoint(el._vx, el._vy);
      if (!s) return;
      el.style.left = s.x + 'px';
      el.style.top = s.y + 'px';
    }
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
    laid = '';
    animateTo(fitAspect(b.x - pad, b.y - pad, b.w + pad * 2, b.h + pad * 2));
  }
  function groupKey(group) {
    return group.items.map(function (item) { return item.slug; }).sort().join('+');
  }

  function closeCard(restore) {
    openKey = '';
    card.hidden = true;
    card.textContent = '';
    closedAt = Date.now();
    var target = restore && restore.isConnected && restore.focus ? restore : stage;
    if (!target || !target.focus) return;
    skipOpenOnFocus = true;
    try { target.focus(); } catch (err) { /* the control may already be gone */ }
    setTimeout(function () { skipOpenOnFocus = false; }, 400);
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
    var press = null;
    function shut(event) {
      event.preventDefault();
      event.stopPropagation();
      closeCard(from);
    }
    close.addEventListener('pointerdown', function (event) {
      press = { id: event.pointerId, x: event.clientX, y: event.clientY };
    });
    close.addEventListener('pointerup', function (event) {
      if (!press || event.pointerId !== press.id) return;
      var moved = Math.hypot(event.clientX - press.x, event.clientY - press.y);
      press = null;
      if (moved > 10) return;
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      swallowClick = true;
      shut(event);
    });
    close.addEventListener('click', shut);
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
          if (swallowClick || Date.now() - closedAt < 400) return;
          var spread = groupSpan(group);
          if (group.items.length > 1 && (spread.w > 28 || spread.h > 28) && zoomLevel() < MAX_ZOOM - 0.05) {
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
          if (skipOpenOnFocus || Date.now() - closedAt < 400) return;
          var spread = groupSpan(group);
          if (group.items.length > 1 && (spread.w > 28 || spread.h > 28) && zoomLevel() < MAX_ZOOM - 0.05) return;
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
    placeLabels();
    drawRoute(placed);
    syncZoom();
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

  function isControl(target) {
    return !!(target && target.closest && target.closest('button, a, input, textarea, select'));
  }
  function onCard(target) {
    return !!(target && target.closest && target.closest('.night-map-card'));
  }
  function showHint(text) {
    var hint = root.querySelector('[data-hint]');
    if (!hint) return;
    hint.textContent = text;
    hint.hidden = false;
    if (hint._t) clearTimeout(hint._t);
    hint._t = setTimeout(function () { hint.hidden = true; }, 1500);
  }
  function armClickGuard() {
    suppressClick = true;
    setTimeout(function () { suppressClick = false; }, 400);
  }
  function bindGestures() {
    var mouse = null;
    var pinch = null;
    var touchStart = null;
    var lastTap = 0;
    var lastTapX = 0;
    var lastTapY = 0;
    var sawTouch = 0;
    var pinchMoved = false;

    stage.addEventListener('click', function (event) {
      if (swallowClick) {
        event.preventDefault();
        event.stopPropagation();
        swallowClick = false;
        return;
      }
      if (onCard(event.target)) return;
      if (suppressClick) {
        event.preventDefault();
        event.stopPropagation();
        suppressClick = false;
        return;
      }
      if (!card.hidden && !isControl(event.target)) closeCard(stage);
    }, true);

    stage.addEventListener('pointerdown', function (event) {
      if (event.pointerType !== 'mouse' || event.button !== 0) return;
      if (onCard(event.target) || isControl(event.target)) return;
      mouse = {
        id: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        origin: { x: view.x, y: view.y, w: view.w, h: view.h },
        moved: false
      };
    });
    stage.addEventListener('pointermove', function (event) {
      if (!mouse || event.pointerId !== mouse.id) return;
      var dx = event.clientX - mouse.x;
      var dy = event.clientY - mouse.y;
      if (!mouse.moved && Math.hypot(dx, dy) < 4) return;
      if (!mouse.moved) {
        mouse.moved = true;
        cancelAnim();
        stage.classList.add('is-panning');
        if (stage.setPointerCapture) {
          try { stage.setPointerCapture(event.pointerId); } catch (err) { /* already released */ }
        }
      }
      event.preventDefault();
      panFrom(mouse.origin, dx, dy);
    });
    function endMouse(event) {
      if (!mouse || (event && event.pointerId !== mouse.id)) return;
      var moved = mouse.moved;
      mouse = null;
      stage.classList.remove('is-panning');
      if (moved) armClickGuard();
      syncZoom();
    }
    stage.addEventListener('pointerup', endMouse);
    stage.addEventListener('pointercancel', endMouse);

    stage.addEventListener('touchstart', function (event) {
      if (onCard(event.target)) return;
      sawTouch = Date.now();
      if (event.touches.length >= 2) event.preventDefault();
      if (event.touches.length === 1) {
        touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY, hinted: false };
        pinch = null;
      }
      if (event.touches.length >= 2) {
        var a = event.touches[0];
        var b = event.touches[1];
        pinch = {
          cx: (a.clientX + b.clientX) / 2,
          cy: (a.clientY + b.clientY) / 2,
          dist: Math.max(12, Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)),
          origin: { x: view.x, y: view.y, w: view.w, h: view.h },
          moved: false
        };
        pinchMoved = false;
        touchStart = null;
        cancelAnim();
      }
    }, { passive: false });
    stage.addEventListener('touchmove', function (event) {
      if (onCard(event.target) && !pinch) return;
      if (event.touches.length >= 2 && pinch) {
        event.preventDefault();
        var a = event.touches[0];
        var b = event.touches[1];
        var cx = (a.clientX + b.clientX) / 2;
        var cy = (a.clientY + b.clientY) / 2;
        var dist = Math.max(12, Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY));
        var rect = stage.getBoundingClientRect();
        var factor = dist / pinch.dist;
        var dx = cx - pinch.cx;
        var dy = cy - pinch.cy;
        if (Math.hypot(dx, dy) > 3 || Math.abs(factor - 1) > 0.01) {
          pinch.moved = true;
          pinchMoved = true;
        }
        var fx = (pinch.cx - rect.left) / rect.width;
        var fy = (pinch.cy - rect.top) / rect.height;
        var w = pinch.origin.w / factor;
        var h = pinch.origin.h / factor;
        var vx = pinch.origin.x + fx * pinch.origin.w;
        var vy = pinch.origin.y + fy * pinch.origin.h;
        setView({
          x: vx - fx * w - dx / rect.width * w,
          y: vy - fy * h - dy / rect.height * h,
          w: w,
          h: h
        });
        layout();
        return;
      }
      if (event.touches.length === 1 && touchStart && !touchStart.hinted) {
        var moved = Math.hypot(event.touches[0].clientX - touchStart.x, event.touches[0].clientY - touchStart.y);
        if (moved > 12) {
          touchStart.hinted = true;
          showHint(touchHint);
          armClickGuard();
        }
      }
    }, { passive: false });
    stage.addEventListener('touchend', function (event) {
      if (event.touches.length >= 2) return;
      if (event.touches.length === 1) {
        pinch = null;
        return;
      }
      var pinched = pinchMoved;
      pinch = null;
      pinchMoved = false;
      if (pinched) {
        armClickGuard();
        syncZoom();
        return;
      }
      if (onCard(event.target) || isControl(event.target)) return;
      var t = event.changedTouches && event.changedTouches[0];
      if (!t) return;
      var now = Date.now();
      if (now - lastTap < 280 && Math.hypot(t.clientX - lastTapX, t.clientY - lastTapY) < 28) {
        lastTap = 0;
        var rect = stage.getBoundingClientRect();
        zoomAbout(2, t.clientX - rect.left, t.clientY - rect.top, true);
        return;
      }
      lastTap = now;
      lastTapX = t.clientX;
      lastTapY = t.clientY;
      syncZoom();
    });
    stage.addEventListener('touchcancel', function () {
      pinch = null;
      touchStart = null;
      syncZoom();
    });

    stage.addEventListener('dblclick', function (event) {
      if (Date.now() - sawTouch < 700 || onCard(event.target) || isControl(event.target)) return;
      event.preventDefault();
      var rect = stage.getBoundingClientRect();
      zoomAbout(2, event.clientX - rect.left, event.clientY - rect.top, true);
    });
    stage.addEventListener('wheel', function (event) {
      if (onCard(event.target)) return;
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault();
        var rect = stage.getBoundingClientRect();
        var delta = event.deltaY;
        if (event.deltaMode === 1) delta *= 16;
        if (event.deltaMode === 2) delta *= rect.height || 800;
        var factor = Math.exp(-delta * 0.0022);
        if (factor < 0.2) factor = 0.2;
        if (factor > 5) factor = 5;
        zoomAbout(factor, event.clientX - rect.left, event.clientY - rect.top, false);
        return;
      }
      showHint(wheelHint);
    }, { passive: false });

    var zoomIn = root.querySelector('[data-zoom="in"]');
    var zoomOut = root.querySelector('[data-zoom="out"]');
    var reset = root.querySelector('[data-zoom="reset"]');
    function centerZoom(factor) {
      var rect = stage.getBoundingClientRect();
      zoomAbout(factor, rect.width / 2, rect.height / 2, true);
    }
    if (zoomIn) zoomIn.addEventListener('click', function () { centerZoom(1.7); });
    if (zoomOut) zoomOut.addEventListener('click', function () { centerZoom(1 / 1.7); });
    if (reset) reset.addEventListener('click', function () { animateTo(homeBox()); });

    stage.addEventListener('keydown', function (event) {
      if (document.activeElement !== stage) return;
      var rect = stage.getBoundingClientRect();
      var step = rect.width * 0.16;
      if (event.key === 'ArrowLeft') { event.preventDefault(); panBy(step, 0); }
      else if (event.key === 'ArrowRight') { event.preventDefault(); panBy(-step, 0); }
      else if (event.key === 'ArrowUp') { event.preventDefault(); panBy(0, step); }
      else if (event.key === 'ArrowDown') { event.preventDefault(); panBy(0, -step); }
      else if (event.key === '+' || event.key === '=' || event.key === 'Add') {
        event.preventDefault();
        centerZoom(1.7);
      } else if (event.key === '-' || event.key === '_' || event.key === 'Subtract') {
        event.preventDefault();
        centerZoom(1 / 1.7);
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
    svg.setAttribute('focusable', 'false');
    rememberLabels();
    bindFilters();
    bindGestures();
    syncZoom();
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
