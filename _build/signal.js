/* Night Signal: one lamp layer and a short card rise. Reduced motion stays still. */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return;
  document.documentElement.classList.add('js');
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var lamp = document.querySelector('.lamp');
  if (lamp && fine && window.matchMedia('(min-width: 700px)').matches) {
    window.addEventListener('pointermove', function (e) {
      lamp.style.transform = 'translate3d(' + e.clientX + 'px,' + e.clientY + 'px,0)';
    }, { passive: true });
  }
  var nodes = document.querySelectorAll('.rise');
  if (!nodes.length || !('IntersectionObserver' in window)) {
    for (var i = 0; i < nodes.length; i++) nodes[i].classList.add('in');
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add('in');
        io.unobserve(en.target);
      });
    }, { threshold: 0.12 });
    for (var j = 0; j < nodes.length; j++) io.observe(nodes[j]);
  }
  var route = document.querySelector('.route[data-live]');
  if (!route) return;
  var parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York', hour: 'numeric', hourCycle: 'h23'
  }).formatToParts(new Date());
  var hour = 0;
  for (var k = 0; k < parts.length; k++) if (parts[k].type === 'hour') hour = parseInt(parts[k].value, 10) || 0;
  if (hour < 5) hour += 24;
  var stops = route.querySelectorAll('[data-hour]');
  var current = null;
  for (var n = 0; n < stops.length; n++) {
    if (parseInt(stops[n].getAttribute('data-hour'), 10) <= hour) current = stops[n];
  }
  if (current) current.classList.add('now');
})();
