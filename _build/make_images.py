"""Make the responsive image set the pages ask for.

Masters live in `_build/img/<slug>.jpg` (full quality, as downloaded by
fetch_images.py). This writes the derivatives the templates reference into
`_build/img/gen/`, and `build.py copy_static()` copies that folder to `/img/`.

For every master <slug>.jpg it writes:
    <slug>.jpg          1280w progressive JPEG, the <picture> fallback
    <slug>-640.webp     phone
    <slug>-960.webp     tablet / 1x desktop
    <slug>-1280.webp    2x
    <slug>-thumb.webp   176x176 square crop, for the venue cards
    <slug>-thumb.jpg    same, fallback

It also writes _build/img/dims.json (committed) so build.py can set width and
height on every image without needing the generated files present.

Run:  python _build/make_images.py        (from the site folder)
It is safe to re-run: it only rewrites a derivative when the master is newer.
"""
import json
import pathlib
import sys

from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "img"
GEN = SRC / "gen"
WIDTHS = (640, 960, 1280)
THUMB = 176
JPEG_Q = 78
WEBP_Q = 72


def newer(master, *targets):
    if not all(t.exists() for t in targets):
        return True
    m = master.stat().st_mtime
    return any(t.stat().st_mtime < m for t in targets)


def build(master):
    slug = master.stem
    out = {}
    im = ImageOps.exif_transpose(Image.open(master)).convert("RGB")
    w, h = im.size

    fallback = GEN / f"{slug}.jpg"
    wide = [GEN / f"{slug}-{n}.webp" for n in WIDTHS]
    thumbs = [GEN / f"{slug}-thumb.webp", GEN / f"{slug}-thumb.jpg"]
    if not newer(master, fallback, *wide, *thumbs):
        return None

    big = im if w <= 1280 else im.resize((1280, round(h * 1280 / w)), Image.LANCZOS)
    big.save(fallback, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
    out[fallback.name] = fallback.stat().st_size

    for n, dst in zip(WIDTHS, wide):
        v = im if w <= n else im.resize((n, round(h * n / w)), Image.LANCZOS)
        v.save(dst, "WEBP", quality=WEBP_Q, method=6)
        out[dst.name] = dst.stat().st_size

    sq = ImageOps.fit(im, (THUMB, THUMB), Image.LANCZOS, centering=(0.5, 0.45))
    sq.save(thumbs[0], "WEBP", quality=WEBP_Q, method=6)
    sq.save(thumbs[1], "JPEG", quality=JPEG_Q, optimize=True)
    for t in thumbs:
        out[t.name] = t.stat().st_size
    return out


def main():
    GEN.mkdir(parents=True, exist_ok=True)
    masters = sorted(p for p in SRC.glob("*.jpg"))
    if not masters:
        sys.exit(f"no masters in {SRC}")
    sizes, made = {}, 0
    for m in masters:
        r = build(m)
        if r:
            made += 1
            sizes.update(r)
            print(f"  {m.stem}: " + ", ".join(f"{k.split('-')[-1]} {v // 1024}kB" for k, v in r.items()))
    # the sizes the templates need for width/height, so pages never shift on load
    dims = {}
    for m in masters:
        with Image.open(m) as im:
            w, h = ImageOps.exif_transpose(im).size
        dims[m.stem] = [min(w, 1280), round(h * min(w, 1280) / w)]
    (SRC / "dims.json").write_text(json.dumps(dims, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    total = sum(p.stat().st_size for p in GEN.iterdir() if p.is_file())
    print(f"{made} of {len(masters)} masters rebuilt; {len(list(GEN.iterdir()))} files, {total // 1024} kB in {GEN}")


if __name__ == "__main__":
    main()
