#!/usr/bin/env python3
import datetime as dt
import html
import os
import re
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parents[1]
BLOG_WEEKLY = ROOT / "blog" / "weekly"
ARCHIVE = ROOT / "blog" / "archive-weekly-briefs.html"
BLOG_INDEX = ROOT / "blog" / "index.html"
SITEMAP = ROOT / "sitemap.xml"


def fmt_date(d: dt.date) -> str:
    return d.strftime("%Y-%m-%d")


def slug(d: dt.date) -> str:
    return f"weekend-brief-{fmt_date(d)}.html"


def date_range_title(d: dt.date) -> str:
    end = d + dt.timedelta(days=3)
    return f"{d.strftime('%B %-d')}–{end.strftime('%-d')}"


def get_weather() -> dict:
    url = "https://wttr.in/New%20York?format=j1"
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    data = r.json()
    current = data.get("current_condition", [{}])[0]
    days = data.get("weather", [])[:7]
    return {
        "current_f": current.get("temp_F", ""),
        "desc": (current.get("weatherDesc", [{}])[0].get("value") or "").lower(),
        "forecast": [
            {
                "date": d.get("date", ""),
                "max_f": d.get("maxtempF", ""),
                "min_f": d.get("mintempF", ""),
                "desc": (d.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value") if d.get("hourly") else "").lower(),
            }
            for d in days
        ],
    }


def fetch_donyc_events(d: dt.date, limit: int = 10):
    url = f"https://donyc.com/events/{d.strftime('%Y/%m/%d')}"
    r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    h = r.text

    # Extract event blocks with title + event URL + venue.
    cards = re.findall(r'(<article[^>]*class="[^"]*ds-listing-event-card[^"]*"[\s\S]*?</article>)', h)
    out = []
    for c in cards:
        m_link = re.search(r'href="([^"]+)"[^>]*class="[^"]*ds-listing-event-title-link[^"]*"', c)
        m_title = re.search(r'class="[^"]*ds-listing-event-title-text[^"]*"[^>]*>(.*?)<', c)
        m_venue = re.search(r'class="[^"]*ds-listing-event-venue-link[^"]*"[^>]*>(.*?)<', c)
        if not (m_link and m_title):
            continue
        title = html.unescape(re.sub(r"\s+", " ", m_title.group(1))).strip()
        venue = html.unescape(re.sub(r"\s+", " ", (m_venue.group(1) if m_venue else "NYC Venue"))).strip()
        link = urljoin("https://donyc.com", m_link.group(1))
        if title and link:
            out.append({"title": title, "venue": venue, "borough": "NYC", "url": link})
        if len(out) >= limit:
            break

    if not out:
        # fallback parser using itemprop pairs
        pairs = re.findall(r'itemprop="name"[^>]*>(.*?)<', h)
        cleaned = [html.unescape(re.sub(r"\s+", " ", p)).strip() for p in pairs if p.strip()]
        for i in range(0, min(len(cleaned)-1, limit*2), 2):
            out.append({"title": cleaned[i], "venue": cleaned[i+1], "borough": "NYC", "url": url})
    return out


def weather_impact_text(w):
    cur = int(w.get("current_f") or 55)
    if cur < 40:
        return "Cold conditions usually concentrate demand into indoor venues and reduce spontaneous long-distance hopping."
    if cur > 78:
        return "Warmer conditions typically increase rooftop and open-air demand early, then drive late-night migration indoors."
    return "Moderate weather supports longer movement windows, but peak-hour lines still reward early commitment and short transfers."


def render_post(d: dt.date, weather: dict, events: list) -> str:
    ds = fmt_date(d)
    title = f"NYC Weekend Nightlife Guide: {date_range_title(d)} ({d.strftime('%b %-d')} Weekend Energy, Live Shows, and Late-Night Strategy)"
    meta = f"NYC weekend nightlife guide for {date_range_title(d)}: weather, live event signals, neighborhood strategy, route planning, and safer late-night execution."

    days = weather.get("forecast", [])
    day_lines = []
    names = ["Friday", "Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    for i, fd in enumerate(days[:7]):
        day_lines.append(f"<li><strong>{names[i]}:</strong> {fd.get('max_f','?')}°/{fd.get('min_f','?')}°F, {fd.get('desc','conditions')}</li>")

    event_items = []
    for e in events[:10]:
        desc = "High-interest live listing with strong weekend traffic signal."
        event_items.append(
            f'<li><strong>{html.escape(e["title"])}</strong> — {html.escape(e["venue"])} ({e["borough"]}): {desc} '
            f'<a href="{e["url"]}" target="_blank" rel="noopener">View listing</a></li>'
        )

    sources_block = """
<a href="https://www.timeout.com/newyork/things-to-do/things-to-do-in-new-york-this-week" target="_blank" rel="noopener">Time Out New York weekly events guide</a><br/>
<a href="https://donyc.com/events" target="_blank" rel="noopener">doNYC events calendar</a><br/>
<a href="https://www.eventbrite.com/d/ny--new-york/events/" target="_blank" rel="noopener">Eventbrite NYC events</a><br/>
<a href="https://www.nycgo.com/things-to-do/events-in-nyc/" target="_blank" rel="noopener">NYCgo events calendar</a><br/>
<a href="https://ra.co/events/us/newyork" target="_blank" rel="noopener">Resident Advisor NYC events</a>
""".strip()

    return f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title} | NYC Nightlife</title>
<meta name="description" content="{meta[:160]}" />
<link rel="canonical" href="https://nynightlife.com/blog/weekly/{slug(d)}" />
<link rel="stylesheet" href="/css/main.css"/>
<meta property="og:title" content="{title} | NYC Nightlife" />
<meta property="og:description" content="{meta[:160]}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://nynightlife.com/blog/weekly/{slug(d)}" />
<meta property="og:image" content="https://nynightlife.com/assets/og-default.jpg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title} | NYC Nightlife" />
<meta name="twitter:description" content="{meta[:160]}" />
<meta name="twitter:image" content="https://nynightlife.com/assets/og-default.jpg" />
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"{title} | NYC Nightlife","url":"https://nynightlife.com/blog/weekly/{slug(d)}","description":"{meta[:160]}","inLanguage":"en-US","isPartOf":{{"@type":"WebSite","name":"NYNightlife","url":"https://nynightlife.com/"}}}}</script>
</head><body><main class="container" style="padding:2rem 1rem; max-width:900px;">

