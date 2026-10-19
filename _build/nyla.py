"""Data for Nyla, the site chatbot (js/concierge.js).

Writes /data/venues.json from the same verified venue + playbook JSON the pages
are built from, so her answers can never drift from what the pages say.
Labels mirror the page chips exactly (see build.fact / STATUS_CHIP):
"1 source", "unconfirmed", "not found yet"; an empty value reads "Not found yet".
Tags + aliases come from each venue's "chat" block.
"""
import json
import re

LABEL = {"likely": " (1 source)", "unconfirmed": " (unconfirmed)", "unknown": " (not found yet)"}
TAGS = {"rooftop", "cocktail", "club", "live", "ticketed", "no_cover", "dress_rule", "under21"}


def _fact(f, key="value", default=None):
    """Value plus its status label, using the same status rule as the page."""
    f = f or {}
    val = (f.get(key) or "").strip()
    if not val:
        return "Not found yet"
    st = f.get("status") or default
    return val + LABEL.get(st, "")


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
        "howto": _fact(v.get("getting_in"), default="likely"),
        "price": _fact(v.get("price"), default="likely"),
        "subway": _fact(v.get("subway"), default="likely"),
        "skip": v.get("skip_if") or [],
        "verified": fmt_date(v.get("checked", "2026-10-18")),
    }


def _plan(p):
    assert re.fullmatch(r"[a-z0-9-]+", p["slug"]), p["slug"]
    return {
        "title": p["title"],
        "url": f"plans/{p['slug']}.html",
        "group": p.get("group"),
        "options": [{"name": o["name"], "low": o["low"], "high": o["high"], "tag": o.get("tag", ""),
                     "label": LABEL.get(o.get("status") or "likely", "").strip()}
                    for o in p.get("options", [])],
        "combo": p.get("combo"),
    }


def build(write, fmt_date, vs, playbooks, generated):
    data = {
        "schema": 2,
        "generated": generated,
        "venues": [_venue(v, fmt_date) for v in sorted(vs, key=lambda v: v["name"].lower())],
        "plans": [_plan(p) for p in playbooks],
    }
    write("/data/venues.json", json.dumps(data, ensure_ascii=False, indent=1))
    return data
