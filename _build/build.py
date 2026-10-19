"""Build NY Nightlife v2 static pages into the site root (../).

Data:  _build/data/venues/*.json  (one per venue, fact-checked; see FACTS.md)
       _build/data/playbooks/*.json
Pages: generated from the templates in this file.
Run:   python _build/build.py   (from the site folder), then: node _build/test_nyla.js .
"""
import html
import json
import os
import pathlib
import posixpath
import re
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(os.environ.get("NYN_OUT", ROOT.parent))  # the live site root
SITE = "https://nynightlife.com"
BASE = os.environ.get("NYN_BASE", "")  # path prefix for test builds; "" for the live site
RELATIVE = os.environ.get("NYN_RELATIVE") == "1"  # relative links for the private preview
CHECKED_FMT = "%b %-d, %Y"

e = html.escape


def u(path):
    return BASE + path


def fmt_date(iso):
    y, m, d = iso.split("-")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[int(m) - 1]} {int(d)}, {y}"


# ---------------------------------------------------------------- shell

def head(title, desc, path, schema=None, robots="index,follow"):
    ld = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>' if schema else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0B0908">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;1,9..144,400&amp;family=Instrument+Sans:wght@400;500;600;700&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="{u('/css/site.css')}?v=20261018">
<link rel="stylesheet" href="{u('/css/concierge.css')}">
<script defer src="{u('/js/concierge.js')}?v=20261018"></script>
<script defer src="{u('/analytics.js')}"></script>
{ld}
</head>
"""


MENU = [("/venues/", "Venues"), ("/guides/nyc-dress-codes.html", "Dress codes"),
        ("/plans/bachelorette-night.html", "Group nights"), ("/how-we-check.html", "How we check")]


def header():
    links = "".join(f'<a class="txt" href="{u(p)}">{e(t)}</a>' for p, t in MENU)
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
<nav aria-label="Footer"><a href="{u('/about.html')}">About</a><a href="{u('/how-we-check.html')}">How we check</a><a href="{u('/affiliate-disclosure.html')}">Affiliate disclosure</a><a href="{u('/privacy.html')}">Privacy</a><a href="{u('/contact.html')}">Contact</a></nav>
<p>NY Nightlife is an independent guide. Facts are checked against the sources listed on each page; always confirm with the venue before you go. 21+ venues are for adults of legal drinking age.</p>
</div></footer>
"""


def actions(buttons, disclose=None):
    d = f'<p class="disclose">{disclose}</p>' if disclose else ""
    return f'<div class="actions" role="region" aria-label="Actions"><div class="wrap">{buttons}{d}</div></div>'


def page(title, desc, path, body, schema=None, body_class="", robots="index,follow"):
    return (head(title, desc, path, schema, robots) +
            f'<body class="{body_class}">\n' + header() + f'<main class="wrap">\n{body}\n</main>\n' + footer() + "</body>\n</html>\n")


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
    return f'<div class="{cls}"><dt>{e(label)}</dt><dd class="{dd}">{shown}</dd>{chip}</div>'


def all_sources(v):
    seen, out = set(), []
    for k in ("dress", "age", "cover", "getting_in", "hours", "price", "accessibility", "subway"):
        for s in (v.get(k) or {}).get("sources", []) or []:
            url = (s.get("url") or "").strip()
            if url and url not in seen:
                seen.add(url)
                out.append((s.get("name") or urllib.parse.urlparse(url).netloc, url))
    return out