<p class="eyebrow">NYC Weekend Brief</p>
<h1>{title}</h1>
<p><strong>Published:</strong> Friday, {ds} at 2:00 PM (America/New_York)</p>

<h2>NYC Weather Snapshot</h2>
<p><strong>Current:</strong> {weather.get('current_f','?')}°F, {weather.get('desc','conditions')}.</p>
<ul>{''.join(day_lines)}</ul>
<p>{weather_impact_text(weather)}</p>

<h2>Weekend Overview</h2>
<p>NYC nightlife this cycle is shaped by stacked optionality: concerts, club nights, themed rooms, and neighborhood micro-scenes all competing for the same peak hours. That means your edge is not more scrolling — it is cleaner planning and tighter movement logic.</p>
<p>Seasonal behavior matters right now: readers who lock one anchor district and two nearby backups consistently outperform “figure-it-out-later” groups. This weekend rewards route discipline, not maximalism.</p>
<p>City momentum is strongest when cultural programming and nightlife listings overlap. Use this brief as a tactical planning guide: map your first move, protect your middle hours, and avoid long speculative transfers after midnight.</p>

<h2>What Changed This Week</h2>
<p>Compared with last week, the key shift is in <strong>event concentration and timing pressure</strong>: more activity is clustering into narrower peak windows, so late reactive pivots are less efficient. Weather range this week also changes pre-midnight movement behavior, especially for groups planning multi-stop routes.</p>
<p>Practical implication: if you ran a broad exploratory route last week, tighten it this week to one district lane plus one verified backup. This preserves your best hours and reduces queue/transport drag.</p>

