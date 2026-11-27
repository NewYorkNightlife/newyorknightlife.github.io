"""Homepage night map: five borough outlines and venue pins.

Borough paths are a simplified copy of the NYC Open Data borough boundaries
(Department of City Planning). A venue is plotted only when venue_geo.json has
an NYC Planning Labs GeoSearch point that still matches the house number,
street, borough, and ZIP on the venue record. Nothing is interpolated.

Geocode again with: python _build/geocode_venues.py
"""
from __future__ import annotations

import gzip
import html
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
BOROUGHS = ROOT / "data" / "boroughs.geojson"
GEO = ROOT / "data" / "venue_geo.json"
IMG = ROOT / "img"

# Label anchors sit on empty land, away from the rooms. They are captions,
# not venue coordinates.
LABELS = {
    "Manhattan": (40.815, -73.955),
    "Brooklyn": (40.635, -73.960),
    "Queens": (40.735, -73.800),
    "Bronx": (40.855, -73.870),
    "Staten Island": (40.580, -74.150),
}
# Real borough sections on /venues/. The old /boroughs/ pages only redirect.
GUIDES = {
    "Manhattan": "/venues/#manhattan",
    "Brooklyn": "/venues/#brooklyn",
    "Queens": "/venues/#queens",
}
ORDER = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]

LAT0 = 40.7128
PAD_LNG = 0.04
PAD_LAT = 0.05
VIEW_W = 800

STREET = re.compile(
    r"\b(\d{1,5}(?:-\d{1,5})?)\s+"
    r"((?:(?:North|South|East|West|N|S|E|W)\.?\s+)?"
    r"(?:[\w.'’\-]+\s+){0,4}"
    r"(?:Street|St|Avenue|Ave|Boulevard|Blvd|Place|Pl|Road|Rd|Drive|Dr|"
    r"Lane|Ln|Court|Ct|Way|Terrace|Ter|Broadway|Plaza|Parkway|Pkwy)\.?)\b",
    re.I,
)
ZIP = re.compile(r"\b(1\d{4})\b")
SUFFIX = {"ST", "AVE", "BLVD", "PL", "RD", "DR", "LN", "CT", "TER", "PKWY", "BROADWAY"}
DIR = {"N", "S", "E", "W"}

e = html.escape


