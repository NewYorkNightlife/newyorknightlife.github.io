"""Fetcher tests: parks/permits filters, de-dupe, New York time, fallback, Ticketmaster terms.

Run: python _build/test_events.py
"""
import datetime as dt
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import events  # noqa: E402
import present  # noqa: E402

fails = 0
NY = events.NY


def check(name, cond):
    global fails
    if not cond:
        fails += 1
        print("FAIL", name)


def at(iso):
    return dt.datetime.fromisoformat(iso).replace(tzinfo=NY)


NOW = at("2026-11-11T21:00:00")


def test_filters():
    check("zumba dropped", not events.parks_keep({
        "title": "Zumba", "categories": "Fitness | Dance Classes | Exercise Classes"}))
    check("canceled dropped", not events.parks_keep({
        "title": "CANCELED: Jazz", "categories": "Concerts"}))
    check("concert kept", events.parks_keep({
        "title": "Stage Band", "categories": "Concerts | Art"}))
    check("kids theater dropped", not events.parks_keep({
        "title": "Three Bears", "categories": "Festivals | Best for Kids | Theater"}))
    check("dance show kept", events.parks_keep({
        "title": "LoopCurrent", "categories": "Dance | Art"}))
    check("health permit dropped", not events.permits_keep({
        "event_name": "Street Health Outreach", "event_type": "Street Event"}))
    check("festival kept", events.permits_keep({
        "event_name": "Veterans Day Festival", "event_type": "Street Festival"}))
    check("soccer dropped", not events.permits_keep({
        "event_name": "Soccer - Non Regulation", "event_type": "Street Festival"}))


def test_time():
    late = events.parse_when("2026-11-15T00:30:00.000")
    check("naive time is New York", late.tzinfo is not None and late.utcoffset() == dt.timedelta(hours=-5))
    check("past midnight stays 12:30am", late.hour == 0 and late.minute == 30)
    check("utc ticketmaster converts", events.parse_when("2026-11-15T05:30:00Z").hour == 0)
    check("1am is still tonight", events.in_tonight(at("2026-11-15T00:30:00"), at("2026-11-15T01:00:00")))
    check("10pm is that night", events.in_tonight(at("2026-11-14T22:00:00"), at("2026-11-15T01:00:00")))
    check("next evening is not tonight", not events.in_tonight(at("2026-11-15T18:00:00"), at("2026-11-15T01:00:00")))
    kept = events.drop_past([
        {"start": "2026-11-11T18:00:00-05:00", "end": "2026-11-11T19:00:00-05:00"},
        {"start": "2026-11-11T22:00:00-05:00", "end": "2026-11-11T23:00:00-05:00"},
    ], NOW)
    check("ended event dropped", len(kept) == 1 and kept[0]["start"].startswith("2026-11-11T22"))


def test_dedupe_and_fallback():
    rows = [
        {"id": "a", "title": "Stage Band", "venue_name": "Wave Hill", "start": "2026-11-15T14:00:00-05:00", "source": "nyc_parks"},
        {"id": "b", "title": "Stage Band!", "venue_name": "Wave Hill", "start": "2026-11-15T14:20:00-05:00", "source": "nyc_parks"},
        {"id": "c", "title": "Stage Band", "venue_name": "Wave Hill", "start": "2026-11-15T18:00:00-05:00", "source": "nyc_parks"},
    ]
    check("near-duplicate collapsed", len(events.dedupe(rows)) == 2)
    previous = {"events": [
        {"id": "p", "source": "nyc_parks", "title": "Old", "venue_name": "Park", "start": "2026-11-11T22:00:00-05:00"},
        {"id": "t", "source": "ticketmaster", "title": "Show", "venue_name": "Hall",
         "start": "2026-11-12T20:00:00-05:00", "fetched_at": "2026-11-09T12:00:00-05:00"},
    ], "listings": []}
    events_out, listings, status = events.assemble(previous, {
        "nyc_parks": {"ok": False, "error": "timeout"},
        "nyc_permits": {"ok": True, "events": [], "fetched_at": "2026-11-11T21:00:00-05:00"},
        "ticketmaster": {"skipped": True, "reason": "no key"},
        "viator": {"skipped": True, "reason": "no key"},
    }, NOW)
    check("parks failure keeps last good", any(ev["id"] == "p" for ev in events_out))
    check("stale ticketmaster cache dropped", all(ev["source"] != "ticketmaster" for ev in events_out))
    check("permits success can be empty", status["nyc_permits"]["ok"] and status["nyc_permits"]["count"] == 0)
    fresh = dict(previous["events"][1], fetched_at="2026-11-11T20:00:00-05:00")
    kept, _, _ = events.assemble({"events": [fresh], "listings": []}, {
        "nyc_parks": {"ok": True, "events": []},
        "nyc_permits": {"ok": True, "events": []},
        "ticketmaster": {"ok": False, "error": "down"},
        "viator": {"skipped": True},
    }, NOW)
    check("fresh ticketmaster fallback kept", any(ev["id"] == "t" for ev in kept))
    check("no listings invented", listings == [])


