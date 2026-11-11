"""Build NY Nightlife v2 static pages into the site root (../).

Data:  _build/data/venues/*.json  (one per venue, fact-checked)
       _build/data/playbooks/*.json
Pages: generated from the templates in this file.
Images: masters in _build/img/, responsive copies in _build/img/gen/ (make_images.py).
Run:   python _build/make_images.py   (only after adding or replacing a photo)
       python _build/build.py         (from the site folder)
       node _build/test_nyla.js .     (Nyla's answer tests; run it 3 times)
"""
import hashlib
import html
import json
import os
import pathlib
import posixpath
import re
import urllib.parse

import affiliates
import events
import extras
import present

ROOT = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(os.environ.get("NYN_OUT", ROOT.parent))  # the live site root
SITE = "https://nynightlife.com"
BASE = os.environ.get("NYN_BASE", "")  # path prefix for test builds; "" for the live site
RELATIVE = os.environ.get("NYN_RELATIVE") == "1"  # relative links for the private preview
CHECKED_FMT = "%b %-d, %Y"
SITE_EDITED = "2026-11-11"   # the day the fixed pages themselves last changed
def _ver(p):
    """Cache-bust from the file's own content, so it can never be forgotten.
    CRLF is normalised because git's autocrlf makes working copies differ."""
    return hashlib.md5(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:8] if p.exists() else "0"
GEN = ROOT / "img" / "gen"
_DIMS_F = ROOT / "img" / "dims.json"
DIMS = json.loads(_DIMS_F.read_text(encoding="utf-8")) if _DIMS_F.exists() else {}
CSS_V = _ver(ROOT / "site.css")
JS_V = _ver(ROOT / "concierge.js")
LIVE_V = _ver(ROOT / "live.js")
SIGNAL_V = _ver(ROOT / "signal.js")
OG_DIR = ROOT / "img" / "og"
OG_DEFAULT = "/img/og/site.jpg"

e = html.escape


def u(path):
    return BASE + path


def fmt_date(iso):
    y, m, d = iso.split("-")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[int(m) - 1]} {int(d)}, {y}"


# ---------------------------------------------------------------- shell

def head(title, desc, path, schema=None, robots="index,follow", image=None, img_alt=None):
    items = [s for s in (schema if isinstance(schema, list) else [schema]) if s] if schema else []
    ld = "\n".join(
        f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in items)
    img = SITE + (image or OG_DEFAULT)
    img_alt = img_alt or "NY Nightlife \u2014 know before you go"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:site_name" content="NY Nightlife">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{e(img)}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(img_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(img)}">
<meta name="twitter:image:alt" content="{e(img_alt)}">
<meta name="theme-color" content="#05070C">
<link rel="preload" as="font" type="font/woff2" crossorigin href="{u('/fonts/instrument-sans-normal-400_700-latin.woff2')}">
<link rel="preload" as="font" type="font/woff2" crossorigin href="{u('/fonts/fraunces-normal-600-latin.woff2')}">
<link rel="stylesheet" href="{u('/css/site.css')}?v={CSS_V}">
<link rel="stylesheet" href="{u('/css/concierge.css')}">
<script defer src="{u('/js/concierge.js')}?v={JS_V}"></script>
<script defer src="{u('/analytics.js')}"></script>
{ld}
</head>
"""


MENU = [("/tonight/", "Tonight"), ("/venues/", "Venues"), ("/guides/nyc-dress-codes.html", "Dress codes"),
        ("/plans/", "Group nights"), ("/plans/nyc-dinner-cruises.html", "Cruises"),
        ("/how-we-check.html", "How we check")]


def header():
    def link(p, t):
        extra = " nav-wide" if p == "/plans/nyc-dinner-cruises.html" else ""
        return f'<a class="txt{extra}" href="{u(p)}">{e(t)}</a>'
    links = "".join(link(p, t) for p, t in MENU)
    panel = "".join(f'<a href="{u(p)}">{e(t)}</a>' for p, t in MENU)
    return f"""<header class="site-head"><div class="wrap">
