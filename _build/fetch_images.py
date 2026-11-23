"""Download licensed photos once into _build/img/<slug>.jpg (the masters).

Sources, in the order we look for them: Wikimedia Commons (any CC or public-domain
file) and Flickr photos whose page shows a CC BY or CC BY-SA licence. Every photo's
author, licence and file page sit next to its URL in the venue JSON (or in
data/place_photos.json) and are printed on /image-credits.html.

Run: python _build/fetch_images.py   (from the site folder), then make_images.py.
Skips files already present. Re-run with --force to download again.
"""
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
IMG = ROOT / "img"
UA = "NYNightlifeImageFetcher/1.1 (hello@nynightlife.com)"
FLICKR = re.compile(r"^https://live\.staticflickr\.com/\d+/\d+_[0-9a-f]+(_[a-z])?\.jpg$")


def source_url(url):
    """A Commons file page, FilePath or upload URL becomes a 1280px FilePath URL.
    A Flickr static URL is used as is. Anything else is refused."""
    if FLICKR.match(url or ""):
        return url
    if "wikimedia" not in (url or ""):
        return None
    if "upload.wikimedia.org" in url:
        name = urllib.parse.unquote(url.rstrip("/").split("/")[-1])
    else:
        m = re.search(r"(?:File:|Special:FilePath/)([^?#]+)", urllib.parse.unquote(url))
        if not m:
            return None
        name = m.group(1)
    name = name.replace(" ", "_")
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(name) + "?width=1280"


def fetch(slug, url, force=False):
    dest = IMG / f"{slug}.jpg"
    if dest.exists() and dest.stat().st_size > 5000 and not force:
        return "cached"
    src = source_url(url)
    if not src:
        return "skip (not Commons or Flickr)"
    req = urllib.request.Request(src, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        ctype = r.headers.get("Content-Type", "")
        data = r.read()
    if not ctype.startswith("image/") or len(data) < 5000:
        return f"rejected ({ctype}, {len(data)} bytes)"
    if ctype != "image/jpeg":  # PNG and friends become a JPEG master
        import io
        from PIL import Image
        buf = io.BytesIO()
        Image.open(io.BytesIO(data)).convert("RGB").save(buf, "JPEG", quality=92)
        data = buf.getvalue()
    dest.write_bytes(data)
    time.sleep(1)
    return f"ok {len(data) // 1024} KB"


def jobs():
    out = []
    for f in sorted((ROOT / "data" / "venues").glob("*.json")):
        v = json.loads(f.read_text(encoding="utf-8"))
        url = (v.get("photo") or {}).get("url")
        if url:
            out.append((v["slug"], url))
    for f in sorted((ROOT / "data" / "playbooks").glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        out.append((p["slug"], p["photo"]["url"]))
    places = ROOT / "data" / "place_photos.json"
    if places.exists():
        for key, p in json.loads(places.read_text(encoding="utf-8"))["places"].items():
            out.append((key, p["url"]))
    out.append(("home", "https://commons.wikimedia.org/wiki/File:East_Village_Sidewalk_After_Dark_(New_York,_NY)_(5720189120).jpg"))
    return out


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    force = "--force" in sys.argv
    bad = 0
    for slug, url in jobs():
        try:
            res = fetch(slug, url, force)
        except Exception as ex:  # report and continue
            res = f"ERROR {ex}"
        if not (res == "cached" or res.startswith("ok")):
            bad += 1
        print(slug, res)
    if bad:
        sys.exit(f"{bad} photo(s) did not download")


if __name__ == "__main__":
    main()
