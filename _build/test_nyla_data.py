"""Fail the Daily build if Nyla's knowledge is stale or incomplete.

Her answers come from data/venues.json. That file must be rebuilt from the
same venue files, events feed, guides, and hours as the rest of the site.
Run after a build:  python _build/test_nyla_data.py [built-site-folder]
"""
from __future__ import annotations

import json
import pathlib
import sys

import events
import nyla
import redirects

ROOT = pathlib.Path(__file__).resolve().parent
SITE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent).resolve()
SRC_VENUES = ROOT / "data" / "venues"


def fail(problems, msg):
    problems.append(msg)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return exc


def main():
    problems = []
    data_path = SITE / "data" / "venues.json"
    feed_path = SITE / "data" / "events.json"
    raw = load_json(data_path)
    if isinstance(raw, Exception):
        fail(problems, f"cannot read {data_path}: {raw}")
        _report(problems)
        return
    feed = load_json(feed_path)
    if isinstance(feed, Exception):
        fail(problems, f"cannot read {feed_path}: {feed}")
        feed = {}

    if raw.get("schema") != 3:
        fail(problems, f"data/venues.json schema is {raw.get('schema')!r}, expected 3")

    generated = events.parse_when(raw.get("generated"))
    feed_at = events.parse_when(raw.get("feed_fetched_at"))
    public_at = events.parse_when((feed or {}).get("fetched_at"))

    if not generated:
        fail(problems, f"generated is missing or unreadable: {raw.get('generated')!r}")
    if not public_at:
        fail(problems, f"data/events.json has no fetched_at: {(feed or {}).get('fetched_at')!r}")
    if not feed_at:
        fail(problems, f"feed_fetched_at is missing or unreadable: {raw.get('feed_fetched_at')!r}")
    elif public_at and feed_at != public_at:
        fail(
            problems,
            "Nyla feed_fetched_at is not the same as data/events.json: "
            f"{raw.get('feed_fetched_at')} vs {(feed or {}).get('fetched_at')}",
        )
    if generated and public_at and generated < public_at:
        fail(
            problems,
            "Nyla generated is older than the events feed: "
            f"{raw.get('generated')} < {(feed or {}).get('fetched_at')}",
        )

    src_slugs = sorted(p.stem for p in SRC_VENUES.glob("*.json"))
    got = raw.get("venues") or []
    got_slugs = [v.get("slug") for v in got]
    missing = [s for s in src_slugs if s not in got_slugs]
    extra = [s for s in got_slugs if s not in src_slugs]
    if missing:
        fail(problems, "Nyla is missing venues: " + ", ".join(missing))
    if extra:
        fail(problems, "Nyla has unknown venues: " + ", ".join(extra))
    if len(got_slugs) != len(set(got_slugs)):
        fail(problems, "Nyla venue list has duplicate slugs")

    for v in got:
        slug = v.get("slug")
        if not (v.get("hours") or "").strip():
            fail(problems, f"{slug}: hours missing")
        if v.get("hours_kind") == "fixed" and not (v.get("week") or {}):
            fail(problems, f"{slug}: fixed hours but no week map")

    expected_guides = {g["slug"] for g in nyla.collect_guides(SITE)}
    # Also require every non-redirect guide file under the built site, in case
    # collect_guides and the test ever drift.
    for f in sorted((SITE / "guides").glob("*.html")):
        rel = f"guides/{f.name}"
        if rel in redirects.REDIRECTS:
            continue
        text = f.read_text(encoding="utf-8")
        if nyla._is_redirect(text):
            continue
        expected_guides.add(f.stem)
    got_guides = {g.get("slug") for g in (raw.get("guides") or [])}
    if expected_guides - got_guides:
        fail(problems, "Nyla is missing guides: " + ", ".join(sorted(expected_guides - got_guides)))
    if got_guides - expected_guides:
        fail(problems, "Nyla has unknown guides: " + ", ".join(sorted(got_guides - expected_guides)))
    if not expected_guides:
        fail(problems, "no canonical guides found in the built site")

    expected_events = nyla.compact_events(feed if isinstance(feed, dict) else {})
    got_events = raw.get("events") or []
    exp_ids = [e.get("id") or f"{e.get('title')}|{e.get('start')}" for e in expected_events]
    got_ids = [e.get("id") or f"{e.get('title')}|{e.get('start')}" for e in got_events]
    if exp_ids != got_ids:
        fail(
            problems,
            "Nyla events do not match the public feed: "
            f"{len(got_ids)} in venues.json vs {len(exp_ids)} in events.json",
        )

    _report(problems)


def _report(problems):
    if problems:
        print(f"FAIL {len(problems)} Nyla data check(s):")
        for msg in problems:
            print(" -", msg)
        sys.exit(1)
    print("Nyla data is in sync with the venues, events feed, guides, and hours")
    sys.exit(0)


if __name__ == "__main__":
    main()