<a class="wordmark" href="{u('/')}">NY Nightlife</a>
<nav class="head-nav" aria-label="Main">{links}
<details class="menu"><summary class="icon-btn" aria-label="Menu"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></summary>
<div class="panel">{panel}</div></details>
</nav></div></header>
"""


def footer():
    return f"""<footer class="site-foot"><div class="wrap">
<nav aria-label="Footer"><a href="{u('/plans/nyc-dinner-cruises.html')}">Dinner cruises</a><a href="{u('/guides/nyc-bar-closing-time.html')}">Closing time</a><a href="{u('/guides/under-21-nyc-bars-clubs.html')}">Under 21</a><a href="{u('/changes/')}">What changed</a><a href="{u('/about.html')}">About</a><a href="{u('/how-we-check.html')}">How we check</a><a href="{u('/affiliate-disclosure.html')}">Affiliate disclosure</a><a href="{u('/privacy.html')}">Privacy</a><a href="{u('/contact.html')}">Contact</a></nav>
<p>NY Nightlife is an independent guide. Facts are checked against the sources listed on each page; always confirm with the venue before you go. 21+ venues are for adults of legal drinking age. We may earn a commission when you book through links on this site, at no extra cost to you. Concert, comedy, theatre, and nightlife listings from Ticketmaster, when shown, are refreshed daily and the ticket link is that event's page.</p>
<nav aria-label="More"><a href="{u('/image-credits.html')}">Image credits</a><a href="{u('/llms.txt')}">llms.txt</a></nav>
</div></footer>
"""


def actions(buttons, disclose=None, side_title=None):
    d = f'<p class="disclose">{disclose}</p>' if disclose else ""
    t = f'<p class="side-title">{e(side_title)}</p>' if side_title else ""
    return f'<div class="actions" role="region" aria-label="Actions"><div class="wrap">{t}{buttons}{d}</div></div>'


def _auto_crumbs(path, label):
    if path in ("/", "/index.html"):
        return [("Home", "/")]
    crumbs = [("Home", "/")]
    if path.startswith("/venues/") and path != "/venues/":
        crumbs.append(("Venues", "/venues/"))
    elif path.startswith("/plans/"):
        crumbs.append(("Group nights", "/plans/"))
    elif path.startswith("/guides/"):
        crumbs.append(("Guides", "/guides/nyc-dress-codes.html"))
    if not crumbs or crumbs[-1][1] != path:
        crumbs.append((label, path))
    return crumbs


def page(title, desc, path, body, schema=None, body_class="", robots="index,follow", image=None, img_alt=None,
         crumbs=None, updated=None, crumb_label=None):
    label = crumb_label or title.split("|")[0].strip()
    trail = _auto_crumbs(path, label) if crumbs is None else crumbs
    blocks = [s for s in (schema if isinstance(schema, list) else [schema]) if s] if schema else []
    if trail:
        blocks.append(present.breadcrumb_schema(trail))
    crumb_html = "" if path in ("/", "/index.html") else present.crumbs_html(trail)
    upd = f'<p class="updated">Updated {e(updated)}</p>' if updated else ""
    signal = f'<script defer src="{u("/js/signal.js")}?v={SIGNAL_V}"></script>\n'
    return (head(title, desc, path, blocks, robots, image, img_alt) +
            f'<body class="{body_class}">\n<div class="lamp" aria-hidden="true"></div>\n' + header() +
            f'<main class="wrap">\n{upd}{crumb_html}\n{body}\n</main>\n' + footer() + signal + "</body>\n</html>\n")


def _rel(m, here):
    attr, target = m.group(1), m.group(2)
    t, _, frag = target.partition("#")
    if t.endswith("/"):
        t += "index.html"
    r = posixpath.relpath(t, posixpath.dirname(here)) if t else ""
    return f'{attr}="{r}{"#" + frag if frag else ""}"'


def write(path, text):
    if RELATIVE:
        here = path if not path.endswith("/") else path + "index.html"
        text = re.sub(r'(href|src)="(/(?!/)[^"]*)"', lambda m: _rel(m, here), text)
    p = OUT / path.lstrip("/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- imagery
# A venue page shows a photograph only when we hold a correctly-licensed one.
# The other venues get a cover drawn in CSS from their own slug and initial:
# it costs no bytes, it is stable between builds, and it can never be mistaken
# for a picture of the room.
SIZES_PLATE = ("(min-width: 1340px) 1116px, (min-width: 1040px) 1016px, "
               "(min-width: 796px) 724px, calc(100vw - 36px)")


def pattern_of(slug):
    return int(hashlib.md5(slug.encode()).hexdigest(), 16) % 6 + 1


def initial_of(name):
    for c in re.sub(r"^(the|a)\s+", "", name.strip(), flags=re.I):
        if c.isalnum():
            return c.upper()
    return "N"


def has_photo(v):
    return bool((v.get("photo") or {}).get("url")) and (ROOT / "img" / (v["slug"] + ".jpg")).exists()


def shows_the_venue(v):
    """True only where the photograph is of the place itself. The others stay
    on their own page, under the caption that says what they really show."""
    return has_photo(v) and not (v.get("photo") or {}).get("depicts")


def picture(slug, alt, sizes, eager=False):
    w, h = DIMS.get(slug, [1280, 853])
    srcset = ", ".join(f'{u("/img/" + slug + "-" + str(n) + ".webp")} {n}w' for n in (640, 960, 1280))
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<picture><source type="image/webp" srcset="{srcset}" sizes="{sizes}">'
            f'<img src="{u("/img/" + slug + ".jpg")}" alt="{e(alt)}" width="{w}" height="{h}" '
            f'{load} decoding="async"></picture>')


def plate(slug, name, eyebrow, title=None, credit=None, alt=None, style=""):
    """The title block. `credit` (already-escaped HTML) means: use the photo."""
    title = title or name
    st = f' style="{style}"' if style else ""
    eb = f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else ""
    if credit:
        return (f'<div class="plate photo"{st}>{picture(slug, alt or name, SIZES_PLATE, eager=True)}'
                f'{eb}<h1>{e(title)}</h1></div><p class="credit">Photo: {credit}</p>')
    return (f'<div class="plate pattern pat{pattern_of(slug)}"{st}>'
            f'<span class="initial" aria-hidden="true">{e(initial_of(name))}</span>'
            f'{eb}<h1>{e(title)}</h1></div>')


def vthumb(v):
    slug = v["slug"]
    if shows_the_venue(v):
        return (f'<span class="vthumb"><picture>'
                f'<source type="image/webp" srcset="{u("/img/" + slug + "-thumb.webp")}">'
                f'<img src="{u("/img/" + slug + "-thumb.jpg")}" alt="" width="176" height="176" '
                f'loading="lazy" decoding="async"></picture></span>')
    return (f'<span class="vthumb pattern pat{pattern_of(slug)}" aria-hidden="true">'
            f'<span class="initial">{e(initial_of(v["name"]))}</span></span>')


def vcard(v, meta, answer):
    return (f'<a class="vcard" href="{u("/venues/" + v["slug"] + ".html")}">{vthumb(v)}'
            f'<span class="vtext"><span class="t">{e(v["name"])}</span>'
            f'<span class="m">{e(meta)}</span><span class="a">{answer}</span></span></a>')


# ---------------------------------------------------------------- venues

STATUS_CHIP = {
    "confirmed": "",
    "likely": '<span class="chip">1 source</span>',
    "unconfirmed": '<span class="chip">unconfirmed</span>',
    "unknown": '<span class="chip">not found yet</span>',
}


def fact(label, f, big=False, full=False):
    f = f or {}
    val = (f.get("value") or "").strip()
    st = f.get("status") or ("unknown" if not val else "likely")
    shown = e(val) if val else "Not found yet"
    cls = "fact full" if full else "fact"
    dd = "big" if big and val and len(val) <= 8 else ""
    chip = STATUS_CHIP.get(st, "") if not (st == "unknown" and not val) else ""
    return f'<div class="{cls}"><dt>{e(label)}</dt><dd class="{dd}">{shown}{chip}</dd></div>'


def all_sources(v):
    seen, out = set(), []
    for k in ("dress", "age", "cover", "getting_in", "hours", "price", "accessibility", "subway"):
        for s in (v.get(k) or {}).get("sources", []) or []:
            url = (s.get("url") or "").strip()
            if url and url not in seen:
                seen.add(url)
                out.append((s.get("name") or urllib.parse.urlparse(url).netloc, url))
    return out


def venue_page(v, vs=None):
    slug = v["slug"]
    path = f"/venues/{slug}.html"
    checked = fmt_date(v.get("checked", "2026-10-18"))
    srcs = all_sources(v)
    dress = v.get("dress") or {}
    gi = v.get("getting_in") or {}
    type_ = v.get("type", "bar")
    hood = v.get("neighborhood", "")
    name = v["name"]
    closed = v.get("status") == "closed"

    photo = v.get("photo") or {}
    shot = has_photo(v)
    credit = None
    if shot:
        lic, lurl = photo.get("license", ""), photo.get("license_url", "")
        lic_html = f'<a href="{e(lurl)}" rel="license noopener">{e(lic)}</a>' if lurl else e(lic)
        credit = (f'{e(photo.get("credit", ""))} · {lic_html} · resized and cropped by us'
                  + (f'. {e(photo["depicts"])}' if photo.get("depicts") else ""))
    # The hero is decorative: the name is in the h1 right beside it and the
    # credit sits underneath, so naming it again only doubles the announcement.
    head_block = plate(slug, name, f"{e(hood)} · {e(type_)}", credit=credit, alt="")

    if closed:
        body = f"""<div class="answer"><div class="label">Status</div><div class="value">Closed</div><p>{e(v.get('status_note', ''))}</p></div>
