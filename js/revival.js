// Micro-interactions for redesigned homepage
(function () {
  const topbar = document.querySelector('.topbar');
  const sections = document.querySelectorAll('.section, .hero');

  document.addEventListener('scroll', () => {
    if (!topbar) return;
    topbar.style.borderBottomColor = window.scrollY > 12 ? 'rgba(255,255,255,0.16)' : 'rgba(255,255,255,0.1)';
  });

  const reveal = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.animate([
          { opacity: 0, transform: 'translateY(22px)' },
          { opacity: 1, transform: 'translateY(0)' }
        ], { duration: 650, easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'forwards' });
        reveal.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  sections.forEach((el) => {
    el.style.opacity = '0';
    reveal.observe(el);
  });

  const setupMarquee = () => {
    const marquee = document.querySelector('.marquee');
    const track = marquee?.querySelector('.track');
    const seedGroup = track?.querySelector('.track-group');
    if (!marquee || !track || !seedGroup) return;

    // Preserve one canonical group and rebuild cleanly on each resize/font-load pass.
    const baseMarkup = track.dataset.baseMarkup || seedGroup.innerHTML;
    track.dataset.baseMarkup = baseMarkup;

    track.innerHTML = '';

    const createGroup = (hidden = false) => {
      const group = document.createElement('div');
      group.className = 'track-group';
      group.setAttribute('aria-hidden', hidden ? 'true' : 'false');
      group.innerHTML = baseMarkup;
      if (hidden) {
        group.querySelectorAll('a').forEach((a) => a.setAttribute('tabindex', '-1'));
      }
      return group;
    };

    const firstGroup = createGroup(false);
    track.appendChild(firstGroup);

    const baseWidth = Math.ceil(firstGroup.getBoundingClientRect().width);
    if (!baseWidth) return;

    // Ensure there is always enough repeated content to avoid any visual gap.
    const minTotalWidth = marquee.clientWidth * 2 + baseWidth;
    let totalWidth = baseWidth;

    while (totalWidth < minTotalWidth) {
      const clone = createGroup(true);
      track.appendChild(clone);
      totalWidth += baseWidth;
    }

    track.style.setProperty('--marquee-distance', `${baseWidth}px`);

    // Keep speed visually stable across content edits (~75px/sec)
    const durationSeconds = Math.max(16, Math.round(baseWidth / 75));
    track.style.setProperty('--marquee-duration', `${durationSeconds}s`);
  };

  if (document.fonts?.ready) {
    document.fonts.ready.then(setupMarquee);
  } else {
    window.addEventListener('load', setupMarquee, { once: true });
  }

  window.addEventListener('resize', setupMarquee);
})();