<h2>Live Event Signals</h2>
<p>Notable confirmed signals from live NYC listings:</p>
<ul>{''.join(event_items)}</ul>
<p>These listings indicate broad multi-venue demand, not a single-scene weekend. Expect variability at doors and rising value for pre-committed plans.</p>

<h2>Top Neighborhoods for This Weekend</h2>
<p><strong>Lower East Side:</strong> mixed-format bars and dance rooms, high density, ideal for low-transfer routing. Best arrival: 9:00–10:30 PM.</p>
<p><strong>Williamsburg:</strong> live music + warehouse-adjacent energy; stronger for groups prioritizing music-forward nights. Best arrival: 8:30–10:00 PM.</p>
<p><strong>Bushwick:</strong> late-energy environments and scene-driven programming. Best for crews comfortable with less predictable sequencing.</p>
<p><strong>Midtown / Hell’s Kitchen:</strong> easier transit anchors with reliable fallback options for visitors.</p>
<p><strong>Meatpacking / West Chelsea:</strong> premium-night routes, stronger upside with reservations and clearer spend boundaries.</p>

<h2>Night Route Strategies</h2>
<p><strong>Concert → Club Pivot:</strong> Start ticketed, then pivot local within a 10–15 minute transfer radius. This controls uncertainty while keeping upside.</p>
<p><strong>Brooklyn Lane:</strong> Commit to one Brooklyn zone and avoid borough switching. You sacrifice breadth but win on time efficiency.</p>
<p><strong>Manhattan Density Lane:</strong> Use close-proximity venues to maximize optionality with minimal ride friction.</p>
<p><strong>Theme-Night Strategy:</strong> If a holiday/themed cycle is active, lock one thematic anchor and one neutral backup.</p>
<p><strong>Low-Cost Route:</strong> Early entry windows + fewer transfers + one planned close location keeps spend predictable.</p>
<p><strong>VIP Route:</strong> Pre-booked entry + controlled movement + pre-set close-out transport.</p>

<h2>Budget + Risk Strategy</h2>
<p>Break spend into four buckets: entry/cover, drinks, transport, and volatility (unexpected waits or pivots). Most overages come from the volatility bucket.</p>
<p>Use a midnight pivot rule: if upside is unclear and transfer time is long, do not move. Protect 10:30 PM–1:00 AM as prime value hours.</p>
<p>For group plans, pre-agree wait tolerance, spend ceiling, and one reunion protocol. Group drift is the #1 execution failure.</p>

<h2>Plan Your NYC Night</h2>
<p>Run discovery in <a href="https://nynightlife.com/tonight">Tonight</a>, build sequencing in <a href="https://nynightlife.com/night-planner">NY Night Planner</a>, compare options in <a href="https://nynightlife.com/venue-compare">Venue Compare</a>, and finalize lane logic in <a href="https://nynightlife.com/weekend">Weekend Hub</a>.</p>
<p>Before final movement decisions, check <a href="https://nynightlife.com/safe-late-night-transport">Safe Late-Night Transport</a> to avoid weak close-out logistics. For historical pattern context, review the <a href="https://nynightlife.com/blog/archive">weekly archive</a>.</p>

<h2>Execution Checklist</h2>
<ul>
<li>Choose one anchor venue.</li>
<li>Pick two nearby backups.</li>
<li>Define a midnight pivot rule.</li>
<li>Set a transfer stop-loss time.</li>
<li>Lock close-out transport before peak surge.</li>
</ul>

<h2>Image Notes</h2>
<p>Recommended image set: skyline-at-dusk hero, neighborhood crowd scene, and one event-energy image tied to active listings. Caption example: “St. Patrick’s themed crowds gathering in Lower Manhattan bars.”</p>

