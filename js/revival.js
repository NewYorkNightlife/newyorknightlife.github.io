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
})();
