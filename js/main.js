// NYC Nightlife Platform — Main JavaScript

const DEFAULT_EMAIL_ENDPOINT = 'https://formspree.io/f/xojnprqp';

document.addEventListener('DOMContentLoaded', function() {
  setActiveNav();
  setupEmailCapture();
  setupTools();
  setupAnalytics();
  setupInternalLinkBlock();
  setupAffiliateModule();
});

// Set active nav link
function setActiveNav() {
  const path = window.location.pathname;
  const navLinks = document.querySelectorAll('nav a');
  navLinks.forEach(link => {
    if (link.href.includes(path) || (path === '/' && link.href.includes('index'))) {
      link.classList.add('active');
    }
  });
}

// Email Capture Handler
function setupEmailCapture() {
  const forms = document.querySelectorAll('.email-form');
  forms.forEach(form => {
    const button = form.querySelector('button');
    if (button && !button.dataset.originalText) {
      button.dataset.originalText = button.textContent;
    }

    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      const emailInput = this.querySelector('input[type="email"]');
      const email = emailInput ? emailInput.value.trim() : '';
      const submitButton = this.querySelector('button');

      if (!email || !isValidEmail(email)) return;

      setButtonState(submitButton, 'Saving…', true);

      const payload = {
        email,
        source: window.location.pathname,
        page_url: window.location.href,
        captured_at: new Date().toISOString()
      };

      const endpoint = getEmailEndpoint(this);

      try {
        if (!endpoint) {
          // Fallback capture so we never lose the lead while endpoint is being configured.
          storeLeadFallback(payload);
          showEmailSuccess(this, submitButton, '✓ Saved. (Provider not connected yet)');
          return;
        }

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          throw new Error(`Email capture failed with status ${response.status}`);
        }

        storeLeadFallback(payload);
        showEmailSuccess(this, submitButton, '✓ Check your email!');
        trackEvent('email_capture_success', { source: payload.source });
      } catch (error) {
        console.error(error);
        storeLeadFallback(payload);
        showEmailSuccess(this, submitButton, '✓ Saved. (Retrying sync later)');
        trackEvent('email_capture_fallback', { source: payload.source });
      }
    });
  });
}

function getEmailEndpoint(form) {
  if (form.dataset.endpoint) return form.dataset.endpoint;

  const meta = document.querySelector('meta[name="nyn-email-endpoint"]');
  if (meta && meta.content) return meta.content;

  if (window.NYN_EMAIL_ENDPOINT) return window.NYN_EMAIL_ENDPOINT;

  return DEFAULT_EMAIL_ENDPOINT;
}

function storeLeadFallback(payload) {
  const key = 'nynightlife_email_leads';
  const leads = JSON.parse(localStorage.getItem(key) || '[]');
  leads.push(payload);
  localStorage.setItem(key, JSON.stringify(leads));
}

function showEmailSuccess(form, button, successText) {
  setButtonState(button, successText, true);
  form.reset();

  setTimeout(() => {
    setButtonState(button, button?.dataset.originalText || 'Submit', false);
  }, 2500);
}

function setButtonState(button, label, disabled) {
  if (!button) return;
  button.textContent = label;
  button.disabled = disabled;
}

function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

// What Should We Do Tonight Spinner
function spinWheel() {
  const activities = [
    '🍸 Find a rooftop bar in Manhattan',
    '🎉 Hit a live music venue in Brooklyn',
    '🍷 Wine bar crawl in SoHo',
    '🎤 Comedy show in Hell\'s Kitchen',
    '💃 Dance club in the Meatpacking District',
    '🍺 Craft beer evening in Williamsburg',
    '🎭 Theater in the Theater District',
    '🍣 Sake bar in East Village',
    '🏊 Club pool party (summer)',
    '📸 Nightlife photography tour'
  ];
  
  const button = document.getElementById('spin-button');
  if (button) {
    button.disabled = true;
    let spins = 0;
    const spinInterval = setInterval(() => {
      const random = Math.floor(Math.random() * activities.length);
      document.getElementById('wheel-result').textContent = activities[random];
      spins++;
      if (spins > 15) {
        clearInterval(spinInterval);
        button.disabled = false;
        trackEvent('tool_spin_wheel_complete', {
          source: window.location.pathname,
          result: document.getElementById('wheel-result')?.textContent || ''
        });
      }
    }, 100);
  }
}

