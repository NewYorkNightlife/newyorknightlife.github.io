/* Mascot Chat Interface */

document.addEventListener('DOMContentLoaded', () => {
  const mascotChar = document.getElementById('mascotChar');
  const chatInterface = document.getElementById('chatInterface');
  const closeChat = document.getElementById('closeChat');
  const chatInput = document.getElementById('chatInput');
  const sendChat = document.getElementById('sendChat');
  const chatMessages = document.getElementById('chatMessages');

  // Toggle chat
  mascotChar.addEventListener('click', () => {
    chatInterface.classList.toggle('active');
  });

  closeChat.addEventListener('click', (e) => {
    e.stopPropagation();
    chatInterface.classList.remove('active');
  });

  // Sample responses
  const responses = {
    'hi': 'Hey! Ready for an amazing night in NYC? 🎉',
    'hello': 'What\'s up! Looking for tonight\'s best spots?',
    'what do i do': 'Explore our guides, spin the wheel, or check events this weekend!',
    'bars': 'Check out our Best NYC Nightlife Experiences guide for all the spots.',
    'rooftop': 'Rooftops are best in summer! Check our venue guide for the hottest ones.',
    'budget': 'Use our budget planner tool to see what you can do with your budget.',
    'crawl': 'Bar crawls are legendary! Read our Bar Crawl Mastery guide.',
    'events': 'Check Events This Weekend for real-time listings and tickets.',
    'where': 'What neighborhood are you interested in? Manhattan, Brooklyn, Queens?',
    'help': 'Ask me about bars, events, neighborhoods, budget planning, or crawls!',
    'default': 'Tell me more! Ask about bars, events, budget, or nightlife tips.'
  };

  function getResponse(input) {
    const lower = input.toLowerCase();
    for (let key in responses) {
      if (lower.includes(key)) {
        return responses[key];
      }
    }
    return responses.default;
  }

  function addMessage(text, sender) {
    const msgEl = document.createElement('div');
    msgEl.className = `chat-msg ${sender}-msg`;
    msgEl.innerHTML = `<p>${text}</p>`;
    chatMessages.appendChild(msgEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Send message
  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    chatInput.value = '';

    setTimeout(() => {
      addMessage(getResponse(text), 'bot');
    }, 500);
  }

  sendChat.addEventListener('click', sendMessage);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
});