<a class="stamp" href="#sources">Checked {checked} · {len(srcs)} sources<span class="go">Sources ↓</span></a>"""
    else:
        dchip = STATUS_CHIP.get(dress.get("status", ""), "")
        warn = ""
        if v.get("status") == "unclear":
            warn = f'<div class="card" style="border:1px solid var(--bronze)"><b>Status unclear.</b> {e(v.get("status_note", ""))} Check the venue before heading out.</div>'
        body = warn + f"""<section class="answer" aria-labelledby="dc"><div class="label" id="dc">Dress code</div>
<div class="value">{e(dress.get('answer') or 'Not found yet')}</div><p>{e(dress.get('detail', ''))}</p>{dchip}</section>
<a class="stamp" href="#sources">Checked {checked} · {len(srcs)} sources · editor review pending<span class="go">Sources ↓</span></a>
<dl class="facts">
{fact('Age', v.get('age'), big=True)}
{fact('Cover', v.get('cover'))}
{fact('Getting in', gi)}
{fact('Hours', v.get('hours'))}
{fact('Drinks', v.get('price'))}
{fact('Nearest subway', v.get('subway'))}
{fact('Accessibility', v.get('accessibility'), full=True)}
</dl>""" + extras.week_table(v)
        if gi.get("booking_url"):
            body += f'<a class="card-link" href="{e(gi["booking_url"])}" rel="nofollow noopener">' \
                    f'<span>Book or check availability<span class="sub">{e(gi.get("booking_platform", "").title())} · venue&#39;s own booking page</span></span><span class="go">Open →</span></a>'
        # Stay22 is not an approved partner, so the hotel card (href="#") is not
        # rendered. hotel_bar stays on the venue JSON for when a real URL exists.
        # if v.get("hotel_bar"):
        #     body += f'<a class="card-link" href="#" data-affiliate="stay22" rel="sponsored nofollow noopener">' \
        #             f'<span>Stay upstairs or nearby<span class="sub">Hotels within a short walk (affiliate link)</span></span><span class="go">See rates →</span></a>'
        body += affiliates.venue_block(v, u)
        skip = [s for s in (v.get("skip_if") or []) if s]
        if skip:
            body += "<h2>Skip it if</h2><ul class=\"clean skip\">" + "".join(f"<li>{e(s)}</li>" for s in skip) + "</ul>"

    faqs = present.venue_faqs(v)
    body += present.answer_box(present.short_answer(v))
    body += present.faq_html(faqs)
    pool = [x for x in vs or [] if x["slug"] != slug and x.get("status") != "closed"]
    same_h = sorted((x for x in pool if x.get("neighborhood") == v.get("neighborhood")), key=lambda x: x["name"].lower())
    same_b = sorted((x for x in pool if x.get("borough") == v.get("borough") and x not in same_h), key=lambda x: x["name"].lower())
    near = (same_h + same_b)[:3]
    if near:
        body += '<h2>Nearby</h2><div class="vlist">' + "".join(
            vcard(x, f'{x.get("neighborhood", "")} · {x.get("borough", "")}',
                  "Dress: " + e((x.get("dress") or {}).get("answer") or "not found yet"))
            for x in near) + "</div>"
    mine = [ev for ev in (events.load_snapshot().get("events") or []) if ev.get("venue_slug") == slug][:4]
    if mine:
        body += present.events_html(
            mine, "Upcoming here",
            "Matched from the daily event feed. Ticketmaster links go to that event's page.",
            "")
    body += f"""<h2 id="sources">Sources</h2>
