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
    const firstGroup = track?.querySelector('.track-group');
    if (!marquee || !track || !firstGroup) return;

    const distance = Math.ceil(firstGroup.getBoundingClientRect().width);
    if (!distance) return;

    track.style.setProperty('--marquee-distance', `${distance}px`);

    // Keep speed visually stable across content edits (~75px/sec)
    const durationSeconds = Math.max(16, Math.round(distance / 75));
    track.style.setProperty('--marquee-duration', `${durationSeconds}s`);
  };

  if (document.fonts?.ready) {
    document.fonts.ready.then(setupMarquee);
  } else {
    window.addEventListener('load', setupMarquee, { once: true });
  }

  window.addEventListener('resize', setupMarquee);
})();