def norm_street(value: str) -> str:
    text = (value or "").upper().replace(".", " ").replace("'", "")
    text = text.replace("BWAY", "BROADWAY")
    for src, dst in (
        (" STREET", " ST"), (" AVENUE", " AVE"), (" BOULEVARD", " BLVD"),
        (" PLACE", " PL"), (" ROAD", " RD"), (" DRIVE", " DR"),
        (" LANE", " LN"), (" COURT", " CT"), (" TERRACE", " TER"),
        (" PARKWAY", " PKWY"),
    ):
        text = text.replace(src, dst)
    text = re.sub(r"\b(NORTH|SOUTH|EAST|WEST)\b", lambda m: m.group(1)[0], text)
    text = re.sub(r"\b(\d+)(?:ST|ND|RD|TH)\b", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def streets_match(want: str, got: str) -> bool:
    want_tokens = norm_street(want).split()
    got_tokens = set(norm_street(got).split())
    name = [token for token in want_tokens if token not in SUFFIX and token not in DIR]
    if not name:
        return norm_street(want) == norm_street(got)
    return all(token in got_tokens for token in name)


def address_still_matches(venue: dict, rec: dict) -> bool:
    """True when the stored address point is still the venue's own address."""
    address = venue.get("address") or ""
    core = re.sub(r"\([^)]*\)", " ", address)
    found = STREET.search(core)
    zcode = ZIP.search(address)
    if not found or not zcode:
        return False
    number = found.group(1)
    street = re.sub(r"\s+", " ", found.group(2)).strip(" ,.")
    if number.upper().replace(" ", "") != str(rec.get("housenumber") or "").upper().replace(" ", ""):
        return False
    if zcode.group(1) != str(rec.get("postalcode") or ""):
        return False
    if (venue.get("borough") or "").lower() != (rec.get("borough") or "").lower():
        return False
    if (rec.get("source") or "") != "nycpad":
        return False
    return streets_match(street, rec.get("street") or "")


def _load_geo() -> dict:
    if not GEO.is_file():
        return {}
    data = json.loads(GEO.read_text(encoding="utf-8"))
    return data.get("venues") or {}


def has_photo(venue: dict) -> bool:
    photo = venue.get("photo") or {}
    return bool(photo.get("url")) and (IMG / f"{venue['slug']}.jpg").is_file()


def point_for(venue: dict, geo: dict | None = None) -> dict | None:
    geo = _load_geo() if geo is None else geo
    rec = geo.get(venue.get("slug") or "")
    if not rec or not has_photo(venue):
        return None
    if not address_still_matches(venue, rec):
        return None
    try:
        lat = round(float(rec["lat"]), 6)
        lng = round(float(rec["lng"]), 6)
    except (KeyError, TypeError, ValueError):
        return None
    if not (40.49 <= lat <= 40.93 and -74.26 <= lng <= -73.70):
        return None
    return {"lat": lat, "lng": lng}


def split(venues: list) -> tuple[list, list]:
    """Return (plotted venue dicts, skipped {slug, reason})."""
    geo = _load_geo()
    plotted = []
    skipped = []
    for venue in venues:
        slug = venue.get("slug") or ""
        if slug not in geo:
            skipped.append({"slug": slug, "reason": "no address point in venue_geo.json"})
            continue
        if not has_photo(venue):
            skipped.append({"slug": slug, "reason": "no licensed photo"})
            continue
        if not address_still_matches(venue, geo[slug]):
            skipped.append({"slug": slug, "reason": "address point does not match the venue address"})
            continue
        point = point_for(venue, geo)
        if not point:
            skipped.append({"slug": slug, "reason": "address point is not usable"})
            continue
        row = dict(venue)
        row["_lat"] = point["lat"]
        row["_lng"] = point["lng"]
        plotted.append(row)
    plotted.sort(key=lambda v: ((ORDER.index(v["borough"]) if v.get("borough") in ORDER else 9), v["name"].lower()))
    return plotted, skipped


def _features():
    data = json.loads(BOROUGHS.read_text(encoding="utf-8"))
    return data["features"]


def _bounds(features) -> dict:
    lngs = []
    lats = []
    for feature in features:
        for ring in feature["geometry"]["coordinates"]:
            for lng, lat in ring:
                lngs.append(lng)
                lats.append(lat)
    span_lng = max(lngs) - min(lngs)
    span_lat = max(lats) - min(lats)
    minlng = min(lngs) - span_lng * PAD_LNG
    maxlng = max(lngs) + span_lng * PAD_LNG
    minlat = min(lats) - span_lat * PAD_LAT
    maxlat = max(lats) + span_lat * PAD_LAT
    span_x = (maxlng - minlng) * math.cos(math.radians(LAT0))
    span_y = maxlat - minlat
    height = int(round(VIEW_W * span_y / span_x))
    return {
        "minlng": minlng, "maxlng": maxlng, "minlat": minlat, "maxlat": maxlat,
        "w": VIEW_W, "h": height, "lat0": LAT0,
    }


def _xy(lng: float, lat: float, box: dict) -> tuple[float, float]:
    span_x = (box["maxlng"] - box["minlng"]) * math.cos(math.radians(box["lat0"]))
    span_y = box["maxlat"] - box["minlat"]
    x = (lng - box["minlng"]) * math.cos(math.radians(box["lat0"])) / span_x * box["w"]
    y = (box["maxlat"] - lat) / span_y * box["h"]
    return round(x, 1), round(y, 1)


def _path(feature, box) -> str:
    parts = []
    for ring in feature["geometry"]["coordinates"]:
        points = [_xy(lng, lat, box) for lng, lat in ring]
        clean = [points[0]]
        for point in points[1:]:
            if point != clean[-1]:
                clean.append(point)
        if len(clean) < 4:
            continue
        if clean[0] != clean[-1]:
            clean.append(clean[0])
        draw = f"M{clean[0][0]:.1f} {clean[0][1]:.1f}"
        draw += "".join(f"L{x:.1f} {y:.1f}" for x, y in clean[1:])
        draw += "Z"
        parts.append(draw)
    return "".join(parts)


def projection(features=None) -> dict:
    features = _features() if features is None else features
    return _bounds(features)


def svg_markup(features=None, box=None) -> str:
    features = _features() if features is None else features
    box = _bounds(features) if box is None else box
    paths = []
    for feature in features:
        name = feature["properties"]["name"]
        slug = name.lower().replace(" ", "-")
        draw = _path(feature, box)
        paths.append(
            f'<path id="boro-{slug}" data-boro="{slug}" d="{draw}"/>'
        )
    body = "".join(paths)
    w, h = box["w"], box["h"]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'class="night-map-svg" role="img" aria-labelledby="night-map-svg-title">'
        f'<title id="night-map-svg-title">New York City, five boroughs</title>'
        f'<g class="night-map-land" fill="#141b2b" stroke="#8eb6ff" stroke-width="1.35" '
        f'stroke-linejoin="round">{body}</g>'
        f'<path id="night-route-glow" class="night-route-glow" fill="none" stroke="#ffb86b" '
        f'stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0.28"/>'
        f'<path id="night-route" class="night-route" fill="none" stroke="#ffb86b" '
        f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="7 9"/>'
        f"</svg>"
    )