<h2>Sources</h2>
<p style="font-size:.92rem; line-height:1.7;">{sources_block}</p>

<h2>Editorial Note</h2>
<p>Event details can change rapidly. Confirm final timing, entry rules, and venue specifics directly on official event pages before spending.</p>

<h2>Final Takeaway</h2>
<p>NYC nightlife this weekend rewards early planning, short transfer distances, and disciplined venue sequencing. If you pick one lane, protect your prime hours, and avoid speculative late pivots, your upside is materially higher.</p>

<p><a href="/methodology/">Methodology</a> · <a href="/affiliate-disclosure.html">Affiliate Disclosure</a></p>
<p><a href="/blog/archive-weekly-briefs.html">← Back to archive</a></p>
</main></body></html>
'''


def update_blog_index():
    txt = BLOG_INDEX.read_text(encoding="utf-8")
    files = sorted(BLOG_WEEKLY.glob("weekend-brief-*.html"))
    latest = files[-3:][::-1]
    links = " · ".join([f'<a href="/blog/weekly/{f.name}">{f.name[13:23]}</a>' for f in latest])
    txt = re.sub(r'<p><strong>Latest Friday Briefs:</strong>.*?</p>', f'<p><strong>Latest Friday Briefs:</strong> {links}</p>', txt, flags=re.S)
    txt = re.sub(r'Open \d+-week Friday Brief Archive', f'Open {len(files)}-week Friday Brief Archive', txt)
    BLOG_INDEX.write_text(txt, encoding="utf-8")


def update_archive(d: dt.date):
    txt = ARCHIVE.read_text(encoding="utf-8")
    month_id = d.strftime("m-%Y-%m")
    month_label = d.strftime("%B %Y")
    li = f'<li data-title="weekend brief {d.strftime("%Y %m %d")}"><a href="/blog/weekly/{slug(d)}">Weekend Brief — {fmt_date(d)}</a><span class="meta">Fri 2:00 PM ET</span></li>'

    m = re.search(r'(\d+) briefs', txt)
    if m:
        count = int(m.group(1))
        txt = txt.replace(f"{count} briefs", f"{count+1} briefs", 1)

    nav_link = f'<a href="#{month_id}">{month_label}</a>'
    if nav_link not in txt:
        txt = re.sub(r'(<nav class="month-nav"[^>]*>)', r'\1\n        ' + nav_link, txt, count=1)

    if f'id="{month_id}"' in txt:
        pattern = rf'(<article id="{month_id}" class="month-card">.*?<ul>)'
        txt = re.sub(pattern, r'\1' + li, txt, count=1, flags=re.S)
    else:
        block = f'<article id="{month_id}" class="month-card">\n<h2>{month_label}</h2>\n<ul>{li}</ul>\n</article>\n'
        txt = re.sub(r'(<section class="month-grid" id="archiveGrid">)', r'\1\n      ' + block, txt, count=1)

    ARCHIVE.write_text(txt, encoding="utf-8")


def update_sitemap(d: dt.date):
    txt = SITEMAP.read_text(encoding="utf-8")
    url = f"https://nynightlife.com/blog/weekly/{slug(d)}"
    line = f"  <url><loc>{url}</loc></url>"
    if url in txt:
        return
    txt = txt.replace("</urlset>", line + "\n</urlset>")
    SITEMAP.write_text(txt, encoding="utf-8")


def main():
    d = dt.datetime.now().date()
    out = BLOG_WEEKLY / slug(d)
    if out.exists():
        print(f"Already exists: {out}")
        return 0

    weather = get_weather()
    events = fetch_donyc_events(d)
    out.write_text(render_post(d, weather, events), encoding="utf-8")
    update_archive(d)
    update_blog_index()
    update_sitemap(d)
    print(f"Created and indexed: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