// Budget Night Planner
function calculateBudget() {
  const budget = document.getElementById('budget-input').value;
  const result = document.getElementById('budget-result');

  trackEvent('tool_budget_calculate', {
    source: window.location.pathname,
    budget
  });
  
  if (budget < 30) {
    result.innerHTML = `
      <p><strong>$${budget} Night Out Plan:</strong></p>
      <ul>
        <li>Happy hour cocktails (2 drinks, $5-6 each)</li>
        <li>Free admission at most bars</li>
        <li>Check: <a href="https://www.eventbrite.com/" target="_blank" rel="noopener">Eventbrite</a> for free events</li>
      </ul>
    `;
  } else if (budget < 75) {
    result.innerHTML = `
      <p><strong>$${budget} Night Out Plan:</strong></p>
      <ul>
        <li>Dinner at casual spot ($15-20)</li>
        <li>3-4 drinks at mid-range bars ($8-10 each)</li>
        <li>Live music or event venue</li>
        <li>Option: <a href="https://www.getyourguide.com" target="_blank" rel="noopener">GetYourGuide</a> bar crawl tours</li>
      </ul>
    `;
  } else {
    result.innerHTML = `
      <p><strong>$${budget}+ Night Out Plan:</strong></p>
      <ul>
        <li>Quality dinner ($30-50)</li>
        <li>Premium cocktail lounge ($15-18 per drink)</li>
        <li>Upscale club or rooftop venue ($20 entry + drinks)</li>
        <li>VIP experience: <a href="https://www.viator.com" target="_blank" rel="noopener">Viator</a> NYC VIP tours</li>
      </ul>
    `;
  }
}

// Neighborhood Quiz
function startNighborhoodQuiz() {
  const answers = [];
  const quiz = document.getElementById('quiz-container');
  if (!quiz) return;
  
  // Simple version - full quiz would be more interactive
  const preferences = prompt('What\'s your vibe? (rooftop/dive/upscale/dance):');
  const neighborhood = getNeighborhoodRecommendation(preferences);
  
  document.getElementById('quiz-result').innerHTML = `
    <h3>Your Neighborhood: ${neighborhood.name}</h3>
    <p>${neighborhood.description}</p>
    <p><a href="${neighborhood.guide}">See Guide →</a></p>
  `;

  trackEvent('tool_neighborhood_quiz_complete', {
    source: window.location.pathname,
    vibe: preferences || 'unknown',
    recommendation: neighborhood.name
  });
}

function getNeighborhoodRecommendation(vibe) {
  const recommendations = {
    'rooftop': {
      name: 'Midtown West',
      description: 'Best rooftop bars with Manhattan skyline views',
      guide: '/guides/best-nightlife-experiences.html'
    },
    'dive': {
      name: 'East Village',
      description: 'Classic dive bars, punk history, local crowd',
      guide: '/guides/best-nightlife-experiences.html'
    },
    'upscale': {
      name: 'SoHo',
      description: 'Upscale cocktail lounges and wine bars',
      guide: '/guides/best-nightlife-experiences.html'
    },
    'dance': {
      name: 'Meatpacking District',
      description: 'Top nightclubs and electronic music venues',
      guide: '/guides/best-nightlife-experiences.html'
    }
  };
  
  return recommendations[vibe] || {
    name: 'Brooklyn',
    description: 'Trendy bars, craft beer, live music',
    guide: '/guides/best-nightlife-experiences.html'
  };
}

// Setup tools on tools page
function setupTools() {
  // Initialize any tool-specific listeners
  const spinButton = document.getElementById('spin-button');
  if (spinButton) {
    spinButton.addEventListener('click', spinWheel);
  }
  
  const budgetInput = document.getElementById('budget-input');
  if (budgetInput) {
    budgetInput.addEventListener('change', calculateBudget);
  }
  
  const quizButton = document.getElementById('quiz-button');
  if (quizButton) {
    quizButton.addEventListener('click', startNighborhoodQuiz);
  }
}

function setupAnalytics() {
  trackEvent('page_view', {
    path: window.location.pathname,
    title: document.title
  });

  setupOutboundLinkTracking();
}