def write_svg(out_dir: pathlib.Path) -> pathlib.Path:
    features = _features()
    box = _bounds(features)
    svg = svg_markup(features, box)
    path = pathlib.Path(out_dir) / "img" / "night-map.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8", newline="\n")
    return path


def path_gzip_size(svg: str | None = None) -> int:
    svg = svg if svg is not None else svg_markup()
    draws = "".join(re.findall(r'\sd="([^"]+)"', svg))
    return len(gzip.compress(draws.encode("utf-8")))


def _pin_payload(venues: list) -> str:
    rows = []
    for venue in venues:
        rows.append({
            "slug": venue["slug"],
            "name": venue["name"],
            "hood": venue.get("neighborhood") or "",
            "borough": venue.get("borough") or "",
            "lat": venue["_lat"],
            "lng": venue["_lng"],
            "photo": f"/img/{venue['slug']}-thumb.webp",
            "url": f"/venues/{venue['slug']}.html",
        })
    blob = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return blob.replace("<", "\\u003c")


def _labels(box) -> str:
    bits = []
    for name in ORDER:
        lat, lng = LABELS[name]
        x, y = _xy(lng, lat, box)
        slug = name.lower().replace(" ", "-")
        bits.append(
            f'<button type="button" class="night-map-label" data-boro="{slug}" '
            f'data-vx="{x:.2f}" data-vy="{y:.2f}" '
            f'style="left:{x / box["w"] * 100:.2f}%;top:{y / box["h"] * 100:.2f}%" '
            f'aria-pressed="false">{e(name)}</button>'
        )
    return "".join(bits)


def _chips() -> str:
    bits = ['<button type="button" data-boro="all" aria-pressed="true">All five</button>']
    for name in ORDER:
        slug = name.lower().replace(" ", "-")
        bits.append(
            f'<button type="button" data-boro="{slug}" aria-pressed="false">{e(name)}</button>'
        )
    return "".join(bits)


def _list(venues: list, u) -> str:
    groups: dict[str, list] = {}
    for venue in venues:
        groups.setdefault(venue.get("borough") or "Other", []).append(venue)
    html_groups = ""
    for name in ORDER:
        rows = groups.get(name) or []
        if not rows:
            continue
        slug = name.lower().replace(" ", "-")
        guide = GUIDES.get(name)
        heading = f'<a href="{e(u(guide))}">{e(name)}</a>' if guide else e(name)
        items = "".join(
            f'<li><a href="{e(u("/venues/" + v["slug"] + ".html"))}">{e(v["name"])}'
            f'<span>{e(v.get("neighborhood") or name)}</span></a></li>'
            for v in rows
        )
        html_groups += f'<section><h3 id="night-map-{slug}">{heading}</h3><ul>{items}</ul></section>'
    count = len(venues)
    noun = "room" if count == 1 else "rooms"
    return (
        f'<details class="night-map-list"><summary>{count} {noun} on this map</summary>'
        f'<div class="night-map-groups">{html_groups}</div></details>'
    )


