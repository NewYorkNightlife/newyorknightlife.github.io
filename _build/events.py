"""Fetch what's on in NYC and write `_build/data/events/latest.json`.

Sources, in order:
  nyc_parks      NYC Open Data `w3wp-dpdi` (no key)
  nyc_permits    NYC Open Data `tvpp-9vvx` (no key)
  ticketmaster   Discovery API, only if TICKETMASTER_API_KEY or TM_API_KEY is set
  viator         Partner API Basic search, only if VIATOR_API_KEY is set

A source that fails keeps its last good events. A missing key is a skip, not a
failure, and it does not wipe events already saved for that source. Past events
are dropped every run. Nothing here is SeatGeek or Resident Advisor.

    python _build/events.py

Stdlib only, plus Pillow when an event image can be stored locally. Images are
never hotlinked: a download that fails just leaves the card without a photo.
"""
import datetime as dt
import json
import os
import pathlib
import re
import urllib.parse
import urllib.request

try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
except Exception:
    NY = dt.timezone(dt.timedelta(hours=-5))

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT.parent
SNAP = ROOT / "data" / "events" / "latest.json"
IMG_DIR = SITE / "img" / "events"
UA = "nynightlife.com events (+https://nynightlife.com/contact.html)"
MAX_BYTES = 2_500_000
TIMEOUT = 25

# DMA 345 is on Madison Square Garden's Discovery venue record (dmas[].id).
# Confirmed from the public Discovery venue example, 2026-11-11. Events are
# still limited to a NYC bounding box so Newark listings in the same DMA drop.
TM_DMA = "345"
NYC_BOX = (40.49, 40.92, -74.27, -73.70)  # lat min, lat max, lng min, lng max

FETCH_HOSTS = {
    "data.cityofnewyork.us",
    "app.ticketmaster.com",
    "api.viator.com",
}
# Never these. Tests lock the set.
BLOCKED_HOSTS = {
    "seatgeek.com", "api.seatgeek.com", "ra.co", "www.ra.co",
    "residentadvisor.net", "www.residentadvisor.net",
}
IMAGE_SUFFIXES = (
    "nycgovparks.org", "ticketm.net", "ticketmaster.com", "livenation.com",
    "tripadvisor.com", "tacdn.com", "viator.com",
)

PARKS = "https://data.cityofnewyork.us/resource/w3wp-dpdi.json"
PERMITS = "https://data.cityofnewyork.us/resource/tvpp-9vvx.json"
PARKS_PAGE = "https://data.cityofnewyork.us/Recreation/NYC-Parks-Public-Events-Upcoming-14-Days/w3wp-dpdi"
PERMITS_PAGE = "https://data.cityofnewyork.us/City-Government/NYC-Permitted-Event-Information/tvpp-9vvx"
TM_EVENTS = "https://app.ticketmaster.com/discovery/v2/events.json"
VIATOR_SEARCH = "https://api.viator.com/partner/products/search"

NIGHT_CATS = {
    "concerts", "festivals", "fall festivals", "theater", "theatre",
    "movies", "film", "films", "music", "live music", "performance", "performances",
}
PERMIT_TYPES = {"street festival", "single block festival", "block party", "parade"}
PERMIT_DENY = (
    "health outreach", "medical", "sampling", "parking", "coffee", "shooting",
    "rigging", "load in", "load out", "soccer", "football", "baseball", "softball",
    "youth sport", "sport -",
)
SOURCES = ("nyc_parks", "nyc_permits", "ticketmaster", "viator")