function setupInternalLinkBlock() {
  const pathname = window.location.pathname;
  const main = document.querySelector('main');
  if (!main) return;

  // Skip homepage; keep links focused on deeper pages.
  if (pathname === '/' || pathname === '/index.html') return;

  const links = getInternalLinkRecommendations(pathname);
  if (!links || links.length < 3) return;

  const existing = document.querySelector('.internal-links-block');
  if (existing) return;

  const section = document.createElement('section');
  section.className = 'section internal-links-block';
  section.style.paddingTop = '24px';

  section.innerHTML = `
    <div class="card glow" style="max-width:1100px; margin:0 auto;">
      <p class="eyebrow">Keep Exploring</p>
      <h2 style="margin-top:4px;">Next Best Pages</h2>
      <div class="links" style="margin-top:8px; gap:12px 18px;">
        ${links.map(link => `<a href="${link.href}" data-internal-rec="1">${link.label} →</a>`).join('')}
      </div>
    </div>
  `;

  const footer = document.querySelector('footer');
  if (footer && footer.parentNode) {
    footer.parentNode.insertBefore(section, footer);
  } else {
    main.appendChild(section);
  }

  section.querySelectorAll('a[data-internal-rec="1"]').forEach(a => {
    a.addEventListener('click', () => {
      trackEvent('internal_link_recommendation_click', {
        from: pathname,
        to: a.getAttribute('href') || ''
      });
    });
  });
}

function getInternalLinkRecommendations(pathname) {
  const common = [
    { href: '/guides/', label: 'Guides Hub' },
    { href: '/tools/', label: 'Nightlife Tools' },
    { href: '/neighborhoods/', label: 'Neighborhoods Hub' },
    { href: '/tonight/', label: 'Tonight in NYC' }
  ];

  if (pathname.startsWith('/guides/')) {
    return [
      { href: '/tools/nyc-night-planner.html', label: 'NYC Night Planner' },
      { href: '/neighborhoods/lower-east-side-nightlife.html', label: 'Lower East Side Guide' },
      { href: '/rankings/best-bars-in-nyc.html', label: 'Best Bars in NYC' },
      ...common.slice(1, 3)
    ];
  }

  if (pathname.startsWith('/neighborhoods/')) {
    return [
      { href: '/tools/venue-compare-nyc.html', label: 'Venue Compare Tool' },
      { href: '/guides/best-nightlife-experiences.html', label: 'Best Nightlife Experiences' },
      { href: '/safety/late-night-safety-by-borough.html', label: 'Late-Night Safety by Borough' },
      ...common.slice(0, 2)
    ];
  }

  if (pathname.startsWith('/tools/')) {
    return [
      { href: '/guides/bar-crawl-guide.html', label: 'Bar Crawl Guide' },
      { href: '/tonight/things-to-do-in-nyc-tonight.html', label: 'Things to Do Tonight' },
      { href: '/visit/first-time-nyc-nightlife-guide.html', label: 'First-Time Nightlife Guide' },
      ...common.slice(0, 2)
    ];
  }

  if (pathname.startsWith('/rankings/') || pathname.startsWith('/categories/')) {
    return [
      { href: '/guides/events-this-weekend.html', label: 'Events This Weekend' },
      { href: '/tools/budget-planner.html', label: 'Budget Planner Tool' },
      { href: '/neighborhoods/williamsburg-nightlife.html', label: 'Williamsburg Nightlife' },
      ...common.slice(0, 2)
    ];
  }

  return common;
}

function setupAffiliateModule() {
  const pathname = window.location.pathname;
  const monetizedPaths = [
    '/guides/', '/tools/', '/things-to-do/', '/visit/', '/rankings/', '/categories/', '/tonight/', '/weekend/'
  ];

  if (!monetizedPaths.some(prefix => pathname.startsWith(prefix))) return;
  if (document.querySelector('.affiliate-module')) return;

  const section = document.createElement('section');
  section.className = 'section affiliate-module';
  section.style.paddingTop = '20px';

  const offers = getAffiliateOffers(pathname);

  section.innerHTML = `
    <div class="card glow" style="max-width:1100px; margin:0 auto;">
      <p class="eyebrow">Book Smarter</p>
      <h2 style="margin-top:4px;">Recommended Booking Options</h2>
      <p class="muted" style="margin-top:-8px;">Affiliate disclosure: We may earn a commission if you book through these links, at no extra cost to you.</p>
      <div class="links" style="gap:12px 18px; margin-top:8px;">
        ${offers.map(offer => `<a href="${offer.href}" target="_blank" rel="nofollow sponsored noopener" data-affiliate-link="1">${offer.label} ↗</a>`).join('')}
      </div>
    </div>
  `;

  const footer = document.querySelector('footer');
  if (footer && footer.parentNode) {
    footer.parentNode.insertBefore(section, footer);
  } else {
    const main = document.querySelector('main');
    if (main) main.appendChild(section);
  }

  section.querySelectorAll('a[data-affiliate-link="1"]').forEach(a => {
    a.addEventListener('click', () => {
      trackEvent('affiliate_link_click', {
        from: pathname,
        to: a.getAttribute('href') || '',
        label: (a.textContent || '').trim()
      });
    });
  });
}