def venue_page(v):
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
    local = (ROOT / "img" / f"{slug}.jpg").exists()
    if photo.get("url") and local:
        plate = (f'<div class="plate photo"><img src="{u("/img/" + slug + ".jpg")}" alt="{e(name)}" loading="eager" decoding="async">'
                 f'<p class="eyebrow">{e(hood)} · {e(type_)}</p><h1>{e(name)}</h1></div>'
                 f'<p class="credit">Photo: {e(photo.get("credit", ""))} · {e(photo.get("license", ""))}</p>')
    else:
        plate = f'<div class="plate"><p class="eyebrow">{e(hood)} · {e(type_)}</p><h1>{e(name)}</h1></div>'

    if closed:
        body = plate + f"""<div class="answer"><div class="label">Status</div><div class="value">Closed</div><p>{e(v.get('status_note', ''))}</p></div>
<a class="stamp" href="#sources">Checked {checked} · {len(srcs)} sources<span class="go">Sources ↓</span></a>"""
    else:
        dchip = STATUS_CHIP.get(dress.get("status", ""), "")
        warn = ""
        if v.get("status") == "unclear":
            warn = f'<div class="card" style="border:1px solid var(--bronze)"><b>Status unclear.</b> {e(v.get("status_note", ""))} Check the venue before heading out.</div>'
        body = plate + warn + f"""<section class="answer" aria-labelledby="dc"><div class="label" id="dc">Dress code</div>
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
</dl>"""
        if gi.get("booking_url"):
            body += f'<a class="card-link" href="{e(gi["booking_url"])}" rel="nofollow noopener">' \
                    f'<span>Book or check availability<span class="sub">{e(gi.get("booking_platform", "").title())} · venue&#39;s own booking page</span></span><span class="go">Open →</span></a>'
        if v.get("hotel_bar"):
            body += f'<a class="card-link" href="#" data-affiliate="stay22" rel="sponsored nofollow noopener">' \
                    f'<span>Stay upstairs or nearby<span class="sub">Hotels within a short walk (affiliate link)</span></span><span class="go">See rates →</span></a>'
        skip = [s for s in (v.get("skip_if") or []) if s]
        if skip:
            body += "<h2>Skip it if</h2><ul class=\"clean skip\">" + "".join(f"<li>{e(s)}</li>" for s in skip) + "</ul>"

    body += f"""<h2 id="sources">Sources</h2>
<p class="small">We checked these on {checked}. Facts change; confirm with the venue before you go. Something wrong at the door? <a href="mailto:hello@nynightlife.com?subject={urllib.parse.quote('Door report: ' + name)}">Tell us</a>.</p>
<ol class="sources">{''.join(f'<li><a href="{e(url)}" rel="nofollow noopener">{e(n)}</a></li>' for n, url in srcs) or '<li>No sources recorded yet.</li>'}</ol>
<p class="small"><a href="{u('/venues/')}">← All venues</a> · <a href="{u('/guides/nyc-dress-codes.html')}">NYC dress codes</a></p>"""

    btns = ""
    if not closed:
        if v.get("phone"):
            tel = "".join(c for c in v["phone"] if c.isdigit() or c == "+")
            btns += f'<a class="btn primary" href="tel:{e(tel)}">Call</a>'
        if v.get("address"):
            q = urllib.parse.quote(f"{name}, {v['address']}")
            btns += f'<a class="btn ghost" href="https://www.google.com/maps/search/?api=1&amp;query={q}" rel="noopener">Directions</a>'
    bar = actions(btns) if btns else ""
    kind = "NightClub" if "club" in type_ else "BarOrPub"
    schema = {"@context": "https://schema.org", "@type": "WebPage", "name": f"{name}: dress code, age & how to get in",
              "url": SITE + path, "dateModified": v.get("checked"),
              "author": {"@type": "Person", "name": "Dan Herlehy"},
              "about": {"@type": kind, "name": name, "address": v.get("address", ""),
                        "sameAs": [x for x in [v.get("website"), v.get("instagram")] if x]}}
    desc = f"{name} ({hood}): dress code, age policy, cover and how to get in, checked {checked} with sources."
    title = f"{name} dress code, age & cover | NY Nightlife"
    write(path, page(title, desc, path, body + bar, schema, "" if btns else "no-bar"))
    return v


def venues_index(vs):
    open_vs = [v for v in vs if v.get("status") != "closed"]
    by_b = {}
    for v in sorted(open_vs, key=lambda x: x["name"].lower()):
        by_b.setdefault(v.get("borough") or "Other", []).append(v)
    body = '<p class="eyebrow" style="margin-top:16px">All venues</p><h1>Know before you go</h1>' \
           '<p class="lede">Dress code, age and how to get in for NYC bars and clubs, each with its sources and the date we checked.</p>'
    for b in sorted(by_b):
        body += f"<h2>{e(b)}</h2><div class=\"vlist two\">"
        for v in by_b[b]:
            body += (f'<a class="vcard" href="{u("/venues/" + v["slug"] + ".html")}"><div class="t">{e(v["name"])}</div>'
                     f'<div class="m">{e(v.get("neighborhood", ""))} · {e(v.get("type", ""))}</div>'
                     f'<div class="a">Dress: {e((v.get("dress") or {}).get("answer") or "not found yet")} {(" · Age: " + e((v.get("age") or {}).get("value"))) if (v.get("age") or {}).get("value") else ""}</div></a>')
        body += "</div>"
    write("/venues/index.html", page("NYC bars & clubs: dress code, age, cover | NY Nightlife",
                                     "Checked, sourced door facts for NYC bars and clubs: dress code, age, cover and how to get in.",
                                     "/venues/", body, body_class="no-bar"))


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
<div class="card"><h3>The short version</h3><ul class="clean">
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


def copy_static():
    import shutil
    site = ROOT.parent
    # Nyla's updated script lives in _build until cutover, so the old live site keeps the old one
    pairs = [(ROOT / "site.css", OUT / "css" / "site.css"), (ROOT / "concierge.js", OUT / "js" / "concierge.js")]
    pairs += [(f, OUT / "img" / f.name) for f in sorted((ROOT / "img").glob("*.jpg"))]
    if OUT.resolve() != site.resolve():
        pairs += [(site / c, OUT / c) for c in CHATBOT]
    for src, dst in pairs:
        if src.exists() and src.resolve() != dst.resolve():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)


def main():
    vs = []
    for f in sorted((ROOT / "data" / "venues").glob("*.json")):
        vs.append(venue_page(json.loads(f.read_text(encoding="utf-8"))))
    venues_index(vs)
    dress_hub(vs)
    import pages
    pages.build(page, write, u, actions, fmt_date, vs)
    import nyla
    pbs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "playbooks").glob("*.json"))]
    nyla.build(write, fmt_date, vs, pbs, max(v.get("checked", "2026-10-18") for v in vs))
    copy_static()
    print(f"built {len(vs)} venue pages + hubs into {OUT}")


if __name__ == "__main__":
    main()