class _Allow(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts):
        super().__init__()
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = urllib.parse.urlsplit(newurl)
        host = (new.hostname or "").lower()
        if new.scheme not in ("https", "http") or not _host_ok(host, self.hosts):
            raise urllib.error.HTTPError(newurl, code, "redirect refused", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _host_ok(host, allowed):
    host = (host or "").lower()
    if host in BLOCKED_HOSTS or any(host == b or host.endswith("." + b) for b in BLOCKED_HOSTS):
        return False
    return any(host == h or host.endswith("." + h) for h in allowed)


def fetch(url, accept="application/json", method="GET", body=None, headers=None, hosts=None):
    """HTTPS (or http only for image CDNs that still publish http) on an allowlisted host."""
    hosts = hosts or FETCH_HOSTS
    p = urllib.parse.urlsplit(url)
    host = (p.hostname or "").lower()
    if p.scheme not in ("https", "http") or p.username or p.port or not _host_ok(host, hosts):
        raise ValueError("fetch refused: " + host)
    if p.scheme != "https" and not url.lower().split("?", 1)[0].endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        raise ValueError("fetch refused: " + host)
    hdrs = {"User-Agent": UA, "Accept": accept}
    if headers:
        hdrs.update(headers)
    data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    opener = urllib.request.OpenerDirector()
    opener.add_handler(urllib.request.HTTPSHandler())
    if p.scheme == "http":
        opener.add_handler(urllib.request.HTTPHandler())
    opener.add_handler(_Allow(hosts))
    opener.add_handler(urllib.request.HTTPDefaultErrorHandler())
    opener.add_handler(urllib.request.HTTPErrorProcessor())
    with opener.open(req, timeout=TIMEOUT) as r:
        blob = r.read(MAX_BYTES + 1)
    if len(blob) > MAX_BYTES:
        raise ValueError("response too large")
    return blob


def fetch_json(url, **kw):
    return json.loads(fetch(url, **kw).decode("utf-8"))


def local_now():
    return dt.datetime.now(NY)


def parse_when(value):
    """NYC Open Data wall times have no offset. Treat those as America/New_York.
    Values that already carry an offset (Ticketmaster UTC) are converted."""
    if not value:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    if s.endswith(".000"):
        s = s[:-4]
    try:
        parsed = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=NY)
    return parsed.astimezone(NY)


def iso(when):
    return when.isoformat(timespec="seconds") if when else None