<p class="small">We checked these on {checked}. Facts change; confirm with the venue before you go. Something wrong at the door? <a href="mailto:hello@nynightlife.com?subject={urllib.parse.quote('Door report: ' + name)}">Tell us</a>.</p>
<ol class="sources">{''.join(f'<li><a href="{e(url)}" rel="nofollow noopener">{e(n)}</a></li>' for n, url in srcs) or '<li>No sources recorded yet.</li>'}</ol>
<p class="small"><a href="{u('/venues/')}">← All venues</a> · <a href="{u('/guides/nyc-dress-codes.html')}">NYC dress codes</a> · <a href="{u('/guides/nyc-bar-closing-time.html')}">What time NYC bars close</a> · <a href="{u('/guides/under-21-nyc-bars-clubs.html')}">Under 21 in NYC</a> · <a href="{u('/tonight/')}">Open tonight</a></p>"""

    btns = ""
    if not closed:
        if v.get("phone"):
            tel = "".join(c for c in v["phone"] if c.isdigit() or c == "+")
            btns += f'<a class="btn primary" href="tel:{e(tel)}">Call</a>'
        if v.get("address"):
            q = urllib.parse.quote(f"{name}, {v['address']}")
            btns += f'<a class="btn ghost" href="https://www.google.com/maps/search/?api=1&amp;query={q}" rel="noopener">Directions</a>'
    bar = actions(btns, disclose=f"Checked {checked}", side_title="Go there") if btns else ""
    if bar:
        body = f'<div class="vgrid"><div class="vmain">{body}</div><div class="vside">{bar}</div></div>'
    body = head_block + body
    # Only a venue we believe is trading is marked up as a business; a closed or
    # unclear one is a plain Place, so the machine-readable page cannot say
    # "open" where the visible page says otherwise.
    kind = "Place" if v.get("status") in ("closed", "unclear") else ("NightClub" if "club" in type_ else "BarOrPub")
    about = {"@type": kind, "name": name, "address": v.get("address", "")}
    hours_spec = present.opening_hours(v)
    if hours_spec and kind != "Place":
        about["openingHoursSpecification"] = hours_spec
    same = [x for x in [v.get("website"), v.get("instagram")] if x]
    if same:
        about["sameAs"] = same
    if shot:
        about["image"] = SITE + f"/img/{slug}.jpg"
    schema = [{"@context": "https://schema.org", "@type": "WebPage", "name": f"{name}: dress code, age & how to get in",
              "url": SITE + path, "dateModified": v.get("checked"),
              "author": {"@type": "Person", "name": "Dan Herlehy"}, "about": about},
             present.faq_schema(faqs)]
    schema += [s for s in (present.event_schema(ev) for ev in mine) if s]
    if closed:
        desc = f"{name} ({hood}) has closed. {v.get('status_note', '')[:110]}".strip()
    elif v.get("status") == "unclear":
        desc = f"{name} ({hood}): we could not confirm this venue is still operating. Checked {checked}."
    else:
        desc = f"{name} ({hood}): dress code, age policy, cover and how to get in, checked {checked} with sources."
    # Keep the descriptive title, then drop clauses until it is 60 characters or under.
    title = next(t for t in (
        f"{name} dress code, age & cover | NY Nightlife",
        f"{name} dress code & cover | NY Nightlife",
        f"{name}: dress code | NY Nightlife",
        f"{name} | NY Nightlife",
    ) if len(t) <= 60)
    boro = v.get("borough") or ""
    crumbs = [("Home", "/"), ("Venues", "/venues/")]
    if boro:
        crumbs.append((boro, "/venues/#" + re.sub(r"[^a-z0-9]+", "-", boro.lower()).strip("-")))
    crumbs.append((name, path))
    write(path, page(title, desc, path, body, schema, "" if btns else "no-bar",
                     image=f"/img/og/{slug}.jpg",   # make_og.py draws one per venue; check_output() enforces it
                     img_alt=f"{name}, {hood}: dress code, age and cover",
                     crumbs=crumbs, updated=v.get("checked"), crumb_label=name))
    return v


def venues_index(vs):
    open_vs = [v for v in vs if v.get("status") != "closed"]
    by_b = {}
    for v in sorted(open_vs, key=lambda x: x["name"].lower()):
        by_b.setdefault(v.get("borough") or "Other", []).append(v)
    body = '<p class="eyebrow" style="margin-top:16px">All venues</p><h1>Know before you go</h1>' \
           + present.answer_box("This is every NYC bar and club we have checked. Open a page for the dress code, age, cover, and how to get in, each with its sources and the date. If a fact was not found, the page says so instead of guessing. Closed places stay marked closed.") \
           + '<p class="lede">Dress code, age and how to get in for NYC bars and clubs, each with its sources and the date we checked.</p>'
    for b in sorted(by_b):
        anchor = re.sub(r"[^a-z0-9]+", "-", b.lower()).strip("-")
        body += f'<h2 id="{e(anchor)}">{e(b)}</h2><div class="vlist two posters">'
        for v in by_b[b]:
            age = (v.get("age") or {}).get("value")
            answer = "Dress: " + e((v.get("dress") or {}).get("answer") or "not found yet")
            body += vcard(v, f'{v.get("neighborhood", "")} · {v.get("type", "")}',
                          answer + (f" · Age: {e(age)}" if age else ""))
        body += "</div>"
    pairs = [(v["name"], f"/venues/{v['slug']}.html") for v in open_vs]
    schema = [present.item_list("NYC bars and clubs", pairs),
              {"@context": "https://schema.org", "@type": "CollectionPage",
               "name": "NYC bars and clubs", "dateModified": max(v.get("checked", "2026-10-18") for v in vs)}]
    write("/venues/index.html", page("NYC bars & clubs: dress code, age, cover | NY Nightlife",
                                     "Checked, sourced door facts for NYC bars and clubs: dress code, age, cover and how to get in.",
                                     "/venues/", body, schema, body_class="no-bar",
                                     updated=max(v.get("checked", "2026-10-18") for v in vs)))


def dress_hub(vs):
    open_vs = sorted([v for v in vs if v.get("status") != "closed"], key=lambda x: x["name"].lower())
    rows = "".join(
        f'<tr><td data-label="Venue"><a href="{u("/venues/" + v["slug"] + ".html")}">{e(v["name"])}</a><div class="small">{e(v.get("neighborhood", ""))}</div></td>'
        f'<td data-label="Dress code">{e((v.get("dress") or {}).get("answer") or "Not found yet")}</td>'
        f'<td data-label="Age">{e((v.get("age") or {}).get("value") or "Not found yet")}</td>'
        f'<td data-label="Cover">{e((v.get("cover") or {}).get("value") or "Not found yet")}</td></tr>' for v in open_vs)
    checked = fmt_date(max(v.get("checked", "2026-10-18") for v in vs))
    body = f"""<p class="eyebrow" style="margin-top:16px">The roundup</p><h1>NYC bar &amp; club dress codes</h1>
