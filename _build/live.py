"""Fetch the "alive" data: tonight's weather, nightlife headlines, new liquor licenses.

Run by .github/workflows/live.yml a few times a day (also fine to run by hand):
    python _build/live.py
Writes only data/live/*.json. The workflow publishes them to the repo's `live-data` branch (main only
takes pull requests); pages read them in the browser (js/live.js), so this job never rewrites HTML.

Rules (see the 2026-10 plan review):
- Every source can fail. A failed source keeps its last good file untouched; nothing is blanked.
- Untrusted input: responses are size-capped, XML with DOCTYPE/ENTITY is refused, titles are
  stripped of markup, links must be https on that feed's own domain. Pages also escape on render.
- Headlines: title + source + date + link only, and only from feeds whose terms we checked (FEEDS).
- Licenses: public NYS Liquor Authority data. A license is not an opening. Individuals' names are
  never shown; only business-entity names.
- Python stdlib only.
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
except Exception:  # Windows without tzdata: fixed EDT/EST guess is fine for local testing
    NY = dt.timezone(dt.timedelta(hours=-4))

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT.parent
OUT = SITE / "data" / "live"
UA = "nynightlife.com live-data job (+https://nynightlife.com/contact.html)"
MAX_BYTES = 2_000_000
TIMEOUT = 20

# terms: "ok" = terms checked, headline+link use not restricted; anything else is not fetched.
FEEDS = [
    {"name": "EV Grieve", "url": "https://feeds.feedburner.com/EvGrieve", "hosts": ["evgrieve.com"],
     "nyc_only": True, "terms": "ok"},
    # Vox Media terms could not be read on 2026-10-23; switch to "ok" only after reading them.
    {"name": "Eater NY", "url": "https://ny.eater.com/rss/index.xml", "hosts": ["ny.eater.com", "eater.com"],
     "nyc_only": True, "terms": "unverified"},
    {"name": "Grub Street", "url": "https://feeds.feedburner.com/nymag/grubstreet", "hosts": ["grubstreet.com", "nymag.com"],
     "nyc_only": False, "terms": "unverified"},
    # Terms restrict reuse (checked 2026-10-23): BKMag, amNY, Brooklyn Paper. Google News: personal use only.
]

SLA_ACTIVE = "https://data.ny.gov/resource/9s3h-dpkz.json"
COUNTIES = {"New York": "Manhattan", "Kings": "Brooklyn", "Queens": "Queens"}
ON_PREMISES = {"0340": "Full liquor (restaurant/bar)", "0240": "Wine and beer (restaurant/bar)", "0349": "Club",
               "0417": "Cabaret", "0425": "Club", "0415": "Bottle club", "0416": "Restaurant brewer"}
# Only unmistakable company suffixes count as a business; anything else is treated as a person.
ENTITY = re.compile(r"\b(LLC|L\.L\.C|INC|INCORPORATED|CORP|CORPORATION|LTD|LLP|PLLC|COMPANY)\b\.?", re.I)

# The only hosts this job may ever contact (redirects included).
FETCH_HOSTS = {"api.weather.gov", "data.ny.gov", "feeds.feedburner.com"} | {
    urllib.parse.urlsplit(f["url"]).hostname for f in FEEDS}


# ---------------------------------------------------------------- safe fetching

class _AllowlistRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects only to https on a host in FETCH_HOSTS."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = urllib.parse.urlsplit(newurl)
        if new.scheme != "https" or (new.hostname or "").lower() not in FETCH_HOSTS:
            raise urllib.error.HTTPError(newurl, code, "redirect to another site refused", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# https only: no file:, ftp: or plain-http handlers at all
_OPENER = urllib.request.OpenerDirector()
for _h in (urllib.request.HTTPSHandler(), _AllowlistRedirect(), urllib.request.HTTPDefaultErrorHandler(),
           urllib.request.HTTPErrorProcessor()):
    _OPENER.add_handler(_h)


def fetch(url, accept="*/*"):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or (p.hostname or "").lower() not in FETCH_HOSTS or p.username or p.port:
        raise ValueError("fetch refused: " + str(p.hostname))
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with _OPENER.open(req, timeout=TIMEOUT) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("response too large")
    return data


def fetch_json(url, accept="application/json"):
    return json.loads(fetch(url, accept).decode("utf-8"))


def clean_text(s, limit=200):
    s = html.unescape(html.unescape(s or ""))      # double-encoded titles too
    s = re.sub(r"<[^>]*>", " ", s)
    s = s.replace("<", " ").replace(">", " ")     # no stray markup survives, whatever renders it
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit].rstrip() + ("…" if len(s) > limit else "")


def safe_link(url, hosts):
    try:
        p = urllib.parse.urlsplit((url or "").strip())
    except ValueError:
        return None
    h = (p.hostname or "").lower()
    # http links from allowlisted hosts are upgraded; anything else (javascript:, data:, other sites,
    # user@host tricks, ports, backslashes) is dropped
    if (p.scheme not in ("https", "http") or "\\" in (url or "") or p.username or p.password or p.port
            or not any(h == x or h.endswith("." + x) for x in hosts)):
        return None
    return urllib.parse.urlunsplit(("https", h, p.path, p.query, ""))


def _refuse(*_):
    raise ValueError("DOCTYPE/ENTITY in feed refused")


def parse_xml(data):
    if b"<!doctype" in data[:4096].lower() or b"<!entity" in data.lower():
        raise ValueError("DOCTYPE/ENTITY in feed refused")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("feed is not UTF-8")
    # first pass with expat itself: DOCTYPE/ENTITY refused by the parser, whatever the encoding
    import xml.parsers.expat
    chk = xml.parsers.expat.ParserCreate()
    chk.StartDoctypeDeclHandler = _refuse
    chk.EntityDeclHandler = _refuse
    chk.Parse(data, True)
    return ET.fromstring(data)


# ---------------------------------------------------------------- weather (NWS, public domain)

def weather(now):
    pts = fetch_json("https://api.weather.gov/points/40.7484,-73.9857", "application/geo+json")
    fc = fetch_json(pts["properties"]["forecast"], "application/geo+json")
    props = fc["properties"]
    for p in props["periods"]:
        end = dt.datetime.fromisoformat(p["endTime"])
        if not p.get("isDaytime") and end > now:
            break
    else:
        raise ValueError("no night period")
    t = p.get("temperature")
    if not isinstance(t, (int, float)) or not -40 <= t <= 130:
        raise ValueError("temperature out of range")
    pop = (p.get("probabilityOfPrecipitation") or {}).get("value")
    return {
        "period": clean_text(p.get("name"), 40),
        "start": p["startTime"], "end": p["endTime"],
        "temp_f": t,
        "rain_pct": pop if isinstance(pop, (int, float)) and 0 <= pop <= 100 else None,
        "wind": clean_text(f'{p.get("windSpeed", "")} {p.get("windDirection", "")}', 40),
        "short": clean_text(p.get("shortForecast"), 80),
        "issued": props.get("updateTime") or props.get("generatedAt"),
        "source": "National Weather Service (weather.gov)",
    }


# ---------------------------------------------------------------- headlines

STRONG = ["bar", "bars", "nightlife", "nightclub", "speakeasy", "cocktail bar", "wine bar", "dive bar", "rooftop bar",
          "lounge", "karaoke", "last call", "liquor license", "sla", "dance party", "dj set", "rave", "club night",
          "drag show", "happy hour", "taproom", "brewery", "music venue", "comedy club", "after-hours", "after hours",
          "bottle service", "disco", "clubbing", "dance floor", "late-night bar", "jazz club"]
MEDIUM = ["cocktails", "drinks", "late-night", "late night", "party", "opening", "closing", "shutters", "concert",
          "live music", "local music", "halloween", "nye", "new year's eve", "pop-up", "lineup", "dj", "drag", "shoegaze", "dance"]
NYC = ["nyc", "new york city", "manhattan", "brooklyn", "queens", "bronx", "staten island", "bushwick", "williamsburg",
       "east village", "lower east side", "les", "soho", "west village", "chelsea", "harlem", "greenpoint", "ridgewood",
       "astoria", "midtown", "tribeca", "dumbo", "gowanus", "meatpacking", "hell's kitchen", "fidi", "nolita"]
AWAY = ["hudson, ny", "hudson valley", "long island", "hamptons", "new jersey", " nj ", "jersey city", "hoboken",
        "los angeles", "santa monica", "california", "miami", "chicago", "london", "philadelphia"]
NEWSY = ["shooting", "shot", "stabbing", "charged", "arrested", "fraud", "lawsuit", "council", "nypd", "mta",
         "election", "bar association", "attorney", "indicted", "killed", "dies", "died"]
FOOD = ["restaurant", "pizzeria", "pizza", "bakery", "chef", "sushi", "bagel", "burger", "taco", "ramen", "deli"]


def _has(text, word):
    return re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text) is not None


def score(title, cats, nyc_only, venue_names):
    t = " " + (title + " " + " ".join(cats)).lower() + " "
    strong = sum(1 for w in STRONG if _has(t, w))
    s = 3 * strong + min(2, sum(1 for w in MEDIUM if _has(t, w)))
    venues = [n for n in venue_names if _has(t, n.lower())]
    s += 4 if venues else 0
    nyc = any(_has(t, w) for w in NYC)
    if not nyc_only and not nyc:
        s -= 3
    if any(w in t for w in AWAY) and not nyc:
        s -= 4
    if any(_has(t, w) for w in NEWSY):
        s -= 3
    if not strong and any(_has(t, w) for w in FOOD):
        s -= 2
    return s, venues


def _date(s):
    for f in (lambda x: dt.datetime.fromisoformat(x.replace("Z", "+00:00")),
              lambda x: __import__("email.utils").utils.parsedate_to_datetime(x)):
        try:
            d = f(s.strip())
            return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
        except Exception:
            pass
    return None


def feed_items(feed, root):
    atom = "{http://www.w3.org/2005/Atom}"
    out = []
    items = root.findall(".//item") or root.findall(f".//{atom}entry")
    for it in items[:60]:
        def g(tag):
            el = it.find(tag)
            if el is None:
                el = it.find(atom + tag)
            return (el.text or "") if el is not None else ""
        link = g("link")
        if not link:
            for l in it.findall(atom + "link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
        cats = [clean_text(c.text or c.get("term", ""), 40) for c in it.findall("category") + it.findall(atom + "category")]
        out.append({"title": clean_text(g("title"), 160), "url": safe_link(link, feed["hosts"]),
                    "date": _date(g("pubDate") or g("published") or g("updated") or ""), "cats": cats})
    return out


def headlines(now, venue_names):
    kept, sources = [], []
    for f in FEEDS:
        if f["terms"] != "ok":
            continue
        try:
            items = feed_items(f, parse_xml(fetch(f["url"], "application/rss+xml, application/atom+xml, text/xml")))
            sources.append({"name": f["name"], "ok": True})
        except Exception as ex:  # one dead feed must not sink the rest
            sources.append({"name": f["name"], "ok": False, "error": type(ex).__name__})
            continue
        for i in items:
            if not i["title"] or not i["url"] or not i["date"]:
                continue
            age = (now - i["date"]).days
            if age < -1 or age > 45:
                continue
            s, venues = score(i["title"], i["cats"], f["nyc_only"], venue_names)
            if s >= 4:
                kept.append({"title": i["title"], "url": i["url"], "source": f["name"],
                             "date": i["date"].astimezone(NY).date().isoformat(), "score": s, "venues": venues})
    seen, out = set(), []
    for k in sorted(kept, key=lambda k: k["date"], reverse=True):
        key = re.sub(r"\W+", "", k["title"].lower())[:60]
        if key not in seen:
            seen.add(key)
            out.append(k)
    if not any(s["ok"] for s in sources):
        raise RuntimeError("every feed failed")
    return {"items": out[:30], "sources": sources}


# ---------------------------------------------------------------- new liquor licenses (NYS SLA open data)

def licenses(now):
    yy = now.strftime("%y")
    years = [yy] + ([f"{int(yy) - 1:02d}"] if now.month == 1 else [])
    since = (now - dt.timedelta(days=35)).date().isoformat()
    where = (f"premisescounty in({','.join(repr(c) for c in COUNTIES)}) AND class in({','.join(repr(c) for c in ON_PREMISES)}) "
             f"AND originalissuedate >= '{since}' AND (" + " OR ".join(f"licensepermitid like '%-{y}-%'" for y in years) + ")")
    q = urllib.parse.urlencode({
        "$select": "licensepermitid,class,legalname,actualaddressofpremises,zipcode,premisescounty,originalissuedate",
        "$where": where, "$order": "originalissuedate DESC", "$limit": "1000"})
    rows = fetch_json(SLA_ACTIVE + "?" + q)
    if not isinstance(rows, list) or len(rows) > 600:
        raise ValueError("unexpected license data")
    out = []
    for r in rows:
        pid = str(r.get("licensepermitid", ""))
        if re.search(r"-\d\d$", pid.split("-", 2)[-1]) and pid.count("-") >= 3:   # "-01" add-on bars duplicate a parent
            continue
        name = clean_text(r.get("legalname"), 80)
        biz = bool(ENTITY.search(name))   # a person's license shows no name, id or street address
        out.append({
            "id": clean_text(pid, 30) if biz else "",
            "type": ON_PREMISES.get(r.get("class"), "On-premises"),
            "name": name if biz else "Individual licensee",
            "address": clean_text(r.get("actualaddressofpremises"), 80) if biz else "",
            "zip": clean_text(r.get("zipcode"), 5),
            "borough": COUNTIES.get(r.get("premisescounty"), ""),
            "issued": str(r.get("originalissuedate") or "")[:10],
        })
    return {"items": out, "source": "NYS Liquor Authority via data.ny.gov (Active Licenses, 9s3h-dpkz)",
            "source_url": "https://data.ny.gov/Economic-Development/Current-Liquor-Authority-Active-Licenses/9s3h-dpkz"}


# ---------------------------------------------------------------- run

def write_if_changed(name, payload):
    p = OUT / name
    body = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    old = p.read_text(encoding="utf-8") if p.exists() else None
    if old is not None:
        # "fetched" alone changing is not a change worth a commit
        a, b = json.loads(old), json.loads(body)
        a.pop("fetched", None), b.pop("fetched", None)
        if a == b:
            return False
    OUT.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8", newline="\n")
    return True


def venue_names():
    names = []
    for f in sorted((ROOT / "data" / "venues").glob("*.json")):
        v = json.loads(f.read_text(encoding="utf-8"))
        names.append(re.sub(r"\s*\(.*?\)", "", v["name"]))
    return names


def main():
    now = dt.datetime.now(dt.timezone.utc)
    stamp = now.isoformat(timespec="seconds")
    jobs = [("weather.json", lambda: weather(now)), ("news.json", lambda: headlines(now, venue_names())),
            ("licenses.json", lambda: licenses(now))]
    failures = []
    status_p = OUT / "status.json"
    status = json.loads(status_p.read_text(encoding="utf-8")) if status_p.exists() else {}
    for name, job in jobs:
        try:
            data = job()
            data["fetched"] = stamp
            print(name, "changed" if write_if_changed(name, data) else "unchanged")
            status[name] = 0
        except Exception as ex:
            failures.append(f"{name}: {type(ex).__name__}: {str(ex)[:120]}")
            print(name, "FAILED, kept last good copy:", type(ex).__name__, str(ex)[:120])
            status[name] = status.get(name, 0) + 1
    # A source failing once is normal; failing 4 runs in a row (about a day) needs a human. That is
    # recorded in status.json and reported by the workflow AFTER the good data is committed, so one
    # dead source never stops the others from updating.
    status["stuck"] = sorted(n for n, c in status.items() if isinstance(c, int) and c >= 4)
    status["checked"] = stamp
    (OUT / "status.json").write_text(json.dumps(status, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if len(failures) == len(jobs):
        sys.exit("all live sources failed:\n" + "\n".join(failures))


if __name__ == "__main__":
    main()
