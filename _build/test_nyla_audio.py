"""Tests for Nyla's pre-rendered voice (_build/nyla_audio.py + js/nyla-voice.js).

Run after build.py and nyla_audio.py:  python _build/test_nyla_audio.py [--strict]

- every manifest entry has its MP3, with the size the manifest says, and every MP3 is listed
- every file name is the SHA-1 of a sentence Nyla can say right now (nothing stale)
- the browser (normalizeSpeech + sha1 in nyla-voice.js) and the build (norm + sha1 in
  nyla_audio.py) give the same hash for the same text, including quotes, dashes, emoji,
  non-breaking spaces and accents
- sample answers from the real rules engine resolve to files that exist
--strict also fails if any current sentence has no file (the workflow runs it without, since
a render budget can leave a few sentences for the next run; those answers are text-only).
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyla_audio as A  # noqa: E402

ROOT = A.ROOT
fails = []


def ok(cond, name, extra=""):
    if not cond:
        fails.append(name)
        print("FAIL", name, str(extra)[:400])


def node(js):
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        raise SystemExit("node failed: " + r.stderr[-1500:])
    return json.loads(r.stdout)


strict = "--strict" in sys.argv
man_path = A.OUT / "manifest.json"
ok(man_path.exists(), "manifest exists", man_path)
man = json.loads(man_path.read_text()) if man_path.exists() else {"files": {}}
files = man.get("files", {})
ok(man.get("version") == 1 and man.get("voice") == "af_heart", "manifest header", {k: man.get(k) for k in ("version", "voice")})
ok(man.get("count") == len(files), "manifest count matches", (man.get("count"), len(files)))

total = 0
for h, (secs, size) in files.items():
    p = A.OUT / f"{h}.mp3"
    if not p.exists():
        ok(False, "manifest entry has its file", h)
        continue
    b = p.read_bytes()
    total += len(b)
    ok(len(b) == size, "file size matches manifest", (h, len(b), size))
    ok(b[:3] == b"ID3" or (b[0] == 0xFF and (b[1] & 0xE0) == 0xE0), "file is an MP3", h)
    ok(0 < secs < 60, "sane duration", (h, secs))
ok(man.get("bytes") == total, "manifest byte total", (man.get("bytes"), total))
on_disk = {p.stem for p in A.OUT.glob("*.mp3")}
ok(on_disk == set(files), "no unlisted MP3s", sorted(on_disk ^ set(files))[:5])

# every file is a current sentence
info, lines = A.sentences()
want = {A.sha1(s): s for s in lines}
ok(set(files) <= set(want), "no stale files", sorted(set(files) - set(want))[:5])
missing = sorted(set(want) - set(files))
cover = 1 - len(missing) / max(1, len(want))
print(f"coverage: {len(want) - len(missing)}/{len(want)} sentences have audio ({cover:.1%})")
if strict:
    ok(not missing, "every sentence has audio (--strict)", [want[h] for h in missing[:5]])
ok(len(want) > 200, "corpus is not empty", len(want))

# JS and Python agree
SAMPLES = [
    "", "Age: 21 plus.", "Hey I’m Nyla.", "“Quoted” and ‘single’", "Cover: $20 to $40; free before 10pm (1 source).",
    "Café Erzulie — Bushwick", "  lots \u00a0 of\tspace\n", "ﬁ ligature and ＦＵＬＬＷＩＤＴＨ", "e\u0301 combining",
    "Jacqueline Novak Tue 7:00 PM at The Bell House.", "🥂 emoji stays if it gets here", "M.E.A.T. Thu 8:00 PM at Le Bain.",
]
js = node("const V=require('./_build/nyla-voice.js');const S=" + json.dumps(SAMPLES) +
          ";process.stdout.write(JSON.stringify(S.map(s=>[V.normalizeSpeech(s),V.sha1(V.normalizeSpeech(s))])))")
for s, (jn, jh) in zip(SAMPLES, js):
    pn = A.norm(s)
    ok(jn == pn, "normalize agrees", (s, jn, pn))
    ok(jh == A.sha1(pn), "sha1 agrees", (s, jh, A.sha1(pn)))
    ok(A.norm(pn) == pn, "normalize is idempotent", s)

# the lines index matches its hashes
idx = json.loads(A.LINES.read_text()) if A.LINES.exists() else {}
ok(all(A.sha1(A.norm(t)) == h for h, t in idx.items()), "lines index hashes match", "")

# real answers resolve to real files
plans = node(r"""
const fs=require('fs'),V=require('./_build/nyla-voice.js');
const d=JSON.parse(fs.readFileSync('data/venues.json','utf8')),m=JSON.parse(fs.readFileSync('audio/nyla/manifest.json','utf8'));
const v=d.venues.find(x=>x.status!=='closed')||d.venues[0];
const card='<b>'+v.name+'</b> ('+v.hood+')<br><b>Cover:</b> '+v.cover+'<br><b>Dress:</b> '+v.dress+'<br><b>Age:</b> '+v.age+'<br><a href="/x">Sources →</a>';
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const card2='<b>'+esc(v.name)+'</b> ('+esc(v.hood)+')<br><b>Cover:</b> '+esc(v.cover)+'<br><b>Dress:</b> '+esc(v.dress)+'<br><b>Age:</b> '+esc(v.age)+'<br><a href="/x">Sources &amp; full facts →</a>';
const p=V.audioPlan(card2,m,'/audio/nyla/');
const miss=V.audioPlan('<b>Zzz</b> a sentence nobody wrote.',m,'/audio/nyla/');
process.stdout.write(JSON.stringify({p:p,miss:miss,base:V.audioBase('https://nynightlife.com/js/nyla-voice.js?v=1'),base2:V.audioBase('https://x.github.io/repo/js/nyla-voice.js')}));
""")
ok(plans["p"] and all((A.OUT / Path(x["url"]).name).exists() for x in plans["p"]), "a venue card resolves to files", plans["p"])
ok(plans["miss"] is None, "an unknown answer is text-only", plans["miss"])
ok(plans["base"] == "https://nynightlife.com/audio/nyla/" and plans["base2"] == "https://x.github.io/repo/audio/nyla/", "audio base follows the script", plans)

print(f"{'FAILED' if fails else 'ok'}: {len(fails)} failures; {len(files)} files, {total / 1e6:.1f} MB")
sys.exit(1 if fails else 0)
