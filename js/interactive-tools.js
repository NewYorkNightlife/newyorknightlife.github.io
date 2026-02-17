/* Interactive Tools: Spinner Wheel & Budget Planner */

document.addEventListener('DOMContentLoaded', () => {
  
  // ═══════════════════════════════════════════════════════════════
  // SPINNER WHEEL
  // ═══════════════════════════════════════════════════════════════
  
  const spinBtn = document.getElementById('spinBtn');
  const spinnerWheel = document.getElementById('spinnerWheel');
  const spinResult = document.getElementById('spinResult');
  
  const activities = [
    '🍸 Rooftop Cocktails & Skyline Views',
    '🍺 Williamsburg Craft Beer Crawl',
    '🎤 Live Music Venue Night',
    '💃 Dance Club All-Nighter',
    '🥃 East Village Speakeasy Hunt',
    '🍻 Lower East Side Bar Crawl',
    '🎭 Comedy Club & Drinks',
    '🌃 Midnight Downtown Vibes'
  ];
  
  let isSpinning = false;
  
  spinBtn.addEventListener('click', () => {
    if (isSpinning) return;
    isSpinning = true;
    spinBtn.disabled = true;
    spinBtn.textContent = 'SPINNING...';
    
    // Spin animation
    let spins = 0;
    const spinInterval = setInterval(() => {
      const rotation = spins * 45;
      spinnerWheel.style.transform = `rotate(${rotation}deg)`;
      spins++;
      
      if (spins > 20) {
        clearInterval(spinInterval);
        const finalSpin = Math.floor(Math.random() * 360);
        spinnerWheel.style.transform = `rotate(${finalSpin}deg)`;
        
        setTimeout(() => {
          const resultIndex = Math.floor((finalSpin + 22.5) / 45) % 8;
          spinResult.textContent = activities[resultIndex];
          spinResult.style.opacity = '1';
          isSpinning = false;
          spinBtn.disabled = false;
          spinBtn.textContent = 'SPIN IT';
        }, 500);
      }
    }, 50);
  });
  
  // ═══════════════════════════════════════════════════════════════
  // BUDGET PLANNER
  // ═══════════════════════════════════════════════════════════════
  
  const budgetSlider = document.getElementById('budgetSlider');
  const budgetDisplay = document.querySelector('.budget-display');
  const budgetResult = document.getElementById('budgetResult');
  
  const budgetPlans = {
    30: {
      title: '$30 Night',
      description: 'Happy hour crawl: 2-3 drinks at happy hour prices, free entrance, chat & vibes.'
    },
    50: {
      title: '$50 Night',
      description: 'Budget bar crawl: 4-5 drinks at mid-range bars, maybe one venue with a cover charge.'
    },
    75: {
      title: '$75 Night',
      description: 'Solid night out: Dinner ($20) + 4 cocktails ($12 each) + nice bar/club experience.'
    },
    100: {
      title: '$100 Night',
      description: 'Full experience: Pre-dinner drinks, nice dinner spot, quality cocktails, club entry.'
    },
    150: {
      title: '$150 Night',
      description: 'Premium night: Upscale dinner, premium cocktails, VIP bar or club, bottle service start.'
    },
    250: {
      title: '$250+ Night',
      description: 'High-end experience: Fancy dinner, top-tier cocktails, exclusive club, VIP treatment.'
    }
  };
  
  function getClosestBudget(value) {
    const budgets = [30, 50, 75, 100, 150, 250];
    return budgets.reduce((prev, curr) => 
      Math.abs(curr - value) < Math.abs(prev - value) ? curr : prev
    );
  }
  
  function updateBudgetResult() {
    const value = parseInt(budgetSlider.value);
    const closestBudget = getClosestBudget(value);
    budgetDisplay.textContent = `$${closestBudget}`;
    
    const plan = budgetPlans[closestBudget];
    budgetResult.innerHTML = `<p><strong>${plan.title}:</strong> ${plan.description}</p>`;
  }
  
  budgetSlider.addEventListener('input', updateBudgetResult);
  
  // Initialize
  updateBudgetResult();
});
