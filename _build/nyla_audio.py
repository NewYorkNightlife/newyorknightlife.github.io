"""Nyla's voice: pre-render every sentence she can say as a static MP3.

Run after build.py:  python _build/nyla_audio.py [--budget SECONDS] [--jobs N]

1. node _build/nyla_lines.js lists every sentence Nyla can speak (the real rules engine and
   the real speechText()/segments() from js/nyla-voice.js, over data/venues.json).
2. Each sentence is normalized (norm(), the twin of normalizeSpeech() in nyla-voice.js) and
   named by the SHA-1 of its UTF-8 bytes: audio/nyla/<sha1>.mp3.
3. Missing files are rendered with Kokoro-82M (kokoro-v1.0.int8.onnx, the q8 model), voice
   af_heart, 24 kHz, encoded as 48 kbps mono MP3. Existing files are kept as they are.
4. Files no sentence uses any more are deleted, and audio/nyla/manifest.json is rewritten
   with only the files that exist. The browser plays an answer only if every one of its
   sentences is in the manifest; otherwise it answers in text only.
--budget caps rendering time so a big feed change can't stall the deploy; what's left is
rendered on the next run (the workflow caches audio/nyla between runs).
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audio" / "nyla"
LINES = ROOT / "_build" / "data" / "nyla_audio_lines.json"
VOICE = "af_heart"
LANG = "en-us"
BITRATE = 48
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
MODEL_FILES = {
    "kokoro-v1.0.int8.onnx": "6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb",
    "voices-v1.0.bin": "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
}
MODEL_DIR = Path(os.environ.get("NYLA_KOKORO_DIR") or Path.home() / ".cache" / "nyla-kokoro")

# Twin of normalizeSpeech() in js/nyla-voice.js. Keep both in step (test_nyla_audio.py checks).
_WS = re.compile("[ \t\n\r\f\v\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+")
_SQ = str.maketrans({c: "'" for c in "\u2018\u2019\u201a\u201b\u2032"})
_DQ = str.maketrans({c: '"' for c in "\u201c\u201d\u201e\u201f\u2033"})


def norm(text):
    s = unicodedata.normalize("NFKC", str(text or ""))
    s = s.translate(_SQ).translate(_DQ)
    return _WS.sub(" ", s).strip(" ")


def sha1(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def sentences(site=ROOT):
    r = subprocess.run(["node", str(ROOT / "_build" / "nyla_lines.js"), str(site)],
                       capture_output=True, text=True, check=False)
    if r.returncode:
        sys.exit("nyla_lines.js failed:\n" + r.stderr[-2000:])
    d = json.loads(r.stdout)
    return d, sorted({norm(s) for s in d["sentences"] if norm(s)})


def ensure_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name, want in MODEL_FILES.items():
        p = MODEL_DIR / name
        if p.exists() and _sha256(p) == want:
            continue
        print(f"nyla audio: downloading {name}", flush=True)
        tmp = p.with_suffix(".part")
        urllib.request.urlretrieve(MODEL_URL + name, tmp)
        got = _sha256(tmp)
        if got != want:
            tmp.unlink()
            sys.exit(f"{name}: sha256 {got} does not match the pinned {want}")
        tmp.replace(p)
    return MODEL_DIR / "kokoro-v1.0.int8.onnx", MODEL_DIR / "voices-v1.0.bin"


def _sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


_TTS = None


def _init(model, voices, threads):
    global _TTS
    import onnxruntime as rt
    from kokoro_onnx import Kokoro
    so = rt.SessionOptions()
    so.intra_op_num_threads = threads
    so.inter_op_num_threads = 1
    sess = rt.InferenceSession(str(model), so, providers=["CPUExecutionProvider"])
    _TTS = Kokoro.from_session(sess, str(voices))


def _render(text):
    import lameenc
    import numpy as np
    audio, sr = _TTS.create(text, voice=VOICE, speed=1.0, lang=LANG)
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2").tobytes()
    enc = lameenc.Encoder()
    enc.set_bit_rate(BITRATE)
    enc.set_in_sample_rate(sr)
    enc.set_channels(1)
    enc.set_quality(2)
    mp3 = enc.encode(pcm) + enc.flush()
    return text, mp3, round(len(audio) / sr, 2)


def mp3_seconds(p):
    """Duration of one of our CBR files without decoding it (bytes / bitrate)."""
    return round(p.stat().st_size * 8 / (BITRATE * 1000), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=float(os.environ.get("NYLA_AUDIO_BUDGET", 900)),
                    help="seconds of rendering before stopping (rest is text-only until the next run)")
    ap.add_argument("--jobs", type=int, default=0, help="worker processes (default: cores // 2)")
    ap.add_argument("--no-render", action="store_true", help="only prune and rewrite the manifest")
    a = ap.parse_args()

    t0 = time.time()
    info, lines = sentences()
    want = {sha1(s): s for s in lines}
    OUT.mkdir(parents=True, exist_ok=True)
    have = {p.stem for p in OUT.glob("*.mp3")}

    pruned = 0
    for h in sorted(have - set(want)):
        (OUT / f"{h}.mp3").unlink()
        pruned += 1
    todo = [want[h] for h in sorted(set(want) - have)]
    print(f"nyla audio: {len(lines)} sentences from {info['answers']} answers "
          f"({info['moments']} tonight moments); {len(want) - len(todo)} cached, {len(todo)} to render, "
          f"{pruned} pruned", flush=True)

    rendered = 0
    durations = {}
    if todo and not a.no_render:
        model, voices = ensure_model()
        cores = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 2)
        jobs = a.jobs or max(1, cores // 2)
        threads = max(1, cores // jobs)
        deadline = time.time() + a.budget
        with cf.ProcessPoolExecutor(jobs, initializer=_init, initargs=(model, voices, threads)) as ex:
            pending = set()
            it = iter(todo)
            def feed():
                for s in it:
                    pending.add(ex.submit(_render, s))
                    if len(pending) >= jobs * 2:
                        return
            feed()
            while pending:
                done, _ = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
                for f in done:
                    pending.discard(f)
                    text, mp3, secs = f.result()
                    h = sha1(text)
                    tmp = OUT / f"{h}.part"
                    tmp.write_bytes(mp3)
                    tmp.replace(OUT / f"{h}.mp3")
                    durations[h] = secs
                    rendered += 1
                    if rendered % 100 == 0:
                        print(f"nyla audio: {rendered}/{len(todo)} rendered", flush=True)
                if time.time() < deadline:
                    feed()
            left = len(todo) - rendered
            if left:
                print(f"nyla audio: budget of {a.budget:.0f}s reached, {left} sentences stay text-only until the next run")

    files = {}
    total = 0
    for h in sorted(want):
        p = OUT / f"{h}.mp3"
        if not p.exists():
            continue
        size = p.stat().st_size
        total += size
        files[h] = [durations.get(h, mp3_seconds(p)), size]
    manifest = {
        "version": 1, "voice": VOICE, "model": "kokoro-v1.0.int8.onnx", "format": f"mp3 {BITRATE}kbps mono",
        "count": len(files), "bytes": total, "files": files,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, separators=(",", ":"), sort_keys=True) + "\n")
    LINES.parent.mkdir(parents=True, exist_ok=True)
    LINES.write_text(json.dumps({h: want[h] for h in sorted(want)}, ensure_ascii=False, indent=0, sort_keys=True) + "\n")
    missing = len(want) - len(files)
    print(f"nyla audio: {len(files)} files, {total / 1e6:.1f} MB, {rendered} rendered, {missing} missing, "
          f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