def _guide_links(u) -> str:
    links = []
    for name, href in GUIDES.items():
        links.append(f'<a href="{e(u(href))}">{e(name)} list</a>')
    return f'<nav class="night-map-guides" aria-label="Borough venue lists">{"".join(links)}</nav>'


def markup(venues: list, u, js_src: str) -> str:
    plotted, skipped = split(venues)
    print(f"night map: {len(plotted)} plotted, {len(skipped)} skipped"
          + ("" if not skipped else " (" + ", ".join(s["slug"] + ": " + s["reason"] for s in skipped) + ")"))
    features = _features()
    box = _bounds(features)
    payload = _pin_payload(plotted)
    w, h = box["w"], box["h"]
    proj = (
        f'{w},{h},{box["minlng"]:.6f},{box["minlat"]:.6f},'
        f'{box["maxlng"]:.6f},{box["maxlat"]:.6f},{box["lat0"]}'
    )
    guides = _guide_links(u)
    zoom = (
        '<div class="nmap-zoom" role="group" aria-label="Zoom the map">'
        '<button type="button" data-zoom="in" aria-label="Zoom in">+</button>'
        '<button type="button" data-zoom="out" aria-label="Zoom out" disabled>−</button>'
        '<button type="button" data-zoom="reset" aria-label="Recenter map">'
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">'
        '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'd="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg></button></div>'
        '<p class="nmap-hint" data-hint hidden aria-hidden="true">Use two fingers to move the map</p>'
    )
    return f"""<section class="night-map" id="night-map" data-night-map data-proj="{proj}" data-svg="{e(u('/img/night-map.svg'))}" aria-labelledby="night-map-title">
<p class="eyebrow"><span class="line-mark" aria-hidden="true">N</span>Five boroughs</p>
<h2 id="night-map-title">Night map</h2>
<p class="night-map-lede">Rooms whose address matches a city address point.</p>
<div class="night-map-layout">
<div class="night-map-stage" style="aspect-ratio:{w}/{h}" tabindex="0" aria-label="Night map. Drag or use two fingers to move. Pinch, or Ctrl or Command and scroll, to zoom. Arrow keys move. Plus and minus zoom.">
<div class="night-map-canvas" data-canvas></div>
<div class="night-map-labels">{_labels(box)}</div>
<div class="night-map-pins" data-pins></div>
{zoom}
<div class="night-map-card" data-card role="region" hidden></div>
<p class="night-map-empty" data-empty hidden>No checked room in this borough.</p>
</div>
<div class="night-map-panel">
<div class="boro-switch" role="group" aria-label="Filter the map by borough">{_chips()}</div>
{guides}
{_list(plotted, u)}
</div>
</div>
<p class="credit">Borough outlines: <a href="https://data.cityofnewyork.us/" rel="noopener">NYC Open Data</a>, Department of City Planning. Address points: <a href="https://geosearch.planninglabs.nyc/" rel="noopener">NYC Planning Labs GeoSearch</a> (PAD).</p>
<script type="application/json" id="night-map-pins">{payload}</script>
</section>
<script>
(function () {{
  var root = document.getElementById('night-map');
  if (!root || root.getAttribute('data-booted')) return;
  function load() {{
    if (root.getAttribute('data-booted')) return;
    root.setAttribute('data-booted', '1');
    var s = document.createElement('script');
    s.src = '{js_src}';
    s.defer = true;
    document.body.appendChild(s);
  }}
  if (!('IntersectionObserver' in window)) {{ load(); return; }}
  var io = new IntersectionObserver(function (entries) {{
    for (var i = 0; i < entries.length; i++) {{
      if (!entries[i].isIntersecting) continue;
      load();
      io.disconnect();
      return;
    }}
  }}, {{ rootMargin: '240px 0px' }});
  io.observe(root);
}})();
</script>"""
