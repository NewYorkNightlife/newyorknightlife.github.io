"""Hard checks on the built site. Run after build.py.

Fails on JSON-LD that does not parse, a missing local file a page links to,
or a page that is not an HTML document. Also locks the money pages' titles,
FAQ and breadcrumb schema, affiliate disclosure, and the stable bachelorette
sentence the birthday intent depends on.

Intent phrases are not checked here. Those live in test_nyla.js.
"""
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
    refs = re.findall(r'(?:src|href)="(/[^"]+)"', text)
    refs += re.findall(r'content="https://nynightlife\.com(/img/[^"]+)"', text)
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
        ("index.html", "/plans/nyc-boat-party.html"),
        ("tonight/index.html", "/guides/nyc-comedy-clubs.html"),
    ):
        if needle not in (ROOT / hub).read_text(encoding="utf-8"):
            fail(f"{hub} does not link to {needle}")
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
    if FAILS:
        print(f"{FAILS} failed")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
