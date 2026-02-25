(function () {
  'use strict';

  const FEED_URL = '/data/tonight-feed.json';

  function esc(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function fmtET(iso) {
    if (!iso) return 'Unavailable';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return 'Unavailable';
    return d.toLocaleString('en-US', {
      timeZone: 'America/New_York',
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    }) + ' ET';
  }

  function renderWeather(weather) {
    const el = document.getElementById('tonight-weather');
    if (!el) return;
    if (!weather) {
      el.innerHTML = '<p>Weather unavailable.</p>';
      return;
    }

    const fiveDay = Array.isArray(weather.five_day) ? weather.five_day : [];
    el.innerHTML = `
      <p><strong>${esc(weather.icon || '⛅')} ${esc(weather.summary || 'NYC weather')}</strong></p>
      <p>${weather.temp_f ?? '—'}°F ${weather.feels_like_f != null ? `(feels like ${weather.feels_like_f}°F)` : ''}</p>
      ${fiveDay.length ? `<ul>${fiveDay.map(d => `<li>${esc(d.day || '')}: ${esc(d.summary || '')} ${d.high_f != null ? `(${d.high_f}°/${d.low_f ?? '—'}°)` : ''}</li>`).join('')}</ul>` : ''}
    `;
  }

  function renderHeadlines(headlines) {
    const el = document.getElementById('tonight-headlines');
    if (!el) return;
    const items = Array.isArray(headlines) ? headlines.slice(0, 3) : [];
    if (!items.length) {
      el.innerHTML = '<li>No live headlines available yet.</li>';
      return;
    }
    el.innerHTML = items.map(h => `<li><a href="${esc(h.url || '#')}" target="_blank" rel="noopener">${esc(h.title || 'Untitled')}</a> <span style="color:#b7b3ab;">(${esc(h.source || 'Source')})</span></li>`).join('');
  }

  function renderFeatured(events) {
    const el = document.getElementById('tonight-featured');
    if (!el) return;
    const items = Array.isArray(events) ? events : [];
    if (!items.length) {
      el.innerHTML = '<p>No verified featured events yet.</p>';
      return;
    }

    el.innerHTML = items.map(event => {
      const verification = event.verification || {};
      const sources = Array.isArray(verification.sources) ? verification.sources : [];
      return `
        <article class="tonight-card">
          <h3>${esc(event.title)}</h3>
          <p><strong>${esc(event.time_window || 'Time TBD')}</strong> · ${esc(event.borough || 'NYC')} · ${esc(event.venue || 'Venue TBD')}</p>
          <p>${esc(event.summary || '')}</p>
          <p><a href="${esc(event.booking_url || '/tonight/things-to-do-in-nyc-tonight.html')}">View details</a></p>
          <p class="tonight-verify">Verification: ${esc(String(verification.source_count ?? 0))}/3 sources · ${esc(verification.confidence || 'pending')}</p>
          ${sources.length ? `<ul>${sources.map(s => `<li><a href="${esc(s.url || '#')}" target="_blank" rel="noopener">${esc(s.name || 'Source')}</a></li>`).join('')}</ul>` : ''}
        </article>
      `;
    }).join('');
  }

  function renderLastThree(items) {
    const el = document.getElementById('tonight-last-three');
    if (!el) return;
    const rows = Array.isArray(items) ? items.slice(0, 3) : [];
    if (!rows.length) {
      el.innerHTML = '<li>Last-three-night archive will appear after first automated updates.</li>';
      return;
    }
    el.innerHTML = rows.map(r => `<li><strong>${esc(r.date || '')}</strong>: <a href="${esc(r.url || '#')}">${esc(r.title || 'Night recap')}</a></li>`).join('');
  }

  async function loadTonightFeed() {
    const updated = document.getElementById('tonight-updated-at');
    try {
      const res = await fetch(FEED_URL, { cache: 'no-store' });
      if (!res.ok) throw new Error(`Feed fetch failed: ${res.status}`);
      const data = await res.json();
      if (updated) updated.textContent = fmtET(data.generated_at);

      renderWeather(data.weather);
      renderHeadlines(data.headlines);
      renderFeatured(data.featured_tonight);
      renderLastThree(data.last_three_nights);
    } catch (err) {
      if (updated) updated.textContent = 'Unavailable';
      const featured = document.getElementById('tonight-featured');
      if (featured) {
        featured.innerHTML = '<p>Live feed unavailable right now. Check back shortly.</p>';
      }
      console.error(err);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadTonightFeed);
  } else {
    loadTonightFeed();
  }
})();