def _tm(name, segment, genre="", **extra):
    ev = {
        "id": extra.get("id", name),
        "name": name,
        "test": False,
        "url": extra.get("url", "https://www.ticketmaster.com/event/" + name.replace(" ", "")),
        "dates": {"start": {"dateTime": extra.get("when", "2026-11-12T01:00:00Z")}},
        "classifications": [{"segment": {"name": segment}, "genre": {"name": genre}, "subGenre": {"name": ""}}],
        "images": extra.get("images", [
            {"url": "https://s1.ticketm.net/dam/a/big.jpg", "width": 2048, "height": 1152},
            {"url": "https://s1.ticketm.net/dam/a/mid.jpg", "width": 640, "height": 360, "fallback": False},
            {"url": "https://evil.example/x.jpg", "width": 640, "height": 360},
        ]),
        "priceRanges": [{"min": 45}],
        "_embedded": {"venues": [{
            "name": extra.get("venue", "Brooklyn Steel"),
            "city": {"name": "Brooklyn"},
            "state": {"stateCode": "NY"},
            "location": {"latitude": "40.719", "longitude": "-73.957"},
        }]},
    }
    return ev


def test_ticketmaster():
    check("no seatgeek or RA", not (events.FETCH_HOSTS & events.BLOCKED_HOSTS))
    for bad in ("https://api.seatgeek.com/2/events", "https://ra.co/events"):
        try:
            events.fetch(bad)
            check("refused " + bad, False)
        except ValueError:
            pass
    music = events._tm_one(_tm("Band", "Music", "Rock"), "2026-11-11T21:00:00-05:00")
    comedy = events._tm_one(_tm("Comic", "Arts & Theatre", "Comedy"), "2026-11-11T21:00:00-05:00")
    theatre = events._tm_one(_tm("Play", "Arts & Theatre", "Theatre"), "2026-11-11T21:00:00-05:00")
    night = events._tm_one(_tm("DJ", "Music", "Dance/Electronic"), "2026-11-11T21:00:00-05:00")
    sport = events._tm_one(_tm("Knicks", "Sports", "Basketball"), "2026-11-11T21:00:00-05:00")
    check("music", music and music["category"] == "music")
    check("comedy", comedy and comedy["category"] == "comedy")
    check("theatre", theatre and theatre["category"] == "theatre")
    check("nightlife", night and night["category"] == "nightlife")
    check("sports dropped", sport is None)
    check("image hotlinked not stored", music["image_url"].endswith("/mid.jpg") and not music.get("image_local")
          and "_image_remote" not in music)
    check("off-cdn image refused", not events.tm_image_ok("https://evil.example/x.jpg"))
    check("ticket url has no affiliate", "pid=" not in music["url"] and "campaign=" not in music["url"]
          and music["url"].startswith("https://www.ticketmaster.com/event/"))
    check("http upgraded", events._tm_url("http://www.ticketmaster.com/e/1").startswith("https://"))
    check("javascript url dropped", events._tm_url("javascript:alert(1)") == "")
    jersey = _tm("NJ", "Music", "Rock", venue="Prudential Center")
    jersey["_embedded"]["venues"][0]["location"] = {"latitude": "40.733", "longitude": "-74.171"}
    jersey["_embedded"]["venues"][0]["city"] = {"name": "Newark"}
    jersey["_embedded"]["venues"][0]["state"] = {"stateCode": "NJ"}
    check("outside nyc dropped", events._tm_one(jersey, "2026-11-11T21:00:00-05:00") is None)

    os.environ["TICKETMASTER_API_KEY"] = "test-key-not-real"
    seen = []

    def get_json(url):
        seen.append(url)
        if "classificationName=dance" in url:
            raise ValueError("unknown classification")
        if "comedy" in url:
            return {"_embedded": {"events": [_tm("Comic", "Arts & Theatre", "Comedy")]}}
        if "Arts" in url or "Theatre" in url:
            return {"_embedded": {"events": [_tm("Play", "Arts & Theatre", "Theatre")]}}
        return {"_embedded": {"events": [_tm("Band", "Music", "Rock"), _tm("DJ", "Music", "Dance/Electronic")]}}

    try:
        rows = events.fetch_ticketmaster(get_json, NOW)
    finally:
        os.environ.pop("TICKETMASTER_API_KEY", None)
    check("four queries and a bad one is skipped", len(seen) == 4 and rows and len(rows) == 4)
    check("queries ask for music comedy theatre dance",
          any("classificationName=music" in u for u in seen)
          and any("comedy" in u for u in seen)
          and any("Arts" in u for u in seen)
          and any("classificationName=dance" in u for u in seen))
    check("no affiliate on the request", all("campaign=" not in u and "pid=" not in u for u in seen))
    check("key not echoed into rows", all("test-key-not-real" not in json_row(r) for r in rows))
    card = present.event_card(music)
    check("card hotlinks the event image", 'src="https://s1.ticketm.net/dam/a/mid.jpg"' in card)
    check("card links the event url", music["url"] in card and "sponsored" not in card)
    check("card attributes ticketmaster", "Ticketmaster" in card)
    os.environ.pop("TICKETMASTER_API_KEY", None)
    check("missing key skips", events.fetch_ticketmaster(get_json, NOW) is None)