function getAffiliateOffers(pathname) {
  const campaign = getAffiliateCampaign(pathname);

  const defaultOffers = [
    { label: 'Eventbrite NYC Events', href: withUTM('https://www.eventbrite.com/d/ny--new-york/nightlife/', campaign, 'eventbrite') },
    { label: 'Viator NYC Experiences', href: withUTM('https://www.viator.com/New-York-City/d687-ttd', campaign, 'viator') },
    { label: 'GetYourGuide NYC Tours', href: withUTM('https://www.getyourguide.com/new-york-city-l59/', campaign, 'getyourguide') }
  ];

  if (pathname.startsWith('/visit/') || pathname.startsWith('/things-to-do/')) {
    return [
      { label: 'Booking.com NYC Hotels', href: withUTM('https://www.booking.com/city/us/new-york.html', campaign, 'booking') },
      { label: 'Viator NYC Experiences', href: withUTM('https://www.viator.com/New-York-City/d687-ttd', campaign, 'viator') },
      { label: 'GetYourGuide NYC Tours', href: withUTM('https://www.getyourguide.com/new-york-city-l59/', campaign, 'getyourguide') }
    ];
  }

  return defaultOffers;
}

function getAffiliateCampaign(pathname) {
  if (pathname.startsWith('/guides/')) return 'guides';
  if (pathname.startsWith('/tools/')) return 'tools';
  if (pathname.startsWith('/visit/')) return 'visit';
  if (pathname.startsWith('/things-to-do/')) return 'things_to_do';
  if (pathname.startsWith('/rankings/')) return 'rankings';
  if (pathname.startsWith('/categories/')) return 'categories';
  if (pathname.startsWith('/tonight/')) return 'tonight';
  if (pathname.startsWith('/weekend/')) return 'weekend';
  return 'site';
}

function withUTM(url, campaign, source) {
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}utm_source=nynightlife&utm_medium=affiliate_module&utm_campaign=${encodeURIComponent(campaign)}&utm_content=${encodeURIComponent(source)}`;
}

function setupOutboundLinkTracking() {
  const links = document.querySelectorAll('a[href]');

  links.forEach(link => {
    link.addEventListener('click', () => {
      const href = link.getAttribute('href') || '';
      const isExternal = /^https?:\/\//i.test(href) && !href.includes(window.location.host);

      if (isExternal) {
        trackEvent('outbound_click', {
          href,
          text: (link.textContent || '').trim().slice(0, 120),
          source: window.location.pathname
        });
      }
    });
  });
}

// Lightweight analytics bridge for GA4/Plausible/custom stacks.
function trackEvent(eventName, data = {}) {
  const payload = sanitizeEventPayload(data);

  // Google Analytics 4 via gtag
  if (typeof window.gtag === 'function') {
    window.gtag('event', eventName, payload);
  }

  // Plausible custom event API
  if (typeof window.plausible === 'function') {
    window.plausible(eventName, { props: payload });
  }

  // Optional custom callback hook for future integrations
  if (typeof window.NYNTrackEvent === 'function') {
    window.NYNTrackEvent(eventName, payload);
  }

  // Keep console visibility during buildout
  console.log('[trackEvent]', eventName, payload);
}

function sanitizeEventPayload(data) {
  const out = {};
  Object.entries(data || {}).forEach(([key, value]) => {
    if (value === undefined || value === null) return;

    if (typeof value === 'string') {
      out[key] = value.trim().slice(0, 200);
      return;
    }

    if (typeof value === 'number' || typeof value === 'boolean') {
      out[key] = value;
      return;
    }

    out[key] = String(value).slice(0, 200);
  });

  return out;
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    if (href !== '#' && document.querySelector(href)) {
      e.preventDefault();
      document.querySelector(href).scrollIntoView({
        behavior: 'smooth'
      });
    }
  });
});
