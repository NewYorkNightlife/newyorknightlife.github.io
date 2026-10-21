"""Draw the 1200x630 share card for every page, in the Ledger design.

Why this exists: a link pasted into iMessage, WhatsApp or Slack is this site's
most likely way of travelling. Before this, there was no card at all, and the
only candidate was a pre-rebuild `assets/og-default.jpg` claiming "VERIFIED
WEEKLY", which is not true: every venue was checked once, on its own date.

Each card carries only facts already on the page: the venue name, its
neighbourhood and type, its dress-code answer, its status when that status is
closed or unclear, and the date it was checked. Nothing is invented. Venues we
hold a licensed photograph of get the photograph behind the same scrim the page
uses; the rest get the same drawn cover as their page, so a card can never
imply a picture of a room we have no picture of.

Run:  python _build/make_og.py        (from the site folder)
Writes _build/img/og/<slug>.jpg plus site.jpg (the fallback). build.py copies
them to /img/og/.
"""
import hashlib
import json
import pathlib
import re
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "img" / "og"
FONTS = ROOT / "fonts-src"
W, H = 1200, 630
PAD = 72

INK, INK2, INK3 = (11, 9, 8), (23, 19, 15), (34, 28, 23)
CREAM, BRONZE, BRONZE_LT, MUTED = (237, 231, 222), (192, 143, 82), (217, 168, 106), (181, 171, 160)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def track(d, xy, text, f, fill, sp=0):
    """Draw text with letter-spacing, and return the width used."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + sp
    return x - xy[0]


def wrap(d, text, f, maxw, lines=2):
    out, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            out.append(cur)
            cur = word
            if len(out) == lines:
                break
    if cur and len(out) < lines:
        out.append(cur)
    return out


def gradient(size, top, bottom):
    g = Image.new("RGB", (1, size[1]))
    for y in range(size[1]):
        t = y / max(size[1] - 1, 1)
        g.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return g.resize(size, Image.BILINEAR)


def pattern_of(slug):
    return int(hashlib.md5(slug.encode()).hexdigest(), 16) % 6 + 1


def initial_of(name):
    for c in re.sub(r"^(the|a)\s+", "", name.strip(), flags=re.I):
        if c.isalnum():
            return c.upper()
    return "N"


def draw_pattern(im, n):
    """The same six covers the CSS draws, at card scale."""
    d = ImageDraw.Draw(im, "RGBA")
    c = (192, 143, 82, 34)
    if n == 1:
        for i in range(-H, W + H, 26):
            d.line([(i, 0), (i + H, H)], fill=c, width=2)
    elif n == 2:
        for y in range(0, H, 34):
            for x in range(0, W, 34):
                d.ellipse([x, y, x + 4, y + 4], fill=(192, 143, 82, 58))
    elif n == 3:
        for r in range(40, 1500, 52):
            d.ellipse([W * 0.92 - r, 30 - r, W * 0.92 + r, 30 + r], outline=c, width=2)
    elif n == 4:
        for x in range(0, W, 52):
            d.line([(x, 0), (x, H)], fill=c, width=2)
    elif n == 5:
        for i in range(-H, W + H, 34):
            d.line([(i, 0), (i + H, H)], fill=(192, 143, 82, 26), width=2)
            d.line([(i, H), (i + H, 0)], fill=(192, 143, 82, 26), width=2)
    else:
        for y in range(0, H, 34):
            d.line([(0, y), (W, y)], fill=c, width=2)


def glow(im):
    """The bronze wash in the top-right corner, matching the CSS radial."""
    g = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(g)
    cx, cy, r = W * 0.88, -H * 0.10, W * 0.78
    for i in range(44):
        rr = r * (1 - i / 44)
        gd.ellipse([cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8], fill=int(76 * (i / 44) ** 1.6))
    im.paste(Image.new("RGB", (W, H), BRONZE), (0, 0), g)


def scrim(im):
    """Bottom- and left-weighted, the same shape as .plate.photo::after."""
    m = Image.new("L", (1, H))
    for y in range(H):
        t = y / (H - 1)
        m.putpixel((0, y), int(255 * max(0.06, min(0.94, 0.06 + 0.88 * t ** 1.6))))
    im.paste(Image.new("RGB", (W, H), INK), (0, 0), m.resize((W, H), Image.BILINEAR))
    m2 = Image.new("L", (W, 1))
    for x in range(W):
        m2.putpixel((x, 0), int(255 * 0.42 * max(0.0, 1 - x / (W * 0.58)) ** 1.4))
    im.paste(Image.new("RGB", (W, H), INK), (0, 0), m2.resize((W, H), Image.BILINEAR))


def card(slug, name, eyebrow, answer, checked, status=None, photo=None):
    if photo and photo.exists():
        src = ImageOps.exif_transpose(Image.open(photo)).convert("RGB")
        im = ImageOps.fit(src, (W, H), Image.LANCZOS, centering=(0.5, 0.42))
        scrim(im)
    else:
        im = gradient((W, H), INK3, INK)
        glow(im)
        draw_pattern(im, pattern_of(slug))
        d = ImageDraw.Draw(im, "RGBA")
        f = font("fraunces-600.ttf", 430)
        ch = initial_of(name)
        w = d.textlength(ch, font=f)
        # high and right, clear of both the title and the checked-date line
        d.text((W - w - 30, -62), ch, font=f, fill=(192, 143, 82, 46))

    d = ImageDraw.Draw(im, "RGBA")
    track(d, (PAD, 54), "NY NIGHTLIFE", font("isans-600.ttf", 25), (237, 231, 222, 205), 3.2)

    y = H - PAD - 34
    if answer:
        d.text((PAD, y), answer, font=font("isans-400.ttf", 30), fill=(214, 206, 195, 240))
    track(d, (W - PAD - track(ImageDraw.Draw(Image.new("RGB", (1, 1))), (0, 0), f"CHECKED {checked.upper()}",
                              font("isans-600.ttf", 21), (0, 0, 0), 1.6), y + 6),
          f"CHECKED {checked.upper()}", font("isans-600.ttf", 21), (181, 171, 160, 235), 1.6)

    title_f = font("fraunces-600.ttf", 92)
    lines = wrap(d, name, title_f, W - PAD * 2 - 40, lines=2)
    ty = y - 34 - len(lines) * 104
    for ln in lines:
        d.text((PAD, ty), ln, font=title_f, fill=CREAM)
        ty += 104

    ey = y - 34 - len(lines) * 104 - 46
    track(d, (PAD, ey), eyebrow.upper(), font("isans-600.ttf", 24), BRONZE_LT, 2.6)

    if status:
        sf = font("isans-600.ttf", 23)
        tw = track(ImageDraw.Draw(Image.new("RGB", (1, 1))), (0, 0), status.upper(), sf, (0, 0, 0), 2.0)
        d.rounded_rectangle([PAD, 110, PAD + tw + 34, 158], 12, fill=(192, 143, 82, 255))
        track(d, (PAD + 17, 121), status.upper(), sf, INK, 2.0)
    return im


def main():
    if not FONTS.exists():
        sys.exit(f"missing {FONTS} (needs fraunces-600.ttf, isans-600.ttf, isans-400.ttf)")
    OUT.mkdir(parents=True, exist_ok=True)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def fmt(iso):
        y, m, dd = iso.split("-")
        return f"{months[int(m) - 1]} {int(dd)}, {y}"

    n = 0
    for f in sorted((ROOT / "data" / "venues").glob("*.json")):
        v = json.loads(f.read_text(encoding="utf-8"))
        slug, st = v["slug"], v.get("status")
        master = ROOT / "img" / f"{slug}.jpg"
        ph = v.get("photo") or {}
        # a photo that shows the building, not the room, stays on its own page
        # under the caption that explains it, and never becomes the share card
        has = bool(ph.get("url")) and master.exists() and not ph.get("depicts")
        if st == "closed":
            answer, chip = "This venue has closed.", "Closed"
        else:
            dress = (v.get("dress") or {}).get("answer") or "Dress code not found yet"
            age = (v.get("age") or {}).get("value") or ""
            answer = f"Dress: {dress}" + (f"  ·  {age.split(';')[0].split(',')[0]}" if age else "")
            chip = "Status unclear" if st == "unclear" else None
        card(slug, v["name"], f"{v.get('neighborhood', '')} · {v.get('type', '')}",
             answer[:78], fmt(v.get("checked", "2026-10-18")), chip,
             master if has else None).save(OUT / f"{slug}.jpg", "JPEG", quality=82, optimize=True, progressive=True)
        n += 1

    checked = fmt(max(json.loads(f.read_text(encoding="utf-8")).get("checked", "2026-10-18")
                      for f in (ROOT / "data" / "venues").glob("*.json")))
    card("home", "Know before you go.", "New York City", "Dress code, age and cover, with sources.",
         checked, None, ROOT / "img" / "home.jpg").save(OUT / "site.jpg", "JPEG", quality=82, optimize=True, progressive=True)
    card("guide", "NYC dress codes", "The roundup", "What 29 bars and clubs say about the door.",
         checked, None, None).save(OUT / "guide.jpg", "JPEG", quality=82, optimize=True, progressive=True)
    for f in sorted((ROOT / "data" / "playbooks").glob("*.json")):
        pb = json.loads(f.read_text(encoding="utf-8"))
        card(pb["slug"], pb["title"], f"Group playbook · party of {pb['group']}",
             "Real listing prices, split per person.", fmt(pb["checked"]), None,
             ROOT / "img" / f"{pb['slug']}.jpg").save(OUT / f"{pb['slug']}.jpg", "JPEG", quality=82, optimize=True, progressive=True)
        n += 1
    total = sum(p.stat().st_size for p in OUT.glob("*.jpg"))
    big = [p.name for p in OUT.glob("*.jpg") if p.stat().st_size > 300_000]
    print(f"{n + 2} share cards, {total // 1024} kB total, largest {max(p.stat().st_size for p in OUT.glob('*.jpg')) // 1024} kB")
    if big:
        print("  over 300 kB (WhatsApp may skip the preview):", ", ".join(big))


if __name__ == "__main__":
    main()
