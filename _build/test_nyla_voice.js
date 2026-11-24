/* Tests for Nyla voice (js/nyla-voice.js) with js/concierge.js and a built data/venues.json.
   Run after a build:  node _build/test_nyla_voice.js <built-site-folder>
   No browser and no npm packages: a tiny fake DOM, a fake clock, and fake Web Speech
   objects stand in for the browser. Exit code 1 on any failure. */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const site = path.resolve(process.argv[2] || path.join(__dirname, '..'));
const data = JSON.parse(fs.readFileSync(path.join(site, 'data', 'venues.json'), 'utf8'));
const CONCIERGE = fs.readFileSync(path.join(__dirname, 'concierge.js'), 'utf8');
const VOICE = fs.readFileSync(path.join(__dirname, 'nyla-voice.js'), 'utf8');
const V = require('./nyla-voice.js');

let fails = 0, passes = 0;
function ok(cond, name, extra) {
  if (cond) { passes++; return; }
  fails++; console.log('FAIL', name, extra === undefined ? '' : JSON.stringify(extra).slice(0, 400));
}

// ---------------------------------------------------------------- pure helpers
(function unit() {
  const card = '<b>House of Yes</b> (Bushwick)<br><b>Cover:</b> $20–$40; free before 10pm (1 source)<br><b>Dress:</b> Costumes welcome<br><b>Age:</b> 21+<br><a href="https://nynightlife.com/venues/house-of-yes.html">Sources &amp; full facts, checked Nov 1, 2026 →</a>';
  const t = V.speechText(card);
  ok(/House of Yes/.test(t) && /Cover: \$20 to \$40/.test(t), 'speechText reads the card', t);
  ok(/21 plus/.test(t), 'speechText says 21 plus', t);
  ok(!/Sources|→|<|&amp;/.test(t), 'speechText drops arrow links, tags and entities', t);
  const list = '<b>Rooftops:</b><ul>' + ['A', 'B', 'C', 'D', 'E'].map(x => '<li><a href="/x">' + x + ' Bar</a> (Chelsea)</li>').join('') + '</ul>2 more. <a href="/v">All venue fact pages →</a>';
  const lt = V.speechText(list);
  ok(/A Bar/.test(lt) && /C Bar/.test(lt) && !/D Bar/.test(lt) && /And 4 more on screen\.$/.test(lt) && !/2 more/.test(lt), 'speechText reads 3 list items then counts the rest', lt);
  ok(V.speechText('GA ~$43, table ~$77') === 'GA about $43, table about $77', 'speechText reads ~ as about', V.speechText('GA ~$43, table ~$77'));
  ok(!/:\./.test(lt) && !/\.\./.test(lt), 'speechText leaves no doubled punctuation', lt);
  ok(V.speechText('Hey 🥂 I’m Nyla. Have fun 😉') === 'Hey I’m Nyla. Have fun', 'speechText strips emoji', V.speechText('Hey 🥂 I’m Nyla. Have fun 😉'));
  const long = Array.from({ length: 40 }, (_, i) => 'Sentence number ' + i + ' is here.').join(' ');
  const lt2 = V.speechText(long);
  ok(lt2.length < 460 && /The rest is on screen\.$/.test(lt2), 'speechText caps long answers', lt2.length);
  const ch = V.chunks(long + ' ' + 'word, '.repeat(80) + 'end.', 180);
  ok(ch.every(c => c.length <= 180) && ch.join(' ').replace(/\s+/g, ' ').includes('Sentence number 39'), 'chunks stay under 180 chars and keep all text', ch.map(c => c.length));
  ok(V.chunks('').length === 0, 'chunks of empty text');

  const voices = [
    { name: 'Daniel', lang: 'en-GB' }, { name: 'Google UK English Male', lang: 'en-GB' },
    { name: 'Google US English', lang: 'en-US' }, { name: 'Samantha', lang: 'en-US' },
    { name: 'Amélie', lang: 'fr-CA' }, { name: 'Bad News', lang: 'en-US' }
  ];
  ok(V.pickVoice(voices).name === 'Samantha', 'pickVoice prefers Samantha', V.pickVoice(voices));
  ok(V.pickVoice(voices.filter(v => v.name !== 'Samantha')).name === 'Google US English', 'pickVoice falls back to Google US English');
  ok(V.pickVoice([{ name: 'Microsoft Guy Online (Natural)', lang: 'en-US' }, { name: 'Microsoft Aria Online (Natural) - English (United States)', lang: 'en-US' }]).name.startsWith('Microsoft Aria'), 'pickVoice picks Aria over Guy on Edge');
  ok(V.pickVoice([{ name: 'Amélie', lang: 'fr-CA' }]) === null, 'pickVoice never picks a non-English voice');
  ok(V.pickVoice([{ name: 'English United States', lang: 'en_US' }, { name: 'English UK female', lang: 'en_GB' }]).name === 'English UK female', 'pickVoice uses "female" on Android');
})();