def clean(text, limit=220):
    s = re.sub(r"<[^>]*>", " ", text or "")
    s = s.replace("<", " ").replace(">", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= limit:
        return s
    return s[: limit - 1].rstrip() + "…"


def norm(text):
    s = re.sub(r"[^a-z0-9]+", " ", (text or "").lower())
    s = re.sub(r"^(the|a|an) ", "", s.strip())
    return re.sub(r"\s+", " ", s).strip()


def https_parks(url):
    if (url or "").startswith("http://") and "nycgovparks.org" in url:
        return "https://" + url[len("http://"):]
    return url or ""


def _cats(row):
    return {c.strip().lower() for c in (row.get("categories") or "").split("|") if c.strip()}


def parks_keep(row):
    """Concerts, festivals, theater, and dance performances. Not fitness classes."""
    title = (row.get("title") or "").strip()
    if not title or title.upper().startswith("CANCEL"):
        return False
    cats = _cats(row)
    if "recreation center programming" in cats and not (cats & {"concerts", "theater", "theatre", "festivals", "fall festivals"}):
        return False
    if cats & NIGHT_CATS:
        if "best for kids" in cats and not (cats & {"concerts", "music", "live music"}):
            return False
        return True
    if "dance" in cats and "dance classes" not in cats and "best for kids" not in cats:
        low = title.lower()
        if any(w in low for w in ("aerobics", "zumba", "fitness", "tiny tots")):
            return False
        if cats & {"fitness", "exercise classes", "shape up nyc"}:
            return False
        return True
    return False


def parks_category(row):
    cats = _cats(row)
    if cats & {"concerts", "music", "live music"}:
        return "music"
    if cats & {"festivals", "fall festivals"}:
        return "festival"
    if "dance" in cats:
        return "club"
    return "parks"


def _coords(value):
    if not value or "," not in str(value):
        return None, None
    try:
        lat, lng = (float(x) for x in str(value).split(",", 1))
    except ValueError:
        return None, None
    return lat, lng


def in_nyc(lat, lng):
    if lat is None or lng is None:
        return False
    s, n, w, e = NYC_BOX
    return s <= lat <= n and w <= lng <= e


def permits_keep(row):
    typ = (row.get("event_type") or "").strip().lower()
    name = (row.get("event_name") or "").strip().lower()
    if not name or name.startswith("cancel"):
        return False
    if any(d in name or d in typ for d in PERMIT_DENY):
        return False
    return typ in PERMIT_TYPES


# A show with no end time is treated as three hours long, here and in js/tonight.js.
ASSUMED_LENGTH = dt.timedelta(hours=3)
WD_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WD_LONG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def night_window(now):
    """5pm through 5am New York time.

    From midnight until 5am the window is still the previous evening. The
    date visitors should see is the date of that 5pm, not the morning's date.
    """
    if now is None:
        return None, None
    now = now.astimezone(NY)
    if now.hour < 5:
        begin = (now - dt.timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
    else:
        begin = now.replace(hour=17, minute=0, second=0, microsecond=0)
    return begin, begin + dt.timedelta(hours=12)


def night_facts(now):
    begin, end = night_window(now)
    return {
        "begin": begin,
        "end": end,
        "short": WD_SHORT[begin.weekday()],
        "long": WD_LONG[begin.weekday()],
        "mon": MONTHS[begin.month - 1],
        "day": begin.day,
        "iso": begin.date().isoformat(),
    }


def in_tonight(start, now):
    """True when `start` falls in the New York night that contains `now`."""
    if start is None or now is None:
        return False
    begin, end = night_window(now)
    return begin <= start.astimezone(NY) < end


def event_end(ev, start=None):
    start = start or parse_when((ev or {}).get("start"))
    if start is None:
        return None
    return parse_when((ev or {}).get("end")) or (start + ASSUMED_LENGTH)


def has_ended(ev, now, start=None):
    """An event has ended when its end (or start plus three hours) is at or before `now`."""
    if now is None:
        return False
    end = event_end(ev, start)
    if end is None:
        return False
    return end <= now.astimezone(NY)


def refresh_stamp(value):
    """The data's own New York time, so 'Updated' is not mistaken for today's date."""
    parsed = parse_when(value)
    if not parsed:
        return (str(value or ""))[:10]
    hour = parsed.hour % 12 or 12
    ap = "am" if parsed.hour < 12 else "pm"
    return f"{parsed.strftime('%Y-%m-%d')} {hour}:{parsed.minute:02d}{ap} ET"


def record(source, ident, title, start, end, venue_name, category, url, **extra):
    ev = {
        "id": f"{source}:{ident}",
        "source": source,
        "title": clean(title, 140),
        "start": iso(start),
        "end": iso(end) if end else None,
        "venue_name": clean(venue_name, 120),
        "venue_slug": extra.get("venue_slug"),
        "lat": extra.get("lat"),
        "lng": extra.get("lng"),
        "borough": extra.get("borough") or "",
        "neighborhood": extra.get("neighborhood") or "",
        "category": category,
        "price_min": extra.get("price_min"),
        "url": url or "",
        "image_url": "",
        "image_local": extra.get("image_local") or "",
        "image_credit": extra.get("image_credit") or "",
        "fetched_at": extra.get("fetched_at") or iso(local_now()),
        "blurb": clean(extra.get("blurb") or "", 180),
    }
    return ev


def from_park(row, fetched_at):
    start = parse_when(row.get("starttime"))
    if not start:
        return None
    end = parse_when(row.get("endtime"))
    link = https_parks(((row.get("link") or {}) if isinstance(row.get("link"), dict) else {}).get("url") or "")
    image = row.get("image") if isinstance(row.get("image"), dict) else {}
    lat, lng = _coords(row.get("coordinates"))
    place = row.get("parknames") or row.get("location") or "NYC Park"
    return record(
        "nyc_parks", row.get("guid") or norm(row.get("title")), row.get("title"), start, end, place,
        parks_category(row), link or PARKS_PAGE, fetched_at=fetched_at, lat=lat, lng=lng,
        blurb=row.get("description") or "", image_remote=https_parks(image.get("url") or ""),
        image_credit="NYC Parks" if image.get("url") else "")


def from_permit(row, fetched_at):
    start = parse_when(row.get("start_date_time"))
    if not start:
        return None
    end = parse_when(row.get("end_date_time"))
    place = row.get("event_location") or row.get("event_borough") or "New York"
    return record(
        "nyc_permits", row.get("event_id") or norm(row.get("event_name")), row.get("event_name"),
        start, end, place, "festival", PERMITS_PAGE, fetched_at=fetched_at,
        borough=row.get("event_borough") or "",
        blurb=(row.get("event_type") or "Permitted event") + " · NYC permitted event listing")


def attach_remote(ev, remote):
    if remote:
        ev["_image_remote"] = remote
    return ev


def _stamp_remote(ev, remote, credit):
    if remote:
        ev["_image_remote"] = remote
        if credit:
            ev["image_credit"] = credit
    return ev


def match_venue(name, venues):
    """Whole-name match against our venue list. Short names are skipped."""
    n = norm(name)
    if len(n) < 4:
        return None
    best = None
    for v in venues:
        vn = norm(v.get("name") or "")
        if len(vn) < 4:
            continue
        if n == vn or vn in n:
            if best is None or len(vn) > len(norm(best.get("name") or "")):
                best = v
    return best


def apply_matches(events, venues):
    for ev in events:
        hit = match_venue(ev.get("venue_name"), venues)
        if hit:
            ev["venue_slug"] = hit["slug"]
            if not ev.get("borough"):
                ev["borough"] = hit.get("borough") or ""
            if not ev.get("neighborhood"):
                ev["neighborhood"] = hit.get("neighborhood") or ""
    return events


def dedupe(events):
    """Collapse near-duplicates. Order follows start, then id, then title,
    so the same set of rows always keeps the same events."""
    kept, seen = [], set()
    ordered = sorted(events, key=lambda ev: (
        ev.get("start") or "", str(ev.get("id") or ""), ev.get("title") or ""))
    for ev in ordered:
        if ev.get("id") and ev["id"] in seen:
            continue
        if ev.get("id"):
            seen.add(ev["id"])
        start = parse_when(ev.get("start"))
        dup = False
        for prev in kept:
            if norm(prev.get("title")) != norm(ev.get("title")):
                continue
            if norm(prev.get("venue_name")) != norm(ev.get("venue_name")):
                continue
            other = parse_when(prev.get("start"))
            if start and other and abs(start - other) <= dt.timedelta(minutes=30):
                dup = True
                break
        if not dup:
            kept.append(ev)
    return kept


def drop_past(events, now):
    """Drop rows that have already ended. Rows that started earlier tonight and
    are still going stay, which is why the fetch window has to reach back to 5pm."""
    out = []
    for ev in events:
        start = parse_when(ev.get("start"))
        if not start or has_ended(ev, now, start):
            continue
        out.append(ev)
    return out


def assemble(previous, results, now):
    """Merge this run with the last good snapshot. Failed sources keep old rows.

    Viator rows are catalog listings, not showtimes, so they stay out of the
    dated event list and are not given a made-up start time.
    """
    prev_events = (previous or {}).get("events") or []
    prev_listings = (previous or {}).get("listings") or []
    by_source = {}
    for ev in prev_events:
        by_source.setdefault(ev.get("source"), []).append(ev)
    merged, status = [], {}
    listings = list(prev_listings)
    for source in SOURCES:
        res = results.get(source) or {"ok": False, "error": "not run"}
        if res.get("skipped"):
            status[source] = {"skipped": True, "reason": res.get("reason") or "no key"}
            if source != "viator":
                merged.extend(ev for ev in (by_source.get(source) or []) if tm_still_fresh(ev, now))
        elif res.get("ok"):
            rows = res.get("events") or []
            status[source] = {"ok": True, "count": len(rows), "fetched_at": res.get("fetched_at")}
            if source == "viator":
                listings = rows
            else:
                merged.extend(rows)
        else:
            status[source] = {"ok": False, "error": (res.get("error") or "failed")[:240]}
            if source != "viator":
                kept = [ev for ev in (by_source.get(source) or []) if tm_still_fresh(ev, now)]
                merged.extend(kept)
    events = dedupe(drop_past(merged, now))
    return events, listings, status


def fetch_start(now):
    """Earliest wall time to ask NYC Open Data for.

    Eight hours before the build is enough during the day. Once the night has
    started, the lower bound also has to reach that night's 5pm, or a run
    after 1am would miss a show that began at 5pm and is still going.
    """
    now = now.astimezone(NY)
    begin, _ = night_window(now)
    lookback = now - dt.timedelta(hours=8)
    if now >= begin:
        return min(begin, lookback)
    return lookback


def _window(now):
    start_at = fetch_start(now)
    end_at = now.astimezone(NY) + dt.timedelta(days=8)
    return start_at.strftime("%Y-%m-%dT%H:%M:%S"), end_at.strftime("%Y-%m-%dT%H:%M:%S")


def tm_range(now):
    """Ticketmaster startDateTime / endDateTime in UTC.

    Discovery's startDateTime drops events that have already started. The
    2026-11-18 04:18Z build was 23:18 in New York, so the query began at
    04:18Z and every show from 5pm to 11:18pm was excluded. The night window
    was then empty while the rest of the week (88 events, all later) remained.
    Once the night has begun, start at that night's 5pm. Before 5pm, start at
    the build clock so the first page of results is not filled with the morning.
    """
    now = now.astimezone(NY)
    begin, _ = night_window(now)
    start_at = begin if now >= begin else now
    end_at = now + dt.timedelta(days=7)
    start = start_at.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = end_at.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return start, end


def fetch_parks(get_json, now):
    start, end = _window(now)
    where = f"starttime >= '{start}' AND starttime < '{end}'"
    url = PARKS + "?" + urllib.parse.urlencode({"$where": where, "$order": "starttime", "$limit": "1000"})
    rows = get_json(url)
    fetched = iso(now)
    out = []
    for row in rows:
        if not parks_keep(row):
            continue
        ev = from_park(row, fetched)
        if not ev:
            continue
        image = row.get("image") if isinstance(row.get("image"), dict) else {}
        remote = https_parks(image.get("url") or "")
        _stamp_remote(ev, remote, "NYC Parks" if image.get("url") else "")
        host = (urllib.parse.urlsplit(remote).hostname or "").lower()
        if remote.startswith("https://") and (host == "nycgovparks.org" or host.endswith(".nycgovparks.org")):
            ev["image_url"] = remote
        out.append(ev)
    return out


def fetch_permits(get_json, now):
    start, end = _window(now)
    quoted = ",".join("'" + t.title() + "'" for t in ("Street Festival", "Single Block Festival", "Block Party", "Parade"))
    # SODA stores the types in title case as returned by the dataset.
    where = f"start_date_time >= '{start}' AND start_date_time < '{end}' AND event_type in({quoted})"
    url = PERMITS + "?" + urllib.parse.urlencode({"$where": where, "$order": "start_date_time", "$limit": "200"})
    try:
        rows = get_json(url)
    except Exception:
        url = PERMITS + "?" + urllib.parse.urlencode({
            "$where": f"start_date_time >= '{start}' AND start_date_time < '{end}'",
            "$order": "start_date_time", "$limit": "400"})
        rows = get_json(url)
    fetched = iso(now)
    out = []
    for row in rows:
        if not permits_keep(row):
            continue
        ev = from_permit(row, fetched)
        if ev:
            out.append(ev)
    return out


def _redact(msg):
    out = msg or ""
    for secret in (_tm_key(), _viator_key()):
        if secret:
            out = out.replace(secret, "REDACTED")
    return out


def _tm_key():
    return (os.environ.get("TICKETMASTER_API_KEY") or os.environ.get("TM_API_KEY") or "").strip()


def _viator_key():
    return (os.environ.get("VIATOR_API_KEY") or "").strip()


# One Discovery call each. Comedy is its own genre. "Arts & Theatre" is the
# segment name. Dance/electronic is the nightlife slice; a bad name is skipped
# inside fetch_ticketmaster so the other three still land.
TM_QUERIES = ("music", "comedy", "Arts & Theatre", "dance")
TM_MAX_AGE = dt.timedelta(hours=36)
TM_IMAGE_HOSTS = ("ticketm.net", "ticketmaster.com")


def _tm_names(ev):
    classes = ev.get("classifications") or []
    return " ".join(
        " ".join(str((c.get(k) or {}).get("name") or "") for k in ("segment", "genre", "subGenre", "type"))
        for c in classes).lower()


def _tm_category(ev):
    """music, comedy, theatre, nightlife. Sports and film stay out."""
    names = _tm_names(ev)
    if not names or "sport" in names or names.strip() == "film":
        return None
    if "comedy" in names:
        return "comedy"
    if any(k in names for k in ("dance", "electronic", "dj", "nightlife", "club")):
        return "nightlife"
    if "theatre" in names or "theater" in names:
        return "theatre"
    if "music" in names or "concert" in names:
        return "music"
    return None


def _tm_url(url):
    """The Discovery event URL, unchanged apart from http→https. No affiliate tags."""
    raw = (url or "").strip()
    if not raw:
        return ""
    parts = urllib.parse.urlsplit(raw)
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or not host or parts.username:
        return ""
    if parts.scheme == "http":
        parts = parts._replace(scheme="https")
    return urllib.parse.urlunsplit(parts)


def _tm_image(images):
    """A mid-size Discovery image URL to show beside this event. Not saved."""
    best, score = None, 10 ** 9
    for im in images or []:
        url = im.get("url") or ""
        host = (urllib.parse.urlsplit(url).hostname or "").lower()
        if not url or not _host_ok(host, TM_IMAGE_HOSTS):
            continue
        w = im.get("width") or 0
        if w < 200:
            continue
        gap = abs(w - 640) + (200 if im.get("fallback") else 0)
        if gap < score:
            best, score = im, gap
    return best


def tm_still_fresh(ev, now):
    """Ticketmaster rows older than the daily window are dropped, even on fallback."""
    if ev.get("source") != "ticketmaster":
        return True
    fetched = parse_when(ev.get("fetched_at"))
    return bool(fetched) and (now - fetched) <= TM_MAX_AGE


def tm_image_ok(url):
    host = (urllib.parse.urlsplit(url or "").hostname or "").lower()
    return bool(url) and _host_ok(host, TM_IMAGE_HOSTS)


def _tm_one(ev, fetched):
    if ev.get("test"):
        return None
    dates = (ev.get("dates") or {}).get("start") or {}
    if dates.get("dateTBA") or dates.get("dateTBD") or dates.get("timeTBA"):
        return None
    start = parse_when(dates.get("dateTime"))
    if not start:
        return None
    end = parse_when(((ev.get("dates") or {}).get("end") or {}).get("dateTime"))
    cat = _tm_category(ev)
    if not cat:
        return None
    url = _tm_url(ev.get("url") or "")
    if not url:
        return None
    venues = ((ev.get("_embedded") or {}).get("venues") or [{}])
    venue = venues[0] or {}
    city = ((venue.get("city") or {}).get("name") or "")
    state = ((venue.get("state") or {}).get("stateCode") or "")
    loc = venue.get("location") or {}
    try:
        lat = float(loc.get("latitude")) if loc.get("latitude") not in (None, "") else None
        lng = float(loc.get("longitude")) if loc.get("longitude") not in (None, "") else None
    except (TypeError, ValueError):
        lat = lng = None
    if state and state != "NY":
        return None
    if lat is not None and not in_nyc(lat, lng):
        return None
    if lat is None and not (state == "NY" and city.lower() in {
            "new york", "brooklyn", "queens", "bronx", "staten island", "manhattan"}):
        return None
    prices = ev.get("priceRanges") or []
    price = None
    currency = ""
    if prices and prices[0].get("min") is not None:
        try:
            price = float(prices[0]["min"])
        except (TypeError, ValueError):
            price = None
    if prices and prices[0].get("currency"):
        cur = str(prices[0]["currency"]).strip().upper()
        if re.fullmatch(r"[A-Z]{3}", cur):
            currency = cur
    image = _tm_image(ev.get("images") or [])
    addr = venue.get("address") or {}
    borough = city if city.lower() in {"brooklyn", "queens", "bronx", "staten island", "manhattan"} else ""
    if not borough and city.lower() == "new york":
        borough = "Manhattan"
    out = record(
        "ticketmaster", ev.get("id"), ev.get("name"), start, end, venue.get("name") or city or "New York",
        cat, url, fetched_at=fetched, lat=lat, lng=lng, borough=borough,
        price_min=price, image_credit="Ticketmaster" if image else "",
        blurb=", ".join(x for x in (addr.get("line1"), city) if x))
    if image:
        # Hotlinked beside this event only. Not written into the repo.
        out["image_url"] = image.get("url") or ""
        out["image_w"] = int(image.get("width") or 0) or None
        out["image_h"] = int(image.get("height") or 0) or None
    if currency:
        out["price_currency"] = currency
    # info / pleaseNote are the copy Ticketmaster publishes. The street address
    # stored in blurb is not a description.
    note = clean(ev.get("info") or ev.get("pleaseNote") or "", 400)
    if note:
        out["description"] = note
    status = str(((ev.get("dates") or {}).get("status") or {}).get("code") or "").lower()
    availability = {"onsale": "https://schema.org/InStock",
                    "offsale": "https://schema.org/SoldOut"}.get(status)
    if availability:
        out["offer_availability"] = availability
    return out


def fetch_ticketmaster(get_json, now):
    key = _tm_key()
    if not key:
        return None  # skipped
    fetched = iso(now)
    start, end = tm_range(now)
    out, misses = [], []
    for name in TM_QUERIES:
        q = {
            "apikey": key, "dmaId": TM_DMA, "classificationName": name,
            "startDateTime": start, "endDateTime": end, "size": "100", "page": "0",
            "sort": "date,asc", "includeTBA": "no", "includeTBD": "no", "includeTest": "no",
            "countryCode": "US",
        }
        try:
            payload = get_json(TM_EVENTS + "?" + urllib.parse.urlencode(q))
        except Exception as ex:
            # An unknown classification name should not blank music and comedy.
            misses.append(name + ": " + type(ex).__name__)
            continue
        for ev in ((payload.get("_embedded") or {}).get("events") or []):
            one = _tm_one(ev, fetched)
            if one:
                out.append(one)
    if misses and not out and len(misses) == len(TM_QUERIES):
        raise RuntimeError("ticketmaster: " + "; ".join(misses)[:180])
    return out


def _viator_one(prod, fetched):
    """A catalog product, not a showtime. `start` stays null on purpose."""
    title = prod.get("title") or ""
    blob = (title + " " + (prod.get("description") or "")).lower()
    if not any(w in blob for w in ("night", "cruise", "comedy", "bar", "rooftop", "speakeasy", "jazz", "club", "sunset")):
        return None
    if any(w in blob for w in ("cruise", "yacht", "boat", "sunset sail")):
        cat = "cruise"
    elif "comedy" in blob:
        cat = "comedy"
    else:
        cat = "tour"
    price = ((prod.get("pricing") or {}).get("summary") or {}).get("fromPrice")
    try:
        price = float(price) if price is not None else None
    except (TypeError, ValueError):
        price = None
    remote = ""
    for im in prod.get("images") or []:
        if not im.get("isCover") and remote:
            continue
        variants = im.get("variants") or []
        pick = None
        for v in variants:
            w = v.get("width") or 0
            if v.get("url") and 300 <= w <= 1000:
                pick = v["url"]
                break
        if not pick and variants:
            pick = variants[0].get("url") or ""
        if pick:
            remote = pick
            if im.get("isCover"):
                break
    out = record(
        "viator", prod.get("productCode") or norm(title), title, None, None,
        "Viator", cat, prod.get("productUrl") or "", fetched_at=fetched,
        price_min=price, image_credit="Viator" if remote else "",
        blurb=prod.get("description") or "")
    out["listing"] = True
    return _stamp_remote(out, remote, out["image_credit"])


def fetch_viator(post_json, now):
    key = _viator_key()
    if not key:
        return None
    fetched = iso(now)
    body = {
        "filtering": {"destination": "687"},
        "sorting": {"sort": "TRAVELER_RATING", "order": "DESCENDING"},
        "pagination": {"start": 1, "count": 20},
        "currency": "USD",
    }
    url = VIATOR_SEARCH + "?" + urllib.parse.urlencode({"campaign-value": "nynightlife-viator-api"})
    payload = post_json(url, body, key)
    out = []
    for prod in payload.get("products") or []:
        one = _viator_one(prod, fetched)
        if one:
            out.append(one)
        if len(out) >= 8:
            break
    return out


def _safe_id(ident):
    return re.sub(r"[^a-z0-9-]+", "-", ident.lower()).strip("-")[:80]


def store_image(ev):
    """Download one event image into img/events. Failure leaves the card photoless."""
    remote = ev.pop("_image_remote", "")
    if not remote:
        ev.pop("_image_remote", None)
        return ev
    try:
        from PIL import Image
        import io
    except Exception:
        return ev
    try:
        blob = fetch(remote, accept="image/*", hosts=IMAGE_SUFFIXES)
        im = Image.open(io.BytesIO(blob)).convert("RGB")
    except Exception:
        return ev
    w, h = im.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 5
    im = im.crop((left, top, left + side, top + side))
    im = im.resize((640, 800), Image.LANCZOS)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    name = _safe_id(ev["id"]) + ".webp"
    path = IMG_DIR / name
    im.save(path, "WEBP", quality=62, method=4)
    if path.stat().st_size > 150_000:
        im.save(path, "WEBP", quality=48, method=4)
    ev["image_local"] = "/img/events/" + name
    ev["image_w"], ev["image_h"] = 640, 800
    return ev


def write_snapshot(snap, path=None):
    """Replace the snapshot atomically. The same payload written twice
    produces the same bytes, and a crash mid-write leaves the previous file."""
    path = pathlib.Path(path or SNAP)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(snap, ensure_ascii=False, indent=1) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def load_snapshot():
    if not SNAP.exists():
        return {"fetched_at": None, "sources": {}, "events": [], "listings": []}
    try:
        data = json.loads(SNAP.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"fetched_at": None, "sources": {}, "events": [], "listings": []}
    data.setdefault("events", [])
    data.setdefault("listings", [])
    return data


PUBLIC_FIELDS = (
    "id", "source", "title", "start", "end", "venue_name", "venue_slug",
    "borough", "neighborhood", "category", "price_min", "url",
    "image_url", "image_local", "image_w", "image_h",
)


def public_feed(snap, now=None):
    """The week snapshot the browser re-slices. Ended rows are left out.

    Unknown keys are dropped so a stray secret in a row cannot be published.
    """
    now = now or local_now()
    rows = []
    for ev in (snap or {}).get("events") or []:
        if not ev.get("start") or has_ended(ev, now):
            continue
        row = {}
        for key in PUBLIC_FIELDS:
            value = ev.get(key)
            if value not in (None, ""):
                row[key] = value
        rows.append(row)
    return {"fetched_at": (snap or {}).get("fetched_at"), "events": rows}


def write_public_feed(snap, path, now=None):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(public_feed(snap, now), ensure_ascii=False, indent=1) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def load_venues():
    out = []
    for f in sorted((ROOT / "data" / "venues").glob("*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def run(now=None, get_json=None, post_json=None, store_images=True):
    now = now or local_now()
    previous = load_snapshot()
    get_json = get_json or (lambda url: fetch_json(url))

    def _post(url, body, key):
        return fetch_json(
            url, method="POST", body=json.dumps(body),
            headers={
                "exp-api-key": key,
                "Accept": "application/json;version=2.0",
                "Accept-Language": "en-US",
                "Content-Type": "application/json",
            })

    post_json = post_json or _post
    results = {}
    for name, fn in (
        ("nyc_parks", lambda: fetch_parks(get_json, now)),
        ("nyc_permits", lambda: fetch_permits(get_json, now)),
        ("ticketmaster", lambda: fetch_ticketmaster(get_json, now)),
        ("viator", lambda: fetch_viator(post_json, now)),
    ):
        try:
            got = fn()
        except Exception as ex:
            results[name] = {"ok": False, "error": _redact(type(ex).__name__ + ": " + str(ex)[:180])}
            continue
        if got is None:
            results[name] = {"skipped": True, "reason": "no key"}
        else:
            results[name] = {"ok": True, "events": got, "fetched_at": iso(now)}
    events, listings, status = assemble(previous, results, now)
    events = apply_matches(events, load_venues())
    pool = list(events) + list(listings)
    if store_images:
        for ev in pool:
            # Ticketmaster images stay on their CDN, next to that event only.
            if ev.get("source") == "ticketmaster" or not ev.get("_image_remote") or ev.get("image_local"):
                ev.pop("_image_remote", None)
            else:
                store_image(ev)
    else:
        for ev in pool:
            ev.pop("_image_remote", None)
    # A rebuilt file must not carry a key that arrived in an error string.
    raw = json.dumps(status)
    for secret in (_tm_key(), _viator_key()):
        if secret and secret in raw:
            raise RuntimeError("refusing to write a snapshot that contains an API key")
    snap = {"fetched_at": iso(now), "sources": status, "events": events, "listings": listings}
    write_snapshot(snap)
    return snap


def main():
    try:
        snap = run()
    except Exception as ex:
        print("events: fetch failed, leaving the last snapshot in place:", ex)
        return 0
    counts = {}
    for ev in snap["events"]:
        counts[ev["source"]] = counts.get(ev["source"], 0) + 1
    print(f"events: {len(snap['events'])} kept {counts} sources={snap['sources']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