<p class="lede">What {len(open_vs)} New York bars and clubs say about dress code, age and cover, and what sources report when the venue says nothing. Checked {checked}.</p>
<div class="card"><h2 class="as-h3">The short version</h2><ul class="clean">
<li>Most cocktail bars publish no dress code. "Smart casual" is the safe default.</li>
<li>Clubs and rooftops are where sneakers, athletic wear and hats get turned away.</li>
<li>Almost every venue here is 21+ at night. Bring a physical ID.</li></ul></div>
<h2>Venue by venue</h2>
<div class="scroll-x"><table class="compare"><thead><tr><th>Venue</th><th>Dress code</th><th>Age</th><th>Cover</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="small">Each venue page lists its sources. <a href="{u('/how-we-check.html')}">How we check</a>.</p>"""
    schema = {"@context": "https://schema.org", "@type": "Article", "headline": "NYC bar & club dress codes",
              "dateModified": max(v.get("checked", "2026-10-18") for v in vs), "author": {"@type": "Person", "name": "Dan Herlehy"}}
    write("/guides/nyc-dress-codes.html", page("NYC bar & club dress codes (checked) | NY Nightlife",
                                                "Dress code, age and cover for NYC bars and clubs in one table, with sources and the date checked.",
                                                "/guides/nyc-dress-codes.html", body, schema, "no-bar"))


# ---------------------------------------------------------------- run

# Files the pages need that live outside the generator: the Ledger CSS and photos
# from _build, and Nyla's chatbot files from the site root (kept byte-for-byte).
CHATBOT = ["css/concierge.css", "assets/nyla-full-welcome.png", "assets/nyla-head.png"]


def sitemap(vs, pbs, extra=()):
    """Generated, not hand-maintained, so a new page can never be forgotten and
    lastmod can never drift from the date the page displays."""
    rows = [("/", max(v.get("checked", "2026-10-18") for v in vs)),
            ("/venues/", max(v.get("checked", "2026-10-18") for v in vs)),
            ("/guides/nyc-dress-codes.html", max(v.get("checked", "2026-10-18") for v in vs))]
    rows += [(f"/venues/{v['slug']}.html", v.get("checked", "2026-10-18")) for v in vs]
    rows += [(f"/plans/{p['slug']}.html", p["checked"]) for p in pbs]
    rows += list(extra)
    rows += [(p, SITE_EDITED) for p in ("/about.html", "/how-we-check.html",
                                        "/affiliate-disclosure.html", "/privacy.html", "/contact.html")]
    body = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{d}</lastmod></url>\n" for p, d in sorted(rows))
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n",
        encoding="utf-8", newline="\n")


def copy_static():
    import shutil
    site = ROOT.parent
    # Nyla's updated script lives in _build until cutover, so the old live site keeps the old one
    pairs = [(ROOT / "site.css", OUT / "css" / "site.css"), (ROOT / "concierge.js", OUT / "js" / "concierge.js"),
             (ROOT / "live.js", OUT / "js" / "live.js"), (ROOT / "signal.js", OUT / "js" / "signal.js")]
    # the responsive set from make_images.py; its <slug>.jpg replaces the master
    pairs += [(f, OUT / "img" / f.name) for f in sorted(GEN.glob("*.jpg"))]
    pairs += [(f, OUT / "img" / f.name) for f in sorted(GEN.glob("*.webp"))]
    pairs += [(f, OUT / "img" / "og" / f.name) for f in sorted(OG_DIR.glob("*.jpg"))]
    pairs += [(f, OUT / "fonts" / f.name) for f in sorted((site / "fonts").glob("*.woff2"))]
    if OUT.resolve() != site.resolve():
        pairs += [(site / c, OUT / c) for c in CHATBOT]
    for src, dst in pairs:
        if src.exists() and src.resolve() != dst.resolve():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)


def check_output():
    """Every local file the pages ask for must exist. A missing derivative used
    to ship as an empty hero and a 404 share image, with no warning."""
    missing = set()
    for f in OUT.rglob("*.html"):
        s = f.read_text(encoding="utf-8")
        refs = re.findall(r'(?:src|href)="(/[^"]+)"', s) + re.findall(r'content="https://nynightlife\.com(/img/[^"]+)"', s)
        for m in re.findall(r'srcset="([^"]+)"', s):
            refs += [c.strip().split()[0] for c in m.split(",") if c.strip()]
        for r in refs:
            r = r.split("?")[0].split("#")[0]
            if r.endswith("/"):
                r += "index.html"
            if not (OUT / r.lstrip("/")).exists():
                missing.add(r)
    if missing:
        raise SystemExit("build produced broken references:\n  " + "\n  ".join(sorted(missing))
                         + "\n(if these are images, run: python _build/make_images.py && python _build/make_og.py)")
    return True


def write_meta(live_day):
    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        "User-agent: GPTBot\nAllow: /\n\n"
        "User-agent: OAI-SearchBot\nAllow: /\n\n"
        "User-agent: PerplexityBot\nAllow: /\n\n"
        "User-agent: ClaudeBot\nAllow: /\n\n"
        "User-agent: Google-Extended\nAllow: /\n\n"
        "User-agent: Bingbot\nAllow: /\n\n"
        "Sitemap: https://nynightlife.com/sitemap.xml\n",
        encoding="utf-8", newline="\n")
    (OUT / "llms.txt").write_text(
        "# NY Nightlife\n\n"
        "> Know before you go for New York bars and clubs: dress code, age, cover, hours, and what is on tonight. "
        "Facts are sourced and dated. Event listings come from NYC Open Data and, when configured, Ticketmaster Discovery. "
        "We do not invent missing facts.\n\n"
        "## Start here\n"
        "- [Tonight](https://nynightlife.com/tonight/): what's on tonight and this week, plus which checked venues are open\n"
        "- [Venues](https://nynightlife.com/venues/): door facts for the checked bars and clubs\n"
        "- [Group nights](https://nynightlife.com/plans/): bachelorette prices and the cruise guide\n"
        "- [Dress codes](https://nynightlife.com/guides/nyc-dress-codes.html)\n"
        "- [Closing time](https://nynightlife.com/guides/nyc-bar-closing-time.html)\n"
        "- [Under 21](https://nynightlife.com/guides/under-21-nyc-bars-clubs.html)\n"
        "- [How we check](https://nynightlife.com/how-we-check.html)\n"
        "- [Image credits](https://nynightlife.com/image-credits.html)\n\n"
        f"Updated {live_day}.\n",
        encoding="utf-8", newline="\n")
    lines = ["# NY Nightlife, full index\n",
             "Each venue page repeats only the facts checked for that place.\n"]
    for f in sorted((ROOT / "data" / "venues").glob("*.json")):
        v = json.loads(f.read_text(encoding="utf-8"))
        lines.append(f"- [{v['name']}](https://nynightlife.com/venues/{v['slug']}.html): {v.get('type', 'venue')} in {v.get('neighborhood', '')}, {v.get('borough', '')}. Checked {v.get('checked', '')}.\n")
    (OUT / "llms-full.txt").write_text("".join(lines), encoding="utf-8", newline="\n")


def main():
    loaded = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "venues").glob("*.json"))]
    vs = [venue_page(raw, loaded) for raw in loaded]
    venues_index(vs)
    dress_hub(vs)
    import pages
    XH = {"u": u, "page": page, "write": write, "fmt_date": fmt_date, "OUT": OUT, "LIVE_V": LIVE_V}
    plan_rows = pages.build(page, write, u, actions, fmt_date, vs,
                            {"plate": plate, "vcard": vcard, "picture": picture, "home_box": lambda: extras.home_box(XH),
                             "newsletter": lambda: extras.newsletter_block(XH)})
    extras.tonight_page(XH, vs)
    changed = extras.changes_pages(XH, vs)   # None while the log is too thin to index
    extra = [extras.guide_under21(XH, vs), extras.guide_closing(XH, vs)] + ([("/changes/", changed)] if changed else [])
    extra += [("/tonight/", "2026-11-11")] + list(plan_rows or [])
    import nyla
    pbs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "playbooks").glob("*.json"))]
    nyla.build(write, fmt_date, vs, pbs, max(v.get("checked", "2026-10-18") for v in vs))
    copy_static()
    snap = events.load_snapshot()
    live_day = (snap.get("fetched_at") or SITE_EDITED)[:10]
    extra = [(p, live_day if p in ("/tonight/", "/") else d) for p, d in extra]
    write_meta(live_day)
    sitemap(vs, pbs, extra)
    check_output()
    print(f"built {len(vs)} venue pages + hubs into {OUT}")


if __name__ == "__main__":
    main()
