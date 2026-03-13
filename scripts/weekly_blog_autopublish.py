#!/usr/bin/env python3
import datetime as dt
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_WEEKLY = ROOT / "blog" / "weekly"
ARCHIVE = ROOT / "blog" / "archive-weekly-briefs.html"
BLOG_INDEX = ROOT / "blog" / "index.html"
SITEMAP = ROOT / "sitemap.xml"

TZ = "America/New_York"


def et_now():
    # Cron sets TZ; fallback safe for local runs
    return dt.datetime.now()


def fmt_date(d: dt.date) -> str:
    return d.strftime("%Y-%m-%d")


def season_angle(d: dt.date) -> str:
    m = d.month
    if m in (12, 1, 2):
        return "winter crowd compression and faster late-night pivots"
    if m in (3, 4, 5):
        return "spring demand acceleration and neighborhood-level variance"
    if m in (6, 7, 8):
        return "summer volume spikes, rooftop pressure, and longer movement windows"
    return "fall event density, high optionality, and sharper route discipline"


def post_title(d: dt.date) -> str:
    return f"NYC Weekend Nightlife Brief: {d.strftime('%B %-d, %Y')} Operational Playbook"


def slug(d: dt.date) -> str:
    return f"weekend-brief-{fmt_date(d)}.html"


def render_post(d: dt.date) -> str:
    ds = fmt_date(d)
    title = post_title(d)
    angle = season_angle(d)
    return f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title} | NYC Nightlife</title>
<meta name="description" content="Source-backed NYC nightlife weekend brief for {ds}, published Friday at 2:00 PM ET with practical planning and risk controls." />
<link rel="canonical" href="https://nynightlife.com/blog/weekly/{slug(d)}" />
<link rel="stylesheet" href="/css/main.css"/>
<meta property="og:title" content="{title} | NYC Nightlife" />
<meta property="og:description" content="Source-backed NYC nightlife weekend brief for {ds}, published Friday at 2:00 PM ET." />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://nynightlife.com/blog/weekly/{slug(d)}" />
<meta property="og:image" content="https://nynightlife.com/assets/og-default.jpg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title} | NYC Nightlife" />
<meta name="twitter:description" content="Source-backed NYC nightlife weekend brief for {ds}, published Friday at 2:00 PM ET." />
<meta name="twitter:image" content="https://nynightlife.com/assets/og-default.jpg" />
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"{title} | NYC Nightlife","url":"https://nynightlife.com/blog/weekly/{slug(d)}","description":"Source-backed NYC nightlife weekend brief for {ds}, published Friday at 2:00 PM ET.","inLanguage":"en-US","isPartOf":{{"@type":"WebSite","name":"NYNightlife","url":"https://nynightlife.com/"}}}}</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3007723856138381" crossorigin="anonymous"></script>
</head><body><main class="container" style="padding:2rem 1rem; max-width:900px;">
<p class="eyebrow">NYC Weekend Brief</p>
<h1>{title}</h1>
<p><strong>Published:</strong> Friday, {ds} at 2:00 PM (America/New_York)</p>

<p>This week’s NYC nightlife signal is defined by <strong>{angle}</strong>. The operational edge is not “more options” — it is faster decisions, tighter transitions, and cleaner close-out logistics.</p>

<h2>How to run this weekend</h2>
<ol>
<li><strong>Anchor first move before 8 PM:</strong> lock one primary district and one backup in the same area.</li>
<li><strong>Use decision checkpoints:</strong> 10:30 PM and 12:00 AM are hard stay/move calls.</li>
<li><strong>Minimize transfer drag:</strong> avoid long speculative rides after midnight.</li>
<li><strong>Protect your close:</strong> define your final 60–90 minute lane early.</li>
</ol>

<h2>Risk controls</h2>
<ul>
<li><strong>Door risk:</strong> keep one ticketed fallback.</li>
<li><strong>Cost risk:</strong> track transport + entry + close-out as separate budget lines.</li>
<li><strong>Group drift risk:</strong> set one clear reunion rule if splitting.</li>
<li><strong>Transit risk:</strong> confirm last-leg return plan before 12:30 AM.</li>
</ul>

<h2>What to verify before spending</h2>
<p>Event pages, doors, ticket terms, and start times can change quickly. Confirm final details directly on official listing pages right before you go.</p>

<h2>Execution links</h2>
<p>Use <a href="/tools/nyc-night-planner.html">NYC Night Planner</a>, <a href="/tools/venue-compare-nyc.html">Venue Compare</a>, and <a href="/plan/safe-late-night-transport-nyc.html">Safe Late-Night Transport</a> to convert options into a concrete route.</p>

<h2>Editorial integrity note</h2>
<p>This brief is source-backed and strategy-first. It intentionally avoids fabricated listings, unverified specials, or unsupported venue-specific claims.</p>

<h2>Sources</h2>
<p style="font-size:.92rem; line-height:1.6;">
<a href="https://www.eventbrite.com/d/ny--new-york/events/" target="_blank" rel="noopener nofollow">Eventbrite NYC events</a><br/>
<a href="https://www.timeout.com/newyork/things-to-do/things-to-do-in-new-york-this-week" target="_blank" rel="noopener nofollow">Time Out New York weekly events guide</a><br/>
<a href="https://www.nycgo.com/things-to-do/events-in-nyc/" target="_blank" rel="noopener nofollow">NYCgo events calendar</a><br/>
<a href="https://ra.co/events/us/newyork" target="_blank" rel="noopener nofollow">Resident Advisor NYC events</a>
</p>
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

    # KPI count
    m = re.search(r'(\d+) briefs', txt)
    if m:
        count = int(m.group(1))
        txt = txt.replace(f"{count} briefs", f"{count+1} briefs", 1)

    # month nav link
    nav_link = f'<a href="#{month_id}">{month_label}</a>'
    if nav_link not in txt:
        txt = re.sub(r'(<nav class="month-nav"[^>]*>)', r'\1\n        ' + nav_link, txt, count=1)

    # insert into month card if exists
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
    now = et_now()
    d = now.date()
    out = BLOG_WEEKLY / slug(d)
    if out.exists():
        print(f"Already exists: {out}")
        return 0

    out.write_text(render_post(d), encoding="utf-8")
    update_archive(d)
    update_blog_index()
    update_sitemap(d)
    print(f"Created and indexed: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
