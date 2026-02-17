// NYC Nightlife Platform — Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
  setActiveNav();
  setupEmailCapture();
  setupTools();
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
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const email = this.querySelector('input[type="email"]').value;
      const button = this.querySelector('button');
      
      if (email && isValidEmail(email)) {
        // Store locally for now (would integrate with MailerLite/ConvertKit)
        localStorage.setItem('nynightlife_email', email);
        button.textContent = '✓ Check your email!';
        button.disabled = true;
        
        setTimeout(() => {
          this.reset();
          button.textContent = 'Get Guide';
          button.disabled = false;
        }, 3000);
      }
    });
  });
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
      }
    }, 100);
  }
}

// Budget Night Planner
function calculateBudget() {
  const budget = document.getElementById('budget-input').value;
  const result = document.getElementById('budget-result');
  
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

// Analytics placeholder
function trackEvent(eventName, data = {}) {
  // Would integrate with Google Analytics or Plausible
  console.log('Event:', eventName, data);
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
