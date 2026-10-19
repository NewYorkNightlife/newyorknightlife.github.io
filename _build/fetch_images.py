"""Download licensed (Wikimedia Commons, CC) photos once into ../next/img/ so pages self-host them.

Run: python nextsrc/fetch_images.py   (from the site folder). Skips files already present.
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
IMG = ROOT / "img"
UA = "NYNightlifeImageFetcher/1.0 (hello@nynightlife.com)"


def filepath_url(url):
    """Turn a Commons file page or FilePath URL into a 1200px FilePath URL."""
    if "wikimedia" not in url:
        return None
    if "upload.wikimedia.org" in url:
        name = urllib.parse.unquote(url.rstrip("/").split("/")[-1])
    else:
        m = re.search(r"(?:File:|Special:FilePath/)([^?#]+)", urllib.parse.unquote(url))
        if not m:
            return None
        name = m.group(1)
    name = name.replace(" ", "_")
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(name) + "?width=1200"


def fetch(slug, url):
    dest = IMG / f"{slug}.jpg"
    if dest.exists() and dest.stat().st_size > 5000:
        return "cached"
    src = filepath_url(url)
    if not src:
        return "skip (not Commons)"
    req = urllib.request.Request(src, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        ctype = r.headers.get("Content-Type", "")
        data = r.read()
    if not ctype.startswith("image/") or len(data) < 5000:
        return f"rejected ({ctype}, {len(data)} bytes)"
    dest.write_bytes(data)
    time.sleep(1)
    return f"ok {len(data) // 1024} KB"


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    jobs = []
    for f in sorted((ROOT / "data" / "venues").glob("*.json")):
        v = json.loads(f.read_text(encoding="utf-8"))
        url = (v.get("photo") or {}).get("url")
        if url:
            jobs.append((v["slug"], url))
    for f in sorted((ROOT / "data" / "playbooks").glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        jobs.append((p["slug"], p["photo"]["url"]))
    jobs.append(("home", "https://commons.wikimedia.org/wiki/File:East_Village_Sidewalk_After_Dark_(New_York,_NY)_(5720189120).jpg"))
    for slug, url in jobs:
        try:
            print(slug, fetch(slug, url))
        except Exception as ex:  # report and continue
            print(slug, "ERROR", ex)


if __name__ == "__main__":
    main()
