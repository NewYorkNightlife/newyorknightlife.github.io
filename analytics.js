/* PostHog analytics (installed by the site-posthog skill): page views, heatmaps, privacy-masked
   session replay, and standard goal events (text/call/email taps, quote buttons, form sends,
   affiliate and outbound clicks). Serve this file as-is from the site's public/static root.
   Skip tracking in this browser: visit any page with ?notrack=1 (undo with ?notrack=0). */
(function () {
  'use strict';
  /* ---- per-site settings (filled in by register_site.py render-js; no double-underscore blanks may remain) ---- */
  var POSTHOG_KEY = "phc_ykPxc7tJ3GL85AmSZDS3snAp4pnziWUpLj4yGq8K6C4Z";       /* public project key, starts with phc_ */
  var POSTHOG_HOST = "https://us.i.posthog.com";      /* e.g. "https://us.i.posthog.com" */
  var LIVE_HOSTS = ["nynightlife.com", "www.nynightlife.com"];                 /* only these domains are tracked (never local previews) */
  var PRIVATE = ".nyb-msgs, .nyb-panel";              /* chat/free-text areas: never recorded or click-tracked ("" = none) */
  var AFFILIATE = [];          /* substrings marking affiliate links, e.g. ["amzn.to/", "tag="] */
  var MIRROR_TO_GA = false;                  /* true = also send these events to Google Analytics (gtag) */
  var RECORDINGS = true;                      /* false = no session recordings at all (sensitive sites) */
  var REPLAY_SAMPLE = 1.0;                /* share of visits recorded, 0-1 (protects the shared free quota) */
  var COOKIELESS = false;                      /* true = no cookies/localStorage for PostHog (each page view is a new visitor) */
  var NOTRACK_KEY = "nyn_notrack";
  var BRIDGE_HOOK = "NYNTrackEvent";               /* name of the site's own custom-event hook ("" = none) */
  var BRIDGE_SKIP = ["outbound_click", "page_view"];               /* hook events already counted by the listeners below */
  /* ------------------------------------------------------------------------------------------------ */

  function optedOut() {
    try {
      var flag = new URLSearchParams(window.location.search).get('notrack');
      if (flag === '1') localStorage.setItem(NOTRACK_KEY, '1');
      if (flag === '0') localStorage.removeItem(NOTRACK_KEY);
      return localStorage.getItem(NOTRACK_KEY) === '1';
    } catch (_) { return false; }
  }
  var ownerOptedOut = optedOut(); /* runs first so ?notrack=1 is remembered even before tracking is on */
  var enabled = LIVE_HOSTS.indexOf(window.location.hostname) !== -1 &&
    /^phc_[A-Za-z0-9_-]{20,}$/.test(POSTHOG_KEY) && !ownerOptedOut;

  /* Private areas (chat logs, free-text boxes) get PostHog's "ph-no-capture" class: they show as a blank
     block in recordings and are never used for click tracking. Also applied to areas added later. */
  function hidePrivate(root) {
    if (!PRIVATE || !root || !root.querySelectorAll) return;
    try {
      if (root.matches && root.matches(PRIVATE)) root.classList.add('ph-no-capture');
      var list = root.querySelectorAll(PRIVATE);
      for (var i = 0; i < list.length; i++) list[i].classList.add('ph-no-capture');
    } catch (_) { /* invalid selector: fall back to text masking below */ }
  }
  if (enabled && PRIVATE) {
    hidePrivate(document);
    document.addEventListener('DOMContentLoaded', function () { hidePrivate(document); });
    if (window.MutationObserver) {
      new MutationObserver(function (records) {
        for (var i = 0; i < records.length; i++) {
          for (var j = 0; j < records[i].addedNodes.length; j++) hidePrivate(records[i].addedNodes[j]);
        }
      }).observe(document.documentElement, {childList: true, subtree: true});
    }
  }

  if (enabled && !window.posthog) {
    /* Official PostHog loader (docs: posthog.com/docs/libraries/js). */
    !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],Object.defineProperty(u,"toString",{configurable:!0,enumerable:!0,writable:!0,value:function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e}}),Object.defineProperty(u.people,"toString",{configurable:!0,enumerable:!0,writable:!0,value:function(){return u.toString(1)+".people (stub)"}}),o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagResult isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
    var config = {
      api_host: POSTHOG_HOST,
      /* Pinned on purpose: 2026-06-25+ defaults record network request bodies (form contents). Handles SPA page changes. */
      defaults: '2026-05-30',
      person_profiles: 'identified_only',
      capture_heatmaps: true,
      respect_dnt: true,
      disable_session_recording: !RECORDINGS,
      session_recording: {
        maskAllInputs: true,
        maskTextSelector: PRIVATE ? PRIVATE + ', .ph-mask' : '.ph-mask',
        /* Explicit false overrides the dashboard setting: form contents are never recorded. */
        recordBody: false,
        recordHeaders: false,
        sampleRate: REPLAY_SAMPLE
      }
    };
    if (COOKIELESS) config.persistence = 'memory';
    window.posthog.init(POSTHOG_KEY, config);
  }

  /* One call for site code: window.siteTrack('event_name', {event_label: '...'}). Never pass personal data. */
  window.siteTrack = function (name, details, options) {
    options = options || {};
    if (MIRROR_TO_GA && typeof window.gtag === 'function') window.gtag('event', options.gaName || name, details);
    if (enabled && window.posthog && typeof window.posthog.capture === 'function') {
      window.posthog.capture(name, details, options.beforeLeaving ? {transport: 'sendBeacon', send_instantly: true} : undefined);
    }
  };

  /* If the site already has its own tracking helper with a custom hook, forward its events here.
     (Skipped if the site defines the hook itself; then its own code decides.) */
  if (BRIDGE_HOOK && typeof window[BRIDGE_HOOK] !== 'function') {
    window[BRIDGE_HOOK] = function (name, payload) {
      if (BRIDGE_SKIP.indexOf(name) !== -1) return;
      var safe = {};
      for (var k in (payload || {})) {
        var v = payload[k];
        if (typeof v === 'string') v = v.split('?')[0].split('#')[0].slice(0, 120); /* no query strings, short values */
        if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') safe[k] = v;
      }
      if (!safe.event_label) safe.event_label = safe.label || safe.anchor || safe.text || safe.to || safe.source || '';
      window.siteTrack(String(name).slice(0, 60), safe);
    };
  }

  function isAffiliate(href) {
    for (var i = 0; i < AFFILIATE.length; i++) if (href.indexOf(AFFILIATE[i]) !== -1) return true;
    return false;
  }

  document.addEventListener('click', function (event) {
    var el = event.target.closest ? event.target.closest('a,button') : null;
    if (!el) return;
    var inPrivate = false;
    try { inPrivate = !!(PRIVATE && el.closest(PRIVATE)); } catch (_) {}
    var href = el.getAttribute('href') || '';
    var label = inPrivate ? '(private area)' : (el.dataset.track || el.textContent || '').trim().slice(0, 60);
    if (/^tel:/i.test(href)) return window.siteTrack('phone_click', {event_label: label}, {beforeLeaving: true});
    if (/^sms:/i.test(href)) return window.siteTrack('sms_click', {event_label: label}, {beforeLeaving: true});
    if (/^mailto:/i.test(href)) return window.siteTrack('email_click', {event_label: label}, {beforeLeaving: true});
    if (href && isAffiliate(href)) return window.siteTrack('affiliate_click', {event_label: label, link_host: el.hostname || ''}, {beforeLeaving: true});
    if (el.hostname && LIVE_HOSTS.indexOf(el.hostname) === -1 && el.hostname !== window.location.hostname && /^https?:/i.test(href)) {
      return window.siteTrack('outbound_click', {event_label: label, link_host: el.hostname}, {beforeLeaving: true});
    }
    if (/#(contact|quote|book|booking)$/i.test(href) || /^(quote|book|contact)/i.test(el.dataset.track || '')) {
      return window.siteTrack('quote_click', {event_label: label});
    }
  }, true);

  /* Form sends (never the field values). Sites that confirm success should call siteTrack('form_submission'). */
  document.addEventListener('submit', function (event) {
    var f = event.target;
    if (f && f.tagName === 'FORM') window.siteTrack('form_submit_attempt', {event_label: String(f.id || f.getAttribute('name') || 'form').slice(0, 40)}, {beforeLeaving: true});
  }, true);
})();