// ---------------------------------------------------------------- fake browser
function makeEl(tag) {
  const kids = {};
  const e = {
    tagName: String(tag || 'div').toUpperCase(), children: [], parentNode: null, style: {}, attrs: {}, listeners: {},
    value: '', className: '', innerHTML: '', textContent: '', type: '', title: '',
    classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); } },
    setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
    appendChild(c) { c.parentNode = this; this.children.push(c); return c; },
    insertBefore(c, ref) { c.parentNode = this; const i = this.children.indexOf(ref); if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); return c; },
    removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) this.children.splice(i, 1); c.parentNode = null; return c; },
    contains(x) { for (let n = x; n; n = n.parentNode) if (n === this) return true; return false; },
    addEventListener(n, f, cap) { (this.listeners[n] = this.listeners[n] || []).push({ f, cap: !!cap }); },
    querySelector(s) { if (!kids[s]) { kids[s] = makeEl(); kids[s].parentNode = this; } return kids[s]; },
    focus() { e.focused = (e.focused || 0) + 1; }, get scrollHeight() { return 0; }
  };
  return e;
}
function fire(el, type, ev) { (el.listeners[type] || []).filter(l => !l.cap).forEach(l => l.f(ev || {})); }

function browser(opt) {
  opt = opt || {};
  const timers = [];
  let now = 0, seq = 0;
  const clock = {
    set(f, ms) { const id = ++seq; timers.push({ id, at: now + (ms || 0), f }); return id; },
    clear(id) { const i = timers.findIndex(t => t.id === id); if (i >= 0) timers.splice(i, 1); }
  };
  const store = Object.assign({ nyb_teased_at: String(Date.now()) }, opt.storage || {});
  const body = makeEl('body'), headEl = makeEl('head');
  const doc = {
    readyState: 'complete', body, head: headEl, listeners: {}, currentScript: { src: 'https://nynightlife.com/js/concierge.js?v=1' },
    createElement: t => makeEl(t), querySelector: () => null,
    addEventListener(n, f, cap) { (this.listeners[n] = this.listeners[n] || []).push({ f, cap: !!cap }); }
  };
  const recs = [], spoken = [], posted = [];
  function SR() { this.started = 0; this.stopped = 0; this.aborted = 0; recs.push(this); }
  SR.prototype.start = function () { if (opt.srThrows) throw new Error('nope'); this.started++; };
  SR.prototype.stop = function () { this.stopped++; };
  SR.prototype.abort = function () { this.aborted++; };
  const synth = {
    voices: [{ name: 'Daniel', lang: 'en-GB' }, { name: 'Samantha', lang: 'en-US' }],
    getVoices() { return this.voices; }, speak(u) { spoken.push(u); }, cancel() { this.cancelled = (this.cancelled || 0) + 1; },
    addEventListener() {}
  };
  function Utter(t) { this.text = t; }
  const ctx = {
    document: doc, location: { pathname: opt.page || '/' }, console, navigator: {},
    Image: function () { return {}; },
    localStorage: { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } },
    fetch: (url, init) => {
      if (/venues\.json/.test(url)) return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(data))) });
      posted.push({ url, init });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ text: opt.transcript || '' }) });
    },
    setTimeout: clock.set, clearTimeout: clock.clear,
    Date, Math, String, RegExp, Array, Object, JSON, Promise, Error
  };
  if (!opt.noSR) ctx.webkitSpeechRecognition = SR;
  if (!opt.noSynth) { ctx.speechSynthesis = synth; ctx.SpeechSynthesisUtterance = Utter; }
  if (opt.config) ctx.NYLA_VOICE_CONFIG = opt.config;
  if (opt.recorder) {
    ctx.navigator.mediaDevices = { getUserMedia: () => Promise.resolve({ getTracks: () => [{ stop() {} }] }) };
    ctx.MediaRecorder = function () { const r = this; r.mimeType = 'audio/mp4'; r.start = () => { r.on = 1; }; r.stop = () => { r.ondataavailable({ data: { size: 9 } }); r.onstop(); }; ctx.lastRecorder = r; };
    ctx.Blob = function (parts, o) { this.parts = parts; this.type = o.type; };
  }
  ctx.window = ctx;
  vm.createContext(ctx);
  if (opt.voiceFirst) { vm.runInContext(VOICE, ctx); vm.runInContext(CONCIERGE, ctx); }
  else { vm.runInContext(CONCIERGE, ctx); vm.runInContext(VOICE, ctx); }

  const bubble = body.children[0], panel = body.children[1];
  const msgs = panel.querySelector('.nyb-msgs');
  const B = {
    ctx, store, recs, spoken, posted, bubble, panel, msgs, synth,
    voice: ctx.__nylaVoice,
    input: panel.querySelector('.nyb-in'),
    form: panel.querySelector('.nyb-inrow'),
    async run(ms) {
      const end = now + ms;
      while (true) {
        await new Promise(r => setImmediate(r));
        timers.sort((a, b) => a.at - b.at || a.id - b.id);
        const t = timers[0];
        if (!t || t.at > end) break;
        timers.shift(); now = t.at; t.f();
      }
      now = end;
      await new Promise(r => setImmediate(r));
    },
    text() { return msgs.children.map(m => m.className + ': ' + m.innerHTML).join('\n'); },
    bots() { return msgs.children.filter(m => /\bbot\b/.test(m.className)); },
    users() { return msgs.children.filter(m => /\buser\b/.test(m.className)).map(m => m.innerHTML); },
    rec() { return recs[recs.length - 1]; },
    say(rec, words) { rec.onstart && rec.onstart(); rec.onresult({ results: [Object.assign([{ transcript: words }], { isFinal: true })] }); rec.onend(); },
    async finishSpeech() { for (let i = 0; i < 50 && spoken.length; i++) { const u = spoken.find(x => !x.done && x.onend); if (!u) break; u.done = true; u.onend(); await B.run(1); } },
    click(target) {
      const ev = { target, stopped: false, stopImmediatePropagation() { this.stopped = true; }, stopPropagation() { this.stopped = true; }, preventDefault() {} };
      (doc.listeners.click || []).filter(l => l.cap).forEach(l => l.f(ev));
      if (!ev.stopped) fire(target, 'click', ev);
    },
    doc
  };
  return B;
}
const realSpoken = B => B.spoken.filter(u => u.text.trim());