def json_row(row):
    return str(row)


def test_match_and_words():
    venues = [{"slug": "house-of-yes", "name": "House of Yes", "borough": "Brooklyn", "neighborhood": "Bushwick"}]
    hit = events.match_venue("House of Yes", venues)
    check("venue match", hit and hit["slug"] == "house-of-yes")
    check("short name skipped", events.match_venue("Box", [{"slug": "the-box", "name": "The Box"}]) is None)
    sample = {
        "name": "Death & Co", "type": "cocktail bar", "neighborhood": "East Village", "borough": "Manhattan",
        "status": "open", "checked": "2026-10-18",
        "dress": {"answer": "None published", "detail": "The venue does not post one."},
        "cover": {"value": "None listed"},
        "hours": {"value": "Sun–Wed 6pm–1am; Thu–Sat 6pm–2am"},
        "getting_in": {"value": "Walk-ins welcome."},
        "address": "433 E 6th St, New York, NY 10009",
    }
    n = len(present.short_answer(sample).split())
    check(f"short answer length {n}", 40 <= n <= 60)
    faqs = present.venue_faqs(sample)
    check("faq count", 4 <= len(faqs) <= 6)
    schema = present.event_schema(music_public())
    check("event schema", schema["@type"] == "Event" and schema["startDate"] and schema["location"]["name"])


def music_public():
    return events._tm_one(_tm("Band", "Music", "Rock"), "2026-11-11T21:00:00-05:00")


if __name__ == "__main__":
    test_filters()
    test_time()
    test_dedupe_and_fallback()
    test_ticketmaster()
    test_match_and_words()
    print(f"{'OK' if not fails else str(fails) + ' FAILED'}: event fetcher tests")
    sys.exit(1 if fails else 0)
