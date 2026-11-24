/* Nyla voice v1 (2026-11): hold Nyla, or tap the mic in her chat, ask out loud, hear her answer.
   Fully in-browser, $0: Web Speech API recognition (webkitSpeechRecognition) for the question,
   speechSynthesis for the answer. No server and no keys. The answer comes from the same
   rules engine as typed chat (js/concierge.js -> window.NylaChat), so spoken answers can
   never drift from the checked facts on the pages.
   Optional later (v1.1, off by default): set window.NYLA_VOICE_CONFIG = { transcribeUrl: '...' }
   before this script and browsers without speech recognition record with MediaRecorder and
   POST the clip to that URL (a Cloudflare Worker running Whisper). It must return {"text": "..."}. */
(function (W) {
  'use strict';
  var HOLD_MS = 350;          // press longer than this on Nyla = push-to-talk; shorter = normal tap (opens chat)
  var START_WATCHDOG_MS = 5000; // some browsers expose the API but never fire events (old Edge, in-app webviews)
  var MAX_SPOKEN = 420;       // keep spoken answers short; the full answer is always on screen
  var CHUNK = 180;            // Chrome desktop cuts utterances off at ~15s, so speak in short chunks
  var MAX_RECORD_MS = 15000;

  // ---------------------------------------------------------------- pure helpers
  var ENT = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'", '&nbsp;': ' ', '&rarr;': ' ', '&middot;': ',' };

  // HTML answer -> what Nyla says out loud. Drops "→" navigation links, reads at most 3 list
  // items, turns "21+" into "21 plus" and "$20–$40" into "$20 to $40", strips emoji.
  function speechText(html) {
    var s = String(html == null ? '' : html);
    s = s.replace(/<a\b[^>]*>[^<]*(?:→|&rarr;)[^<]*<\/a>/g, ' ');
    var items = 0, extra = 0;
    s = s.replace(/<li\b[^>]*>([\s\S]*?)<\/li>/g, function (m, inner) {
      items++;
      if (items > 3) { extra++; return ' '; }
      return ' ' + inner + '. ';
    });
    s = s.replace(/<br\s*\/?>/gi, '. ').replace(/<\/(p|div|ul|ol)>/gi, '. ');
    s = s.replace(/<[^>]+>/g, ' ');
    s = s.replace(/&[a-z]+;|&#\d+;/gi, function (e) { return ENT[e] != null ? ENT[e] : ' '; });
    s = s.replace(/[\uD83C-\uDBFF][\uDC00-\uDFFF]|[\u2600-\u27BF]|\uFE0F/g, '');
    s = s.replace(/[→←↗•·]/g, ' ');
    s = s.replace(/(\d)\s*[–—-]\s*(\$?\d)/g, '$1 to $2');
    s = s.replace(/(\d)\+/g, '$1 plus');
    s = s.replace(/~\s*(?=\$?\d)/g, 'about ');
    s = s.replace(/\s*&\s*/g, ' and ');
    s = s.replace(/:\s*\./g, ':').replace(/\s+([.,!?;:])/g, '$1');
    s = s.replace(/([.!?:;,])(?:\s*[.!?:;,])+/g, '$1').replace(/\s+/g, ' ').trim();
    s = s.replace(/^[.,;:\s]+/, '');
    if (extra) {
      s = s.replace(/\s*\b(\d+) more\.\s*/, function (m, n) { extra += +n; return ' '; }).trim();
      s += (/[.!?]$/.test(s) ? ' ' : '. ') + 'And ' + extra + ' more on screen.';
    }
    if (s.length > MAX_SPOKEN) {
      var cut = s.slice(0, MAX_SPOKEN), end = Math.max(cut.lastIndexOf('. '), cut.lastIndexOf('? '), cut.lastIndexOf('! '));
      s = (end > 80 ? cut.slice(0, end + 1) : cut.replace(/\s+\S*$/, '') + '.') + ' The rest is on screen.';
    }
    return s;
  }

  // Split into sentence chunks of at most `max` characters.
  function chunks(text, max) {
    max = max || CHUNK;
    var out = [], parts = String(text || '').match(/[^.!?]+[.!?]*\s*/g) || [];
    var cur = '';
    parts.forEach(function (p) {
      p = p.trim();
      if (!p) return;
      while (p.length > max) {
        var at = p.lastIndexOf(', ', max); if (at < 40) at = p.lastIndexOf(' ', max); if (at < 1) at = max;
        if (cur) { out.push(cur); cur = ''; }
        out.push(p.slice(0, at + (p.charAt(at) === ',' ? 1 : 0)).trim());
        p = p.slice(at + 1).trim();
      }
      if (cur && (cur + ' ' + p).length > max) { out.push(cur); cur = p; }
      else cur = cur ? cur + ' ' + p : p;
    });
    if (cur) out.push(cur);
    return out;
  }

  // Best available English female voice. Names differ per OS, so score by a known-good list.
  var PREFERRED = ['Samantha', 'Ava', 'Allison', 'Susan', 'Zoe', 'Google US English', 'Microsoft Aria',
    'Microsoft Jenny', 'Microsoft Ava', 'Microsoft Michelle', 'Microsoft Emma', 'Microsoft Zira',
    'Google UK English Female', 'Karen', 'Moira', 'Tessa', 'Serena', 'Victoria', 'Kate', 'Fiona'];
  var MALE = /\b(male|daniel|alex|fred|david|mark|guy|george|james|tom|aaron|arthur|rishi|oliver|ryan|eric|christopher|brian|andrew|roger|steffan|reed|ralph|evan|nathan|gordon|lee|rocko|eddy|grandpa)\b/i;
  function voiceScore(v) {
    var n = String(v.name || ''), sc = 0;
    if (!/^en([-_]|$)/i.test(v.lang || '')) return -1e9;
    for (var i = 0; i < PREFERRED.length; i++) if (n.indexOf(PREFERRED[i]) === 0 || n.indexOf(' ' + PREFERRED[i]) !== -1 || n === PREFERRED[i]) { sc += 100 - i * 3; break; }
    if (/female|woman/i.test(n)) sc += 40;
    if (MALE.test(n)) sc -= 200;
    if (/natural|neural|premium|enhanced|online/i.test(n)) sc += 15;
    if (/^en[-_]US$/i.test(v.lang)) sc += 10;
    if (/novelty|whisper|bells|bubbles|cellos|zarvox|trinoids|organ|bad news|good news|jester|superstar|boing|albert|wobble/i.test(n)) sc -= 500;
    return sc;
  }
  function pickVoice(voices) {
    var best = null, bs = -1e8;
    (voices || []).forEach(function (v) { var s = voiceScore(v); if (s > bs) { bs = s; best = v; } });
    return best;
  }

  // ---------------------------------------------------------------- styles (Night Signal tokens)
  var CSS = [
    '.nyb-bubble{-webkit-touch-callout:none;-webkit-user-select:none;user-select:none;touch-action:manipulation}',
    '.nyb-bubble::before{content:"";position:absolute;left:50%;bottom:4%;width:118%;height:56%;transform:translateX(-50%);border-radius:50%;pointer-events:none;opacity:0;transition:opacity .2s}',
    '.nyb-bubble.nyv-listening{animation:none}',
    '.nyb-bubble.nyv-listening::before{opacity:1;border:2px solid #6EA8FF;box-shadow:0 0 22px rgba(110,168,255,.75),inset 0 0 18px rgba(110,168,255,.35);animation:nyvRing 1.1s ease-out infinite}',
    '.nyb-bubble.nyv-listening{filter:drop-shadow(0 18px 24px rgba(0,0,0,.55)) drop-shadow(0 0 30px rgba(110,168,255,.7))}',
    '.nyb-bubble.nyv-speaking{filter:drop-shadow(0 18px 24px rgba(0,0,0,.55)) drop-shadow(0 0 30px rgba(255,184,107,.75))}',
    '@keyframes nyvRing{0%{transform:translateX(-50%) scale(.92);opacity:1}100%{transform:translateX(-50%) scale(1.18);opacity:0}}',
    '.nyv-live{position:fixed;right:22px;bottom:360px;z-index:1550;max-width:258px;background:linear-gradient(160deg,#0c1424,#080B12);color:#F2F5FA;border:1px solid rgba(110,168,255,.7);border-radius:16px;padding:10px 14px;font:14px/1.45 "Instrument Sans",system-ui,sans-serif;box-shadow:0 0 24px rgba(110,168,255,.35),0 14px 38px rgba(0,0,0,.6)}',
    '.nyv-live b{display:flex;align-items:center;gap:8px;color:#6EA8FF;font-size:12px;letter-spacing:.12em;text-transform:uppercase}',
    '.nyv-live .nyv-heard{display:block;margin-top:4px;min-height:1.2em}',
    '@media (max-width:540px){.nyv-live{max-width:220px;font-size:13px}}',
    /* phones: Nyla is a 44px round button in the header (site.css), so glow the ring instead */
    '@media (max-width:767px){.nyb-bubble::before{display:none}body .nyb-bubble.nyv-listening{border-color:#6EA8FF;box-shadow:0 0 0 4px rgba(110,168,255,.35),0 0 20px rgba(110,168,255,.9);animation:nyvPulse 1.2s ease-out infinite}body .nyb-bubble.nyv-speaking{border-color:#FFB86B;box-shadow:0 0 0 4px rgba(255,184,107,.3),0 0 20px rgba(255,184,107,.9)}}',
    '.nyv-bars{display:inline-flex;align-items:flex-end;gap:2px;height:12px}',
    '.nyv-bars i{display:block;width:3px;height:4px;border-radius:2px;background:currentColor;animation:nyvBar .9s ease-in-out infinite}',
    '.nyv-bars i:nth-child(2){animation-delay:.15s}.nyv-bars i:nth-child(3){animation-delay:.3s}.nyv-bars i:nth-child(4){animation-delay:.45s}',
    '@keyframes nyvBar{0%,100%{height:3px}50%{height:12px}}',
    '.nyv-mic{flex:none;width:42px;border-radius:10px;border:1px solid rgba(110,168,255,.55);background:rgba(110,168,255,.12);color:#6EA8FF;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;padding:0;position:relative}',
    '.nyv-mic svg{width:20px;height:20px}',
    '.nyv-mic:hover{background:rgba(110,168,255,.22)}',
    '.nyv-mic:focus-visible,.nyv-spk:focus-visible{outline:2px solid #FFB86B;outline-offset:2px}',
    '.nyv-mic[aria-pressed="true"]{background:#6EA8FF;color:#05070C;box-shadow:0 0 0 0 rgba(110,168,255,.7);animation:nyvPulse 1.2s ease-out infinite}',
    '@keyframes nyvPulse{0%{box-shadow:0 0 0 0 rgba(110,168,255,.7)}100%{box-shadow:0 0 0 12px rgba(110,168,255,0)}}',
    '.nyv-spk{background:none;border:0;color:#C5CEDA;cursor:pointer;padding:4px 6px;display:inline-flex;align-items:center}',
    '.nyv-spk svg{width:20px;height:20px}',
    '.nyv-spk[aria-pressed="true"]{color:#FFB86B}',
    '.nyb-head .nyb-close{margin-left:0}',
    '.nyv-spk{margin-left:auto}',
    '.nyb-head-ava{position:relative;transition:box-shadow .2s}',
    '.nyb-panel.nyv-speaking .nyb-head-ava{border-color:#FFB86B;box-shadow:0 0 0 3px rgba(255,184,107,.25),0 0 18px rgba(255,184,107,.8);animation:nyvTalk .7s ease-in-out infinite alternate}',
    '.nyb-panel.nyv-listening .nyb-head-ava{border-color:#6EA8FF;box-shadow:0 0 0 3px rgba(110,168,255,.25),0 0 18px rgba(110,168,255,.8)}',
    '@keyframes nyvTalk{from{transform:scale(1)}to{transform:scale(1.07)}}',
    '.nyv-status{display:none;align-items:center;gap:8px;padding:0 16px 6px;font-size:.8rem;color:#C5CEDA}',
    '.nyv-status.on{display:flex}',
    '.nyb-panel.nyv-listening .nyv-status{color:#6EA8FF}',
    '.nyb-panel.nyv-speaking .nyv-status{color:#FFB86B}',
    '.nyv-status button{margin-left:auto;background:none;border:1px solid currentColor;color:inherit;border-radius:999px;padding:2px 10px;font-size:.75rem;cursor:pointer}',
    '.nyb-m.nyv-note{border-color:rgba(110,168,255,.35);color:#C5CEDA;font-size:.84rem}',
    '@media (prefers-reduced-motion:reduce){.nyb-bubble.nyv-listening::before,.nyv-bars i,.nyv-mic[aria-pressed="true"],.nyb-panel.nyv-speaking .nyb-head-ava{animation:none}}'
  ].join('\n');

  var MIC_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0M12 17v4M8 21h8"/></svg>';
  var SPK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4z"/><path class="nyv-wave" d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/></svg>';
  var BARS = '<span class="nyv-bars" aria-hidden="true"><i></i><i></i><i></i><i></i></span>';

  // ---------------------------------------------------------------- controller
  function create(chat, env) {
    env = env || {};
    var win = env.window || W, doc = env.document || win.document;
    var SR = env.SpeechRecognition !== undefined ? env.SpeechRecognition : (win.SpeechRecognition || win.webkitSpeechRecognition || null);
    var synth = env.speechSynthesis !== undefined ? env.speechSynthesis : (win.speechSynthesis || null);
    var Utter = env.SpeechSynthesisUtterance || win.SpeechSynthesisUtterance;
    var cfg = win.NYLA_VOICE_CONFIG || {};
    var nav = win.navigator || {};
    var canRecord = !!(cfg.transcribeUrl && win.MediaRecorder && nav.mediaDevices && nav.mediaDevices.getUserMedia && win.fetch);
    var setT = env.setTimeout || win.setTimeout, clearT = env.clearTimeout || win.clearTimeout;
    function lsGet(k) { try { return win.localStorage.getItem(k); } catch (e) { return null; } }
    function lsSet(k, v) { try { win.localStorage.setItem(k, v); } catch (e) {} }
    function track(n, p) { try { if (win.posthog && win.posthog.capture) win.posthog.capture(n, p || {}); } catch (e) {} }

    var panel = chat.panel, bubble = chat.bubble;
    var msgs = panel.querySelector('.nyb-msgs');
    var input = panel.querySelector('.nyb-in');
    var form = panel.querySelector('.nyb-inrow');
    var head = panel.querySelector('.nyb-head');
    var closeBtn = panel.querySelector('.nyb-close');

    var state = 'idle', mode = null, rec = null, recorder = null, gotStart = false, finalText = '', interim = '', errored = false;
    var holdTimer = null, holding = false, suppressClick = false, watchdog = null, speakGuard = null;
    var srBroken = false, queue = [], live = [], voice = null;
    var speakOn = lsGet('nyv_speak') === '1' && !!synth; // on after the first voice question, until muted

    // ---- DOM
    var style = doc.createElement('style');
    style.textContent = CSS;
    (doc.head || doc.body).appendChild(style);

    var mic = doc.createElement('button');
    mic.type = 'button';
    mic.className = 'nyv-mic';
    mic.setAttribute('aria-label', 'Ask ' + chat.name() + ' out loud');
    mic.setAttribute('aria-pressed', 'false');
    mic.innerHTML = MIC_SVG;
    var send = form.querySelector('.nyb-send');
    if (send && form.insertBefore) form.insertBefore(mic, send); else form.appendChild(mic);

    var spk = doc.createElement('button');
    spk.type = 'button';
    spk.className = 'nyv-spk';
    spk.innerHTML = SPK_SVG;
    if (closeBtn && head.insertBefore) head.insertBefore(spk, closeBtn); else head.appendChild(spk);
    if (!synth) spk.style.display = 'none';

    var status = doc.createElement('div');
    status.className = 'nyv-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    var typing = panel.querySelector('.nyb-typing');
    if (typing && typing.parentNode && typing.parentNode.insertBefore) typing.parentNode.insertBefore(status, typing);
    else panel.appendChild(status);

    var liveCap = null;
    bubble.setAttribute('aria-label', 'Chat with ' + chat.name() + ', the nightlife concierge. Press and hold to ask out loud.');

    function syncSpk() {
      spk.setAttribute('aria-pressed', speakOn ? 'true' : 'false');
      spk.setAttribute('aria-label', speakOn ? 'Turn off ' + chat.name() + '’s voice' : 'Turn on ' + chat.name() + '’s voice');
      spk.title = speakOn ? 'Voice on' : 'Voice off';
    }
    syncSpk();

    function note(html) {
      var m = doc.createElement('div');
      m.className = 'nyb-m bot nyv-note';
      m.innerHTML = html;
      msgs.appendChild(m);
      msgs.scrollTop = msgs.scrollHeight;
      return m;
    }
    function setStatus(html) {
      status.innerHTML = html || '';
      status.className = 'nyv-status' + (html ? ' on' : '');
      var b = status.querySelector && status.querySelector('button');
      if (html && b && b.addEventListener) b.addEventListener('click', function () { toggle('tap'); });
    }
    function cls(el, c, on) { if (el && el.classList) { if (on) el.classList.add(c); else el.classList.remove(c); } }
    function setState(s) {
      state = s;
      cls(bubble, 'nyv-listening', s === 'listening'); cls(panel, 'nyv-listening', s === 'listening');
      cls(bubble, 'nyv-speaking', s === 'speaking'); cls(panel, 'nyv-speaking', s === 'speaking');
      mic.setAttribute('aria-pressed', s === 'listening' ? 'true' : 'false');
      mic.setAttribute('aria-label', s === 'listening' ? 'Stop listening' : 'Ask ' + chat.name() + ' out loud');
      if (s === 'listening') setStatus(BARS + '<span>Listening…' + (mode === 'hold' ? ' let go when you’re done' : '') + '</span>' + (mode === 'hold' ? '' : '<button type="button">Done</button>'));
      else if (s === 'thinking') setStatus('<span>' + chat.name() + ' is thinking…</span>');
      else if (s === 'speaking') setStatus(BARS + '<span>' + chat.name() + ' is speaking</span><button type="button">Stop</button>');
      else setStatus('');
    }
    function showCaption(text) {
      if (!liveCap) {
        liveCap = doc.createElement('div');
        liveCap.className = 'nyv-live';
        liveCap.setAttribute('aria-hidden', 'true'); // the panel transcript is the accessible copy
        doc.body.appendChild(liveCap);
      }
      if (!liveCap.querySelector || !liveCap.querySelector('.nyv-heard') || !liveCap.innerHTML) liveCap.innerHTML = '<b>' + BARS + 'Listening</b><span class="nyv-heard"></span>';
      var sp = liveCap.querySelector('.nyv-heard');
      if (sp) sp.textContent = text || 'Ask me anything…';
      // sit next to Nyla wherever the page put her (full figure on desktop, header button on phones)
      try {
        var r = bubble.getBoundingClientRect(), H = win.innerHeight, Wd = win.innerWidth;
        liveCap.style.right = Math.max(8, Wd - r.right) + 'px';
        if (r.top > 150) { liveCap.style.bottom = (H - r.top + 10) + 'px'; liveCap.style.top = 'auto'; }
        else { liveCap.style.top = (r.bottom + 10) + 'px'; liveCap.style.bottom = 'auto'; }
      } catch (e) {}
    }
    function hideCaption() { if (liveCap && liveCap.parentNode) liveCap.parentNode.removeChild(liveCap); liveCap = null; }

    // ---- speaking
    function loadVoice() { if (synth && synth.getVoices) voice = pickVoice(synth.getVoices()) || voice; }
    loadVoice();
    if (synth && synth.addEventListener) synth.addEventListener('voiceschanged', loadVoice);
    else if (synth) synth.onvoiceschanged = loadVoice;

    var unlocked = false;
    // iOS Safari only lets speech start from a tap. Speak a silent utterance inside the tap
    // so the real answer, which arrives later, is allowed to play.
    function unlock() {
      if (unlocked || !synth || !Utter) return;
      unlocked = true;
      try { var u = new Utter(' '); u.volume = 0; synth.speak(u); } catch (e) {}
    }
    function stopSpeaking() {
      queue = []; live = [];
      if (speakGuard) { clearT(speakGuard); speakGuard = null; }
      try { if (synth) synth.cancel(); } catch (e) {}
      if (state === 'speaking') setState('idle');
    }
    function speak(text) {
      if (!synth || !Utter || !text) return;
      queue = queue.concat(chunks(text));
      if (state !== 'speaking') next();
    }
    function next() {
      if (speakGuard) { clearT(speakGuard); speakGuard = null; }
      var t = queue.shift();
      if (!t) { live = []; if (state === 'speaking') setState('idle'); return; }
      if (!voice) loadVoice();
      var u = new Utter(t);
      if (voice) { u.voice = voice; u.lang = voice.lang; } else u.lang = 'en-US';
      u.rate = 1.02; u.pitch = 1.05;
      var done = false;
      function fin() { if (done) return; done = true; next(); }
      u.onend = fin; u.onerror = fin;
      live.push(u); // keep a reference: Chrome drops onend for garbage-collected utterances
      setState('speaking');
      // safety net if the engine never fires onend (seen on some Android builds)
      speakGuard = setT(fin, 2500 + t.length * 90);
      try { synth.speak(u); } catch (e) { fin(); }
    }
    function openChat() { chat.open({ noFocus: true }); }
    function onReply(html) {
      if (state === 'thinking' && !speakOn) setState('idle');
      if (!speakOn || state === 'listening') return;
      var t = speechText(html);
      if (t) speak(t);
    }

    // ---- listening
    function supported() { return !!SR && !srBroken; }
    function unsupported() {
      track('nyla_voice_unsupported');
      note(synth
        ? 'Talking to me doesn’t work in this browser yet. It works in Chrome, and in Safari with Siri turned on. Type your question and I’ll read my answer out loud.'
        : 'Voice doesn’t work in this browser yet. It works in Chrome, and in Safari with Siri turned on. You can still type your question.');
      if (synth && lsGet('nyv_muted') !== '1') { speakOn = true; lsSet('nyv_speak', '1'); syncSpk(); }
    }
    function privacyOnce() {
      if (lsGet('nyv_noticed')) return;
      lsSet('nyv_noticed', '1');
      note('Your browser will ask to use your mic. Your browser’s own speech service (Google in Chrome, Apple in Safari) turns your words into text. We don’t record or keep your audio.');
    }
    function begin(m) {
      mode = m;
      if (state === 'speaking') stopSpeaking();
      if (state === 'listening') return;
      unlock();
      if (synth && lsGet('nyv_muted') !== '1') { speakOn = true; lsSet('nyv_speak', '1'); syncSpk(); }
      if (!chat.isOpen() && m !== 'hold') openChat();
      if (!supported()) {
        if (canRecord) return beginRecording(m);
        if (m === 'hold') openChat();
        return unsupported();
      }
      privacyOnce();
      finalText = ''; interim = ''; errored = false; gotStart = false;
      try {
        rec = new SR();
        rec.lang = 'en-US';
        rec.interimResults = true;
        rec.continuous = false;
        rec.maxAlternatives = 1;
      } catch (e) { srBroken = true; return begin(m); }
      rec.onstart = rec.onaudiostart = function () { gotStart = true; };
      rec.onresult = function (ev) {
        var fin = '', mid = '';
        for (var i = 0; i < ev.results.length; i++) {
          var r = ev.results[i];
          if (r.isFinal) fin += r[0].transcript; else mid += r[0].transcript;
        }
        finalText = fin.trim(); interim = mid.trim();
        var shown = (finalText + ' ' + interim).trim();
        input.value = shown;
        if (mode === 'hold') showCaption(shown);
      };
      rec.onerror = function (ev) {
        errored = true;
        var e = ev && ev.error;
        track('nyla_voice_error', { error: e });
        if (e === 'not-allowed' || e === 'service-not-allowed') {
          if (mode === 'hold') openChat();
          note('I can’t hear you because the mic is blocked. Allow the microphone for nynightlife.com in your browser settings (on iPhone, Siri must be on too), then try again. You can always type.');
        } else if (e === 'no-speech') {
          note('I didn’t catch that. Tap the mic and try again.');
        } else if (e === 'network') {
          note('Voice needs an internet connection right now. Type your question instead.');
        } else if (e === 'audio-capture') {
          note('I can’t find a microphone. You can type your question instead.');
        } else if (e !== 'aborted') {
          note('Voice hit a snag. Type your question instead.');
        }
      };
      rec.onend = function () { finish(); };
      try { rec.start(); } catch (e) { srBroken = true; rec = null; if (m === 'hold') openChat(); return unsupported(); }
      setState('listening');
      track('nyla_voice_start', { mode: m });
      if (m === 'hold') showCaption('');
      watchdog = setT(function () {
        if (!gotStart && state === 'listening') {
          srBroken = true;
          try { rec.abort(); } catch (e) {}
          rec = null; hideCaption(); setState('idle');
          if (mode === 'hold') openChat();
          unsupported();
        }
      }, START_WATCHDOG_MS);
    }
    function finish() {
      if (watchdog) { clearT(watchdog); watchdog = null; }
      if (state !== 'listening') return;
      rec = null;
      hideCaption();
      var q = (finalText || interim).trim();
      setState('idle');
      if (!q) {
        input.value = '';
        if (!errored) { if (mode === 'hold') openChat(); note('I didn’t catch that. Try again, a little closer to the mic.'); }
        return;
      }
      submit(q);
    }
    function submit(q) {
      if (!chat.isOpen()) openChat();
      track('nyla_voice_question');
      setState('thinking');
      chat.ask(q); // shows the question as the user's bubble (the transcript) and answers it
      setT(function () { if (state === 'thinking') setState('idle'); }, 6000);
    }
    function end() {
      if (recorder) { try { recorder.stop(); } catch (e) {} return; }
      if (rec && state === 'listening') { try { rec.stop(); } catch (e) { finish(); } }
    }
    function toggle(m) {
      if (state === 'listening') return end();
      if (state === 'speaking') { stopSpeaking(); return; }
      begin(m);
    }

    // ---- v1.1 fallback: record and send to our own Worker (only when configured)
    function beginRecording(m) {
      privacyOnce();
      nav.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
        var parts = [];
        try { recorder = new win.MediaRecorder(stream); } catch (e) { stream.getTracks().forEach(function (t) { t.stop(); }); recorder = null; return unsupported(); }
        recorder.ondataavailable = function (e) { if (e.data && e.data.size) parts.push(e.data); };
        recorder.onstop = function () {
          stream.getTracks().forEach(function (t) { t.stop(); });
          var type = recorder.mimeType || 'audio/webm';
          recorder = null; hideCaption();
          if (!parts.length) { setState('idle'); return; }
          setState('thinking');
          win.fetch(cfg.transcribeUrl, { method: 'POST', headers: { 'Content-Type': type }, body: new win.Blob(parts, { type: type }) })
            .then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
            .then(function (d) {
              var q = (d && d.text || '').trim();
              setState('idle');
              if (q) submit(q); else note('I didn’t catch that. Try again, a little closer to the mic.');
            }, function () { setState('idle'); note('Voice hit a snag. Type your question instead.'); });
        };
        recorder.start();
        setState('listening');
        if (m === 'hold') showCaption('');
        setT(function () { if (recorder) end(); }, MAX_RECORD_MS);
      }, function () {
        if (m === 'hold') openChat();
        note('I can’t hear you because the mic is blocked. Allow the microphone for nynightlife.com in your browser settings, then try again.');
      });
    }

    // ---- wiring
    mic.addEventListener('click', function () { toggle('tap'); });
    spk.addEventListener('click', function () {
      speakOn = !speakOn;
      lsSet('nyv_speak', speakOn ? '1' : '0');
      lsSet('nyv_muted', speakOn ? '0' : '1');
      if (!speakOn) stopSpeaking(); else unlock();
      syncSpk();
    });
    // typing a question cancels any speech still playing
    form.addEventListener('submit', function () { if (state === 'speaking') stopSpeaking(); });
    if (closeBtn) closeBtn.addEventListener('click', function () { end(); stopSpeaking(); });

    // press-and-hold on Nyla = push-to-talk. A short tap still opens the chat as before.
    function down(e) {
      if (e && e.button != null && e.button !== 0) return;
      clearT(holdTimer);
      holding = false;
      holdTimer = setT(function () {
        holdTimer = null;
        holding = true;
        suppressClick = true;
        begin('hold');
      }, HOLD_MS);
    }
    function up() {
      if (holdTimer) { clearT(holdTimer); holdTimer = null; }
      if (holding) { holding = false; end(); }
    }
    bubble.addEventListener('pointerdown', down);
    doc.addEventListener('pointerup', up);
    doc.addEventListener('pointercancel', up);
    bubble.addEventListener('contextmenu', function (e) { if (e.preventDefault) e.preventDefault(); });
    // swallow the click that ends a hold, before concierge.js sees it
    doc.addEventListener('click', function (e) {
      if (suppressClick && e && e.target && (e.target === bubble || (bubble.contains && bubble.contains(e.target)))) {
        suppressClick = false;
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        if (e.stopPropagation) e.stopPropagation();
        if (e.preventDefault) e.preventDefault();
      } else suppressClick = false;
    }, true);

    return {
      onReply: onReply,
      state: function () { return state; },
      speakOn: function () { return speakOn; },
      toggle: toggle, begin: begin, end: end, down: down, up: up,
      voice: function () { return voice; },
      els: { mic: mic, spk: spk, status: status }
    };
  }

  var api = { speechText: speechText, chunks: chunks, pickVoice: pickVoice, voiceScore: voiceScore, create: create };
  W.NylaVoice = api;

  function boot(chat) {
    if (W.__nylaVoice || !chat || !chat.panel) return;
    try {
      var v = create(chat);
      W.__nylaVoice = v;
      W.__nylaOnReply = v.onReply;
    } catch (e) { /* voice is an extra; never break the typed chat */ }
  }
  if (W.NylaChat) boot(W.NylaChat); else W.__nylaVoiceInit = boot;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : this);
