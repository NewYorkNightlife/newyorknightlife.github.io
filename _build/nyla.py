"""Data for Nyla, the site chatbot (js/concierge.js).

Writes /data/venues.json from the same verified venue + playbook JSON the pages
are built from, plus the events feed and the canonical guide pages, so her
answers can never drift from what the pages say.

Labels mirror the page chips exactly (see build.fact / STATUS_CHIP):
"1 source", "unconfirmed", "not found yet"; an empty value reads "Not found yet".
Tags + aliases come from each venue's "chat" block.

`generated` is the build clock in America/New_York, not the last venue
fact-check date. `feed_fetched_at` is copied from the same public events
snapshot written to /data/events.json.
"""
import html as htmlmod
import json
import pathlib
import re

import redirects

LABEL = {"likely": " (1 source)", "unconfirmed": " (unconfirmed)", "unknown": " (not found yet)"}
IMG = pathlib.Path(__file__).resolve().parent / "img"
TAGS = {"rooftop", "cocktail", "club", "live", "ticketed", "no_cover", "dress_rule", "under21"}

# Extra question words that should route to a guide. Titles and slugs are
# also matched in js/concierge.js.
GUIDE_ALIASES = {
    "nyc-speakeasies": ["speakeasy", "speakeasies", "hidden door", "hidden bar"],
    "nyc-rooftop-bars": ["rooftop", "rooftops", "roof bar"],
    "nyc-new-years-eve": ["new years eve", "new year's eve", "nye", "ball drop"],
    "nyc-holiday-nights": ["holiday", "christmas lights", "dyker heights", "winter village", "rockefeller tree", "bryant park"],
    "nyc-comedy-clubs": ["comedy", "stand-up", "standup", "comedy club"],
    "nyc-dress-codes": ["dress code", "dress codes", "what to wear"],
    "nyc-bar-closing-time": ["closing time", "last call", "4am", "4 am", "when do bars close"],
    "under-21-nyc-bars-clubs": ["under 21", "under-21", "18+", "all ages"],
}

EVENT_FIELDS = (
    "id", "source", "title", "start", "end", "venue_name", "venue_slug",
    "borough", "neighborhood", "category", "url",
)


def _fact(f, key="value", default=None):
    """Value plus its status label, using the same status rule as the page."""
    f = f or {}
    val = (f.get(key) or "").strip()
    if not val:
        return "Not found yet"
    st = f.get("status") or default
    return val + LABEL.get(st, "")


def _has_photo(v):
    return bool((v.get("photo") or {}).get("url")) and (IMG / f"{v['slug']}.jpg").exists()


def _venue(v, fmt_date):
    chat = v.get("chat") or {}
    tags = chat.get("tags") or []
    bad = set(tags) - TAGS
    assert not bad, f"{v['slug']}: unknown chat tags {bad}"
    assert re.fullmatch(r"[a-z0-9-]+", v["slug"]), v["slug"]
    return {
        "slug": v["slug"],
        "name": v["name"],
        "hood": v.get("neighborhood", ""),
        "borough": v.get("borough", ""),
        "type": v.get("type", ""),
        "status": v.get("status", "open"),
        "status_note": v.get("status_note", "") if v.get("status") != "open" else "",
        "url": f"venues/{v['slug']}.html",
        "tags": tags,
        "aliases": chat.get("aliases") or [],
        "cover": _fact(v.get("cover"), default="likely"),
        "dress": _fact(v.get("dress"), "answer"),  # page shows no chip when dress has no status
        "age": _fact(v.get("age"), default="likely"),
        "hours": _fact(v.get("hours"), default="likely"),
        # structured week for "open tonight" (js/live.js); only "fixed" venues are ever shown as open
        "week": (v.get("hours") or {}).get("week") or {},
        "hours_kind": (v.get("hours") or {}).get("kind") or "",
        "hours_status": (v.get("hours") or {}).get("status") or "likely",
        "hours_note": (v.get("hours") or {}).get("note") or "",
        "howto": _fact(v.get("getting_in"), default="likely"),
        "price": _fact(v.get("price"), default="likely"),
        "subway": _fact(v.get("subway"), default="likely"),
        "skip": v.get("skip_if") or [],
        "verified": fmt_date(v.get("checked", "2026-10-18")),
        # card photo for js/tonight.js; empty when we hold no licensed photo
        "photo": f"img/{v['slug']}-640.webp" if _has_photo(v) else "",
    }


