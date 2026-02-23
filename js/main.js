// NYC Nightlife Platform — Main JavaScript

const DEFAULT_EMAIL_ENDPOINT = 'https://formspree.io/f/xojnprqp';

document.addEventListener('DOMContentLoaded', function() {
  setActiveNav();
  setupEmailCapture();
  setupTools();
  setupAnalytics();
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
  // Google Analytics 4 via gtag
  if (typeof window.gtag === 'function') {
    window.gtag('event', eventName, data);
  }

  // Plausible custom event API
  if (typeof window.plausible === 'function') {
    window.plausible(eventName, { props: data });
  }

  // Optional custom callback hook for future integrations
  if (typeof window.NYNTrackEvent === 'function') {
    window.NYNTrackEvent(eventName, data);
  }

  // Keep console visibility during buildout
  console.log('[trackEvent]', eventName, data);
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
