"""Hard checks on the built site. Run after build.py.

Fails on JSON-LD that does not parse, a missing local file a page links to,
or a page that is not an HTML document. Also locks the money pages' titles,
FAQ and breadcrumb schema, affiliate disclosure, and the stable bachelorette
sentence the birthday intent depends on.

Intent phrases are not checked here. Those live in test_nyla.js.
"""
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MONEY = {
    "/plans/nyc-boat-party.html": "NYC boat party and sunset cruise | NY Nightlife",
    "/plans/bachelor-party.html": "NYC bachelor party ideas | NY Nightlife",
    "/guides/nyc-comedy-clubs.html": "NYC comedy clubs | NY Nightlife",
}
FAILS = 0


def fail(msg):
    global FAILS
    FAILS += 1
    print("FAIL", msg)


def local_refs(text):
    """Root-relative links, including ones that only appear inside JSON-LD."""
    refs = re.findall(r'(?:src|href)="(/[^"]+)"', text)
    refs += re.findall(r'https://nynightlife\.com(/[^"\s<]+)', text)
    for srcset in re.findall(r'srcset="([^"]+)"', text):
        refs += [c.strip().split()[0] for c in srcset.split(",") if c.strip().startswith("/")]
    return refs


def main():
    pages = sorted(ROOT.rglob("*.html"))
    if not pages:
        fail("no html")
    for f in pages:
        rel = "/" + f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8")
        if not text.lstrip().lower().startswith("<!doctype html"):
            fail(f"{rel} missing doctype")
        if text.lower().count("<html") != 1 or "</html>" not in text.lower():
            fail(f"{rel} is not one html document")
        if text.lower().count("<script") != text.lower().count("</script>"):
            fail(f"{rel} has an unclosed script")
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
        types = set()
        for i, raw in enumerate(blocks):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as ex:
                fail(f"{rel} JSON-LD #{i} {ex}")
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    types.add(item.get("@type"))
        for ref in local_refs(text):
            target = ref.split("?")[0].split("#")[0]
            if target.endswith("/"):
                target += "index.html"
            if not (ROOT / target.lstrip("/")).exists():
                fail(f"{rel} broken link {ref}")
        if rel in MONEY:
            m = re.search(r"<title>(.*?)</title>", text)
            title = m.group(1) if m else ""
            if title != MONEY[rel]:
                fail(f"{rel} title {title!r}")
            if len(title) > 60:
                fail(f"{rel} title length {len(title)}")
            if "FAQPage" not in types or "BreadcrumbList" not in types:
                fail(f"{rel} schema types {types}")
            if 'class="short-answer"' not in text:
                fail(f"{rel} missing answer box")
            if "affiliate-disclosure.html" not in text or "pid=P00330813" not in text or "mcid=42383" not in text:
                fail(f"{rel} missing affiliate disclosure or partner ids")
            if "Checked 2026-11-16" not in text:
                fail(f"{rel} missing checked date")
            if 'rel="sponsored nofollow noopener"' not in text:
                fail(f"{rel} affiliate link missing sponsored rel")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for path in MONEY:
        if f"https://nynightlife.com{path}" not in sitemap:
            fail(f"sitemap missing {path}")
    bach = (ROOT / "plans/bachelorette-night.html").read_text(encoding="utf-8")
    if "with 6 people" not in bach.lower() and "With 6 people" not in bach:
        fail("bachelorette page missing stable 'With 6 people' sentence")
    # hubs that should point at the new pages
    for hub, needle in (
        ("plans/index.html", "/plans/nyc-boat-party.html"),
        ("plans/index.html", "/plans/bachelor-party.html"),
        ("plans/index.html", "/guides/nyc-comedy-clubs.html"),
        ("plans/index.html", "/this-weekend/"),
        ("index.html", "/plans/nyc-boat-party.html"),
        ("index.html", "/this-weekend/"),
        ("index.html", "/guides/nyc-speakeasies.html"),
        ("index.html", "/guides/nyc-rooftop-bars.html"),
        ("index.html", "/guides/nyc-new-years-eve.html"),
        ("tonight/index.html", "/guides/nyc-comedy-clubs.html"),
        ("tonight/index.html", "/this-weekend/"),
    ):
        if needle not in (ROOT / hub).read_text(encoding="utf-8"):
            fail(f"{hub} does not link to {needle}")
    guide_pages = {
        "/this-weekend/": "NYC this weekend | NY Nightlife",
        "/guides/nyc-speakeasies.html": "NYC speakeasies | NY Nightlife",
        "/guides/nyc-rooftop-bars.html": "NYC rooftop bars | NY Nightlife",
        "/guides/nyc-new-years-eve.html": "NYC New Year's Eve 2026 | NY Nightlife",
    }
    for path, want in guide_pages.items():
        if f"https://nynightlife.com{path}" not in sitemap:
            fail(f"sitemap missing {path}")
        target = ROOT / (path.strip("/") + ("/index.html" if path.endswith("/") else ""))
        text = target.read_text(encoding="utf-8")
        m = re.search(r"<title>(.*?)</title>", text)
        title = html.unescape(m.group(1)) if m else ""
        if title != want:
            fail(f"{path} title {title!r}")
        if len(title) > 60:
            fail(f"{path} title length {len(title)}")
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
        types = set()
        for raw in blocks:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            for item in (data if isinstance(data, list) else [data]):
                if isinstance(item, dict):
                    types.add(item.get("@type"))
        if "FAQPage" not in types or "BreadcrumbList" not in types:
            fail(f"{path} schema types {types}")
        if 'class="short-answer"' not in text or 'class="route"' not in text:
            fail(f"{path} missing answer box or route line")
        if "pid=P00330813" not in text or "mcid=42383" not in text:
            fail(f"{path} missing viator partner ids")
        if 'rel="sponsored nofollow noopener"' not in text:
            fail(f"{path} affiliate link missing sponsored rel")
        if "59f0bf98-cda3-4aaf-9bd2-b750205147c8" not in text:
            fail(f"{path} lost the impact verification tag")
        if "dateModified" not in text:
            fail(f"{path} missing dateModified")
    weekend = (ROOT / "this-weekend" / "index.html").read_text(encoding="utf-8")
    if "js/tonight.js" not in weekend or 'data-night-page="weekend"' not in weekend:
        fail("weekend page missing the weekend client")
    if "ItemList" not in weekend or '"@type": "Event"' not in weekend and '"@type":"Event"' not in weekend:
        # Event schema is omitted when the feed has no weekend rows. ItemList still has venues.
        if "ItemList" not in weekend:
            fail("weekend page missing ItemList")
    speak = (ROOT / "guides" / "nyc-speakeasies.html").read_text(encoding="utf-8")
    for slug in ("please-dont-tell", "the-back-room", "attaboy", "employees-only", "death-and-co", "mr-purple"):
        if f"/venues/{slug}.html" not in speak:
            fail(f"speakeasy guide missing {slug}")
    if "phone booth inside Crif Dogs" not in speak or "Toy Company" not in speak or "AB 134" not in speak:
        fail("speakeasy guide dropped a checked door fact")
    if "rooftop bar" not in speak:
        fail("speakeasy guide does not say Mr. Purple is a rooftop")
    roofs = (ROOT / "guides" / "nyc-rooftop-bars.html").read_text(encoding="utf-8")
    for slug in ("230-fifth-rooftop", "westlight", "magic-hour-rooftop", "phd-rooftop-lounge",
                 "harriets-rooftop", "le-bain", "mr-purple", "ophelia-lounge", "somewhere-nowhere"):
        if f"/venues/{slug}.html" not in roofs:
            fail(f"rooftop guide missing {slug}")
    nye = (ROOT / "guides" / "nyc-new-years-eve.html").read_text(encoding="utf-8")
    for needle in ("December 31, 2026", "11:59", "timessquarenyc.org/nye/nye-faq",
                   "circleline.com/nyc-new-years-eve-cruises", "4am"):
        if needle not in nye:
            fail(f"NYE guide missing {needle}")
    if re.search(r"\$\d", nye):
        fail("NYE guide invented a price")
    for slug in ("magic-hour-rooftop", "phd-rooftop-lounge", "employees-only"):
        if f"/venues/{slug}.html" not in nye:
            fail(f"NYE guide missing {slug}")
    import datetime as dt
    sys.path.insert(0, str(ROOT / "_build"))
    import events
    import pages
    now = dt.datetime(2026, 11, 16, 18, 0, tzinfo=events.NY)
    sample = [
        {"category": "comedy", "title": "Late set", "venue_name": "Gotham", "start": "2026-11-16T20:00:00-05:00"},
        {"category": "music", "title": "A band", "venue_name": "Hall", "start": "2026-11-16T20:00:00-05:00"},
        {"category": "nightlife", "title": "Comedy night", "venue_name": "Bar", "start": "2026-11-17T21:00:00-05:00"},
        {"category": "comedy", "title": "Last week", "start": "2026-11-01T20:00:00-05:00"},
        {"listing": True, "category": "comedy", "title": "Comedy tour", "start": "2026-11-16T20:00:00-05:00"},
        {"category": "comedy", "title": "No time"},
    ]
    picked = pages.comedy_events(sample, now, events.parse_when)
    titles = [ev["title"] for ev in picked]
    if titles != ["Late set", "Comedy night"]:
        fail(f"comedy feed filter returned {titles}")
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    tonight = (ROOT / "tonight" / "index.html").read_text(encoding="utf-8")
    if "59f0bf98-cda3-4aaf-9bd2-b750205147c8" not in home or "59f0bf98-cda3-4aaf-9bd2-b750205147c8" not in tonight:
        fail("impact site verification missing")
    if "js/tonight.js" not in home or "data-events=" not in home or "data-night-line" not in home:
        fail("home missing the tonight client")
    if "js/tonight.js" not in tonight or 'data-night-page="tonight"' not in tonight:
        fail("tonight page missing the tonight client")
    if not (ROOT / "data" / "events.json").is_file():
        fail("missing data/events.json")
    else:
        feed = json.loads((ROOT / "data" / "events.json").read_text(encoding="utf-8"))
        if "events" not in feed or "fetched_at" not in feed:
            fail("events.json is not the week snapshot")
        blob = json.dumps(feed)
        if "apikey" in blob.lower() or "test-key" in blob:
            fail("events.json contains a key")
    if "pid=P00330813" not in tonight or "mcid=42383" not in tonight:
        fail("tonight page lost the viator affiliate")
    for label, text in (("home", home), ("tonight", tonight)):
        if re.search(r"\b(list|lists) 0\b", text) or re.search(r"\b0 events\b", text) or re.search(r"\b0 tonight\b", text):
            fail(f"{label} shows a bare zero count")
    if FAILS:
        print(f"{FAILS} failed")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