def _plan(p):
    assert re.fullmatch(r"[a-z0-9-]+", p["slug"]), p["slug"]
    return {
        "slug": p["slug"],
        "title": p["title"],
        "url": f"plans/{p['slug']}.html",
        "group": p.get("group"),
        "blurb": (p.get("blurb") or "").strip(),
        "options": [{"name": o["name"], "low": o["low"], "high": o["high"], "tag": o.get("tag", ""),
                     "label": LABEL.get(o.get("status") or "likely", "").strip()}
                    for o in p.get("options", [])],
        "combo": p.get("combo"),
    }


def _attr(text, name):
    m = re.search(rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"', text, re.I)
    return htmlmod.unescape(m.group(1)).strip() if m else ""


def _title(text):
    m = re.search(r"<title>([^<]+)</title>", text, re.I)
    if not m:
        return ""
    title = htmlmod.unescape(m.group(1)).strip()
    return re.sub(r"\s+\|\s+NY Nightlife\s*$", "", title).strip()


def _is_redirect(text):
    low = text.lower()
    return 'http-equiv="refresh"' in low or ("location.replace" in low and "noindex" in low)


def collect_guides(out):
    """Canonical /guides pages only. Redirect stubs are left out."""
    root = pathlib.Path(out)
    guides = []
    for f in sorted((root / "guides").glob("*.html")):
        rel = f"guides/{f.name}"
        if rel in redirects.REDIRECTS:
            continue
        text = f.read_text(encoding="utf-8")
        if _is_redirect(text):
            continue
        slug = f.stem
        title = _title(text) or slug.replace("-", " ")
        blurb = _attr(text, "description")
        guides.append({
            "slug": slug,
            "title": title,
            "url": rel,
            "blurb": blurb,
            "aliases": list(GUIDE_ALIASES.get(slug, [])),
        })
    return guides


def collect_html_plans(out, playbooks):
    """Plan pages that have no playbook JSON still belong in Nyla's knowledge."""
    root = pathlib.Path(out)
    have = {p["slug"] for p in playbooks}
    extra = []
    for f in sorted((root / "plans").glob("*.html")):
        if f.stem == "index":
            continue
        rel = f"plans/{f.name}"
        if rel in redirects.REDIRECTS or f.stem in have:
            continue
        text = f.read_text(encoding="utf-8")
        if _is_redirect(text):
            continue
        slug = f.stem
        assert re.fullmatch(r"[a-z0-9-]+", slug), slug
        extra.append({
            "slug": slug,
            "title": _title(text) or slug.replace("-", " "),
            "url": rel,
            "group": None,
            "blurb": _attr(text, "description"),
            "options": [],
            "combo": None,
        })
    return extra


def compact_events(events_feed):
    rows = []
    for ev in (events_feed or {}).get("events") or []:
        if not ev.get("start"):
            continue
        row = {}
        for key in EVENT_FIELDS:
            value = ev.get(key)
            if value not in (None, ""):
                row[key] = value
        if row.get("title") and row.get("start"):
            rows.append(row)
    return rows


def build(write, fmt_date, vs, playbooks, generated, guides=None, events_feed=None, extra_plans=None):
    feed_fetched = (events_feed or {}).get("fetched_at") or None
    plans = [_plan(p) for p in playbooks]
    # HTML-only plan pages are appended after the priced playbooks so existing
    # tests that look up the bachelorette book still see it when they want it.
    # js/concierge.js must pick a plan by question, not by plans[0].
    if extra_plans:
        plans = plans + list(extra_plans)
    if guides is None:
        guides = []
    data = {
        "schema": 3,
        "generated": generated,
        "feed_fetched_at": feed_fetched,
        "venues": [_venue(v, fmt_date) for v in sorted(vs, key=lambda v: v["name"].lower())],
        "plans": plans,
        "guides": guides,
        "events": compact_events(events_feed),
    }
    write("/data/venues.json", json.dumps(data, ensure_ascii=False, indent=1))
    return data