(async () => {
  // 1. tap the mic, ask, hear the answer
  {
    const B = browser();
    ok(!!B.voice, 'voice boots after concierge');
    const mic = B.voice.els.mic;
    ok(mic.className === 'nyv-mic' && mic.attrs['aria-label'] === 'Ask Nyla out loud', 'mic button is labelled', mic.attrs);
    B.click(mic);
    const rec = B.rec();
    ok(rec && rec.started === 1 && rec.lang === 'en-US' && rec.interimResults === true, 'mic tap starts recognition', rec);
    ok(B.panel.classList.contains('open'), 'mic tap opens the chat');
    ok(B.voice.state() === 'listening' && mic.attrs['aria-pressed'] === 'true', 'listening state shown', B.voice.state());
    ok(B.panel.classList.contains('nyv-listening') && B.bubble.classList.contains('nyv-listening'), 'listening animation classes');
    ok(/Listening/.test(B.voice.els.status.innerHTML), 'listening status line');
    ok(/mic/.test(B.text()) && /don’t record/.test(B.text()), 'privacy note on first use', B.text());
    ok(B.spoken.length === 1 && B.spoken[0].volume === 0, 'speech unlocked inside the tap (iOS)', B.spoken.map(u => u.text));
    rec.onstart();
    rec.onresult({ results: [Object.assign([{ transcript: 'cover at house' }], { isFinal: false })] });
    ok(B.input.value === 'cover at house', 'interim words show in the box', B.input.value);
    B.say(rec, 'cover at House of Yes');
    ok(B.users().some(u => /cover at House of Yes/.test(u)), 'the spoken question is shown as text', B.users());
    await B.run(1500);
    const said = realSpoken(B).map(u => u.text).join(' ');
    ok(/House of Yes/.test(said) && /Cover/.test(said), 'Nyla says the answer out loud', said);
    ok(!/night concierge|What kind of night/.test(said), 'greeting is not read out', said);
    ok(realSpoken(B).every(u => u.voice && u.voice.name === 'Samantha'), 'female voice chosen', realSpoken(B).map(u => u.voice && u.voice.name));
    ok(B.voice.state() === 'speaking' && B.panel.classList.contains('nyv-speaking'), 'speaking animation while audio plays', B.voice.state());
    ok(B.bots().some(m => /House of Yes/.test(m.innerHTML)), 'answer is also on screen');
    await B.finishSpeech();
    ok(B.voice.state() === 'idle' && !B.panel.classList.contains('nyv-speaking'), 'back to idle after speaking', B.voice.state());
    ok(!B.input.focused, 'voice turn does not pop the keyboard', B.input.focused);
    // typed follow-up is read out too now that voice is on
    const n = realSpoken(B).length;
    B.input.value = 'dress code at Le Bain';
    fire(B.form, 'submit', { preventDefault() {} });
    await B.run(1500);
    ok(realSpoken(B).length > n && /Le Bain/.test(realSpoken(B).slice(n).map(u => u.text).join(' ')), 'typed follow-up spoken while voice is on');
    // stop button
    B.click(B.voice.els.mic);
    ok(B.voice.state() === 'idle' && B.synth.cancelled, 'mic tap while speaking stops speech', B.voice.state());
  }

  // 2. typing-only visitors hear nothing
  {
    const B = browser();
    B.click(B.bubble);
    ok(B.panel.classList.contains('open'), 'tap on Nyla still opens chat');
    B.input.value = 'rooftops';
    fire(B.form, 'submit', { preventDefault() {} });
    await B.run(1500);
    ok(realSpoken(B).length === 0, 'no speech for typed chat unless voice is on', realSpoken(B).map(u => u.text));
    ok(B.voice.els.spk.attrs['aria-pressed'] === 'false', 'speaker shows off');
  }

  // 3. press and hold Nyla = push-to-talk
  {
    const B = browser({ voiceFirst: true });
    ok(!!B.voice, 'voice boots when loaded before concierge');
    fire(B.bubble, 'pointerdown', { button: 0 });
    await B.run(200);
    ok(B.recs.length === 0, 'no recognition before the hold time');
    await B.run(200);
    const rec = B.rec();
    ok(rec && rec.started === 1 && B.voice.state() === 'listening', 'holding starts listening', B.voice.state());
    ok(!B.panel.classList.contains('open'), 'chat stays closed while holding');
    const cap = B.doc.body.children.find(c => c.className === 'nyv-live');
    ok(!!cap && /Listening/.test(cap.innerHTML), 'listening caption over Nyla');
    rec.onstart();
    rec.onresult({ results: [Object.assign([{ transcript: 'is pdt 21+' }], { isFinal: true })] });
    (B.doc.listeners.pointerup || []).forEach(l => l.f({}));
    ok(rec.stopped === 1, 'letting go stops listening');
    B.click(B.bubble);
    rec.onend();
    await B.run(1500);
    ok(B.panel.classList.contains('open'), 'chat opens with the answer');
    ok(B.users().some(u => /is pdt 21\+/.test(u)), 'held question shown as text', B.users());
    ok(/Age and ID/.test(realSpoken(B).map(u => u.text).join(' ')), 'held question answered out loud', realSpoken(B).map(u => u.text));
    ok(!B.doc.body.children.some(c => c.className === 'nyv-live'), 'caption removed after release');
  }

  // 4. the click that ends a hold does not toggle the chat; a short tap does open it
  {
    const B = browser();
    fire(B.bubble, 'pointerdown', { button: 0 });
    await B.run(400);
    (B.doc.listeners.pointerup || []).forEach(l => l.f({}));
    B.click(B.bubble);
    ok(!B.panel.classList.contains('open'), 'release click after a hold is swallowed');
    B.rec().onend();
    const B2 = browser();
    fire(B2.bubble, 'pointerdown', { button: 0 });
    await B2.run(100);
    (B2.doc.listeners.pointerup || []).forEach(l => l.f({}));
    B2.click(B2.bubble);
    ok(B2.panel.classList.contains('open') && B2.recs.length === 0, 'short tap opens chat without the mic');
  }

  // 5. no speech recognition (Firefox, some in-app browsers): explain, still speak answers
  {
    const B = browser({ noSR: true });
    B.click(B.voice.els.mic);
    ok(/doesn’t work in this browser/.test(B.text()), 'unsupported browser gets a plain explanation', B.text());
    ok(B.voice.speakOn() === true, 'answers are still read out loud');
    B.input.value = 'no cover';
    fire(B.form, 'submit', { preventDefault() {} });
    await B.run(1500);
    ok(realSpoken(B).length > 0, 'typed question answered out loud without recognition');
  }

  // 6. API present but silent (events never fire): watchdog falls back
  {
    const B = browser();
    B.click(B.voice.els.mic);
    await B.run(5100);
    ok(B.rec().aborted === 1 && /doesn’t work in this browser/.test(B.text()) && B.voice.state() === 'idle', 'watchdog catches a dead recognizer', B.voice.state());
    B.click(B.voice.els.mic);
    ok(B.recs.length === 1, 'and does not retry it');
  }

  // 7. mic blocked
  {
    const B = browser();
    B.click(B.voice.els.mic);
    const rec = B.rec();
    rec.onerror({ error: 'not-allowed' }); rec.onend();
    await B.run(100);
    ok(/mic is blocked/.test(B.text()) && B.voice.state() === 'idle' && B.users().length === 0, 'blocked mic explained, nothing asked', B.text());
    B.click(B.voice.els.mic);
    const r2 = B.rec();
    r2.onstart(); r2.onend();
    ok(/didn’t catch that/.test(B.text()), 'silence gets a retry hint');
  }

  // 8. mute sticks
  {
    const B = browser();
    B.click(B.voice.els.mic);
    B.say(B.rec(), 'rooftops');
    await B.run(1500);
    await B.finishSpeech();
    B.click(B.voice.els.spk);
    ok(B.voice.speakOn() === false && B.store.nyv_muted === '1', 'speaker button mutes');
    const n = realSpoken(B).length;
    B.click(B.voice.els.mic);
    B.say(B.rec(), 'no cover');
    await B.run(1500);
    ok(realSpoken(B).length === n, 'muted: voice questions are answered in text only');
    ok(B.bots().some(m => /no cover/i.test(m.innerHTML)), 'muted answer still on screen');
  }

  // 9. no speechSynthesis either: mic still works, speaker hidden
  {
    const B = browser({ noSynth: true });
    ok(B.voice.els.spk.style.display === 'none', 'speaker hidden without speechSynthesis');
    B.click(B.voice.els.mic);
    B.say(B.rec(), 'bushwick clubs');
    await B.run(1500);
    ok(B.bots().some(m => /House of Yes/.test(m.innerHTML)), 'voice question answered in text');
  }

  // 10. v1.1 recorder fallback, only when a transcribe URL is configured
  {
    const B = browser({ noSR: true, recorder: true, config: { transcribeUrl: 'https://voice.example/stt' }, transcript: 'cover at House of Yes' });
    B.click(B.voice.els.mic);
    await B.run(10);
    ok(B.voice.state() === 'listening' && B.ctx.lastRecorder && B.ctx.lastRecorder.on, 'recorder starts when configured', B.voice.state());
    B.click(B.voice.els.mic);
    await B.run(1500);
    ok(B.posted.length === 1 && B.posted[0].url === 'https://voice.example/stt' && B.posted[0].init.headers['Content-Type'] === 'audio/mp4', 'clip posted to the Worker', B.posted.map(p => p.url));
    ok(B.users().some(u => /cover at House of Yes/.test(u)), 'Worker transcript asked through Nyla', B.users());
  }

  console.log(`${passes} passed, ${fails} failed`);
  process.exit(fails ? 1 : 0);
})().catch(e => { console.log('FAIL crashed', e && e.stack); process.exit(1); });
