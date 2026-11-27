"""Pages added in the Oct 2026 "alive" pass: Tonight, two guides, the changes log + RSS,
weekly hours tables, and the newsletter block.

Static and built from checked data, except the Tonight sections that js/live.js fills from
data/live/*.json (written by the scheduled job, _build/live.py).
"""
import html
import json
import pathlib

import affiliates
from email.utils import format_datetime
import datetime as dt

e = html.escape
ROOT = pathlib.Path(__file__).resolve().parent
SITE = "https://nynightlife.com"
DAYS = [("mon", "Mon"), ("tue", "Tue"), ("wed", "Wed"), ("thu", "Thu"), ("fri", "Fri"), ("sat", "Sat"), ("sun", "Sun")]
HOURS_CHIP = {"likely": '<span class="chip">1 source</span>', "unconfirmed": '<span class="chip">unconfirmed</span>'}
LAW_106 = "https://www.nysenate.gov/legislation/laws/ABC/106"
LAW_65 = "https://www.nysenate.gov/legislation/laws/ABC/65"
LAW_65C = "https://www.nysenate.gov/legislation/laws/ABC/65-C"
SLA_HOURS = "https://sla.ny.gov/county-closing-hours"
LAW_CHECKED = "2026-10-23"


def config():
    p = ROOT / "config.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _t(hm):
    """'27:30' -> '3:30am'; 'late' stays 'late'."""
    if hm == "late":
        return "late"
    h, m = (int(x) for x in hm.split(":"))
    h %= 24
    if h == 0 and m == 0:
        return "midnight"
    ap = "am" if h < 12 else "pm"
    hh = 12 if h % 12 == 0 else h % 12
    return f"{hh}{':%02d' % m if m else ''}{ap}"


def span_text(span):
    a, b = span.split("-")
    return f"{_t(a)}–{_t(b)}"


def close_mins(span):
    b = span.split("-")[1]
    if b == "late":
        return 9999
    h, m = (int(x) for x in b.split(":"))
    return h * 60 + m


def late_venues(vs, now):
    """Checked venues whose weekly hours run to midnight or later on this night.

    The night's weekday is the evening's date: 1am Wednesday is still Tuesday night.
    Event-only rooms have no weekly hours and are not listed as open.
    """
    import events
    begin, _ = events.night_window(now)
    key = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][begin.weekday()]
    out = []
    for v in vs or []:
        if v.get("status") == "closed":
            continue
        hours = v.get("hours") or {}
        if hours.get("kind") == "event":
            continue
        span = (hours.get("week") or {}).get(key)
        if not span:
            continue
        mins = close_mins(span)
        if mins >= 24 * 60:
            out.append((v, span, mins))
    out.sort(key=lambda row: (-row[2], (row[0].get("name") or "").lower()))
    return out


def late_posters(vs, now, limit=8):
    import present
    rows = late_venues(vs, now)
    html_cards = "".join(present.venue_poster(v, span_text(span)) for v, span, _mins in rows[:limit])
    return rows, html_cards


# ---------------------------------------------------------------- venue pages

def week_table(v):
    h = v.get("hours") or {}
    week = h.get("week") or {}
    if h.get("kind") != "fixed" or not week:
        return ""
    cells = "".join(f'<tr><th scope="row">{d}</th><td>{e(span_text(week[k])) if k in week else "Closed or not listed"}</td></tr>'
                    for k, d in DAYS)
    note = f'<p class="small"><b>Note:</b> {e(h["note"])}</p>' if h.get("note") else ""
    status = {"likely": " (one source)", "unconfirmed": " (unconfirmed)"}.get(h.get("status") or "", "")
    return (f'<h2>Hours by day</h2><table class="hours-table"><tbody>{cells}</tbody></table>{note}'
            f'<p class="small">Laid out from the Hours fact above{status}. '
            'Late times run into the next morning. Holidays and events change them.</p>')


# ---------------------------------------------------------------- Tonight

def tonight_page(H, vs):
    import events
    import present
    u = H["u"]
    snap = events.load_snapshot()
    now = events.local_now()
    tonight, week = present.split_events(snap.get("events") or [], now)
    fetched_at = snap.get("fetched_at") or ""
    fetched = fetched_at[:10] or now.date().isoformat()
    late_rows, posters = late_posters(vs, now)
    note = ("Listings come from NYC Open Data (Parks events and permitted street festivals) and, when a key is configured, Ticketmaster Discovery for music, comedy, theatre, and nightlife. "
            "Ticketmaster links are the event URL, with no affiliate tag. Images from Ticketmaster are loaded beside that event only. "
            f"Feed checked {fetched}.")
    week_note = "The next listings after tonight, from the same feeds."
    short = present.tonight_short(now, len(tonight), len(week))
    line = present.hero_line(now, len(tonight), len(tonight) + len(week), len(late_rows))
    attrs = present.night_attrs("tonight")
    if tonight:
        tonight_html = present.events_html(tonight, "Tonight", note,
                                           "Nothing in the 5pm–5am window is still ahead in the latest feed.", attrs)
        later = week
        later_heading = "This week"
    else:
        tonight_html = present.empty_night(week[:6], posters, note, attrs)
        later = week[6:]
        later_heading = "Later this week"
    faqs = [
        ("What time do NYC bars stop serving?",
         "4am. New York State law stops on-premises alcohol sales at 4am in all five boroughs. The closing-time guide cites the statute."),
        ("Where do these event listings come from?",
         "NYC Parks public events and NYC permitted events, both from NYC Open Data, plus Ticketmaster Discovery when the site's build has a key. We do not scrape Resident Advisor or SeatGeek."),
        ("Are Ticketmaster links affiliate links?",
         "No. The button goes to the event URL Ticketmaster returned. Viator booking links elsewhere on the page are the affiliate links, and they are labeled."),
        ("Why is a show missing?",
         "The parks feed is mostly daytime programs, and we keep concerts, festivals, theater, and dance performances. Ticketmaster is limited to the next seven days in New York City. Anything outside those feeds is not listed."),
    ]
    schemas = [
        {"@context": "https://schema.org", "@type": "WebPage", "name": "Tonight in NYC",
         "url": "https://nynightlife.com/tonight/", "dateModified": fetched},
        present.faq_schema(faqs),
        present.item_list("Tonight and this week", [(ev["title"], "/tonight/") for ev in (tonight + week)[:30]]),
    ]
    schemas += [s for s in (present.event_schema(ev) for ev in (tonight + week)[:24]) if s]
    body = f"""<p class="eyebrow" style="margin-top:8px"><span class="line-mark" aria-hidden="true">N</span>New York City</p><h1>Tonight</h1>
<p class="hero-live" data-night-line>{e(line)}</p>
{present.answer_box(short, "tonight")}
{present.route_html()}
{tonight_html}
{present.events_html(later[:24], later_heading, week_note, "No later listings in this feed.", "data-week-events")}
{present.faq_html(faqs)}
<h2>Open now, from checked hours</h2>
<p class="lede">Which of our checked venues are open tonight, tonight's forecast, nightlife headlines and new liquor licenses.</p>
<div id="tonight" class="live" aria-live="polite"><p class="small">Loading tonight's list…</p>
<noscript><p>This page needs JavaScript to work out what's open right now in New York time. Every venue's hours are on its own page: <a href="{u('/venues/')}">all venues</a>.</p></noscript></div>
<h2>Good to know</h2>
<ul class="clean"><li>Friday through Sunday: <a href="{u('/this-weekend/')}">this weekend</a>.</li>
<li>NYC bars stop serving at 4am by state law. <a href="{u('/guides/nyc-bar-closing-time.html')}">Closing time, explained</a>.</li>
<li>Under 21? <a href="{u('/guides/under-21-nyc-bars-clubs.html')}">Which venues let you in</a>.</li>
<li>Dressing for the door: <a href="{u('/guides/nyc-dress-codes.html')}">every dress code in one table</a>.</li>
<li>Comedy tonight: <a href="{u('/guides/nyc-comedy-clubs.html')}">clubs we could verify</a>, plus any comedy row in the feed above.</li>
<li>Lights, winter villages, and Christmas Eve hours we could verify: <a href="{u('/guides/nyc-holiday-nights.html')}">holiday nights 2026</a>.</li></ul>
{affiliates.block(affiliates.TONIGHT, "nynightlife-tonight", "tonight", u, "Book a night out")}
{newsletter_block(H)}
<script defer src="{u('/js/live.js')}?v={H['LIVE_V']}"></script>
<script defer src="{H['tonight_js']}"></script>"""
    H["write"]("/tonight/index.html", H["page"]("Tonight in NYC: what's on | NY Nightlife",
                                                "What's on in NYC tonight and this week from NYC Open Data and Ticketmaster, plus which checked bars are open.",
                                                "/tonight/", body, schemas, "no-bar",
                                                updated=events.refresh_stamp(fetched_at) or fetched,
                                                updated_iso=fetched_at or fetched))


def weekend_late(vs, limit=8):
    """Checked venues open past midnight on Friday, Saturday, or Sunday."""
    import present
    rows = []
    labels = {"fri": "Fri", "sat": "Sat", "sun": "Sun"}
    for v in vs or []:
        if v.get("status") == "closed":
            continue
        hours = v.get("hours") or {}
        if hours.get("kind") == "event":
            continue
        week = hours.get("week") or {}
        best = None
        for key, label in labels.items():
            span = week.get(key)
            if not span:
                continue
            mins = close_mins(span)
            if mins >= 24 * 60 and (best is None or mins > best[0]):
                best = (mins, label, span)
        if best:
            rows.append((v, best[1], best[2], best[0]))
    rows.sort(key=lambda row: (-row[3], (row[0].get("name") or "").lower()))
    html_cards = "".join(
        present.venue_poster(v, f"{label} {span_text(span)}") for v, label, span, _mins in rows[:limit])
    return rows, html_cards


def weekend_page(H, vs):
    import events
    import present
    import affiliates
    u = H["u"]
    snap = events.load_snapshot()
    now = events.local_now()
    rows = present.weekend_events(snap.get("events") or [], now)
    fetched_at = snap.get("fetched_at") or ""
    fetched = fetched_at[:10] or now.date().isoformat()
    facts = events.weekend_facts(now)
    late_rows, posters = weekend_late(vs)
    note = ("Events that start between Friday at 5am and Monday at 5am New York time. "
            "A start after midnight is shown on the previous night, same as Tonight. "
            "Listings come from NYC Open Data and, when a key is configured, Ticketmaster Discovery. "
            "Ticketmaster links are the event URL. "
            f"Feed checked {fetched}.")
    short = present.weekend_short(now, len(rows))
    line = present.weekend_line(now, len(rows))
    attrs = present.night_attrs("weekend")
    listed = rows[:30]
    faqs = [
        ("What counts as this weekend?",
         "Friday at 5am through Monday at 5am, New York time. Monday, Tuesday, Wednesday, and Thursday show the coming Friday. Friday, Saturday, and Sunday show the Friday already underway. Monday before 5am is still Sunday night. The 5am cutoff is the same one Tonight uses, so Thursday night is not part of the weekend."),
        ("Where do these listings come from?",
         "NYC Parks public events and NYC permitted events, both from NYC Open Data, plus Ticketmaster Discovery when the site's build has a key. We do not scrape Resident Advisor or SeatGeek. Viator cards on this page are separate, labeled booking links."),
        ("Are the booking links affiliate links?",
         "Viator links are affiliate links (partner ID P00330813) and Klook links are affiliate links (account AID 145278). Both are marked sponsored. Ticketmaster buttons, when a listing has one, go to the event URL Ticketmaster returned and are not affiliate links."),
        ("Why is a show missing?",
         "The parks feed is mostly daytime programs, and we keep concerts, festivals, theater, and dance performances. Ticketmaster is limited to the next seven days in New York City. Anything outside those feeds is not listed. A missing listing means the feed did not include it."),
    ]
    schemas = [
        {"@context": "https://schema.org", "@type": "WebPage", "name": "This weekend in NYC",
         "url": "https://nynightlife.com/this-weekend/", "dateModified": fetched},
        present.faq_schema(faqs),
        present.item_list(
            "This weekend",
            [(ev["title"], "/this-weekend/") for ev in listed] or
            [(v.get("name") or "Venue", "/venues/" + v["slug"] + ".html") for v, _label, _span, _mins in late_rows[:8]]),
    ]
    schemas += [s for s in (present.event_schema(ev) for ev in listed[:24]) if s]
    late_block = ""
    if posters:
        late_block = (f'<h2>Open past midnight</h2>'
                      f'<p class="small">Checked weekly hours on Friday, Saturday, or Sunday. '
                      f'Not a live door report, and not a New Year\'s Eve schedule.</p>'
                      f'<div class="pcards">{posters}</div>')
    span = f"{facts['fri_long']} {facts['fri_mon']} {facts['fri_day']}–{facts['sun_long']} {facts['sun_mon']} {facts['sun_day']}"
    body = f"""<p class="eyebrow" style="margin-top:8px"><span class="line-mark" aria-hidden="true">N</span>New York City</p><h1>This weekend</h1>
<p class="hero-live" data-night-line>{e(line)}</p>
{present.answer_box(short, "weekend")}
{present.route_html()}
{present.weekend_html(listed, now, note, attrs)}
{late_block}
<h2>Good to know</h2>
<ul class="clean"><li>Tonight's slice of the same feed: <a href="{u('/tonight/')}">what's on tonight</a>.</li>
<li>NYC bars stop serving at 4am by state law. <a href="{u('/guides/nyc-bar-closing-time.html')}">Closing time, explained</a>.</li>
<li>Hidden doors we could check: <a href="{u('/guides/nyc-speakeasies.html')}">NYC speakeasies</a>.</li>
<li>Rooftop hours and dress codes: <a href="{u('/guides/nyc-rooftop-bars.html')}">NYC rooftop bars</a>.</li>
<li>December 31 is its own page: <a href="{u('/guides/nyc-new-years-eve.html')}">New Year's Eve 2026</a>.</li>
<li>Thanksgiving through New Year's Day: <a href="{u('/guides/nyc-holiday-nights.html')}">holiday nights 2026</a>.</li>
<li>A group plan: <a href="{u('/plans/')}">group nights</a>.</li></ul>
{affiliates.block(affiliates.WEEKEND, "nynightlife-this-weekend", "this-weekend", u, "Book a weekend tour or cruise")}
{affiliates.klook_block(affiliates.KLOOK_AHEAD, "klook:this-weekend", u, "Book ahead", "Klook listings for a New York visit, separate from the event feed and the Viator links above. " + affiliates.NOTE)}
{newsletter_block(H)}
<script defer src="{H['tonight_js']}"></script>"""
    title = "NYC this weekend | NY Nightlife"
    if len(title) > 60:
        raise SystemExit(f"title over 60 characters ({len(title)}): {title}")
    H["write"]("/this-weekend/index.html", H["page"](
        title,
        f"What's on in NYC {span}: Friday through Sunday from the same feeds as Tonight, plus bars open past midnight.",
        "/this-weekend/", body, schemas, "no-bar",
        updated=events.refresh_stamp(fetched_at) or fetched,
        updated_iso=fetched_at or fetched,
        crumb_label="This weekend"))


def home_box(H):
    u = H["u"]
    return f"""<div id="tonight-box" class="card live" aria-live="polite"><h2>Tonight in NYC</h2>
<p><a href="{u('/tonight/')}">See what's open tonight →</a></p></div>
<script defer src="{u('/js/live.js')}?v={H['LIVE_V']}"></script>"""


# ---------------------------------------------------------------- guides

def _vlink(H, v):
    flag = ' <span class="chip">status unclear</span>' if v.get("status") == "unclear" else ""
    return f'<a href="{H["u"]("/venues/" + v["slug"] + ".html")}">{e(v["name"])}</a>{flag}'


def _fact_txt(f, key="value"):
    f = f or {}
    val = (f.get(key) or "").strip()
    return (e(val) if val else "Not found yet") + (HOURS_CHIP.get(f.get("status") or "", "") if val else "")


def guide_under21(H, vs):
    live = [v for v in vs if v.get("status") != "closed"]
    in21 = [v for v in live if "under21" in ((v.get("chat") or {}).get("tags") or [])]
    rest = [v for v in live if v not in in21]
    checked = max(v.get("checked", "2026-10-18") for v in live)
    rows = "".join(f'<tr><td data-label="Venue">{_vlink(H, v)}<div class="small">{e(v.get("neighborhood", ""))}</div></td>'
                   f'<td data-label="Who gets in">{_fact_txt(v.get("age"))}</td></tr>' for v in in21)
    rest_rows = "".join(f'<tr><td data-label="Venue">{_vlink(H, v)}</td><td data-label="Age">{_fact_txt(v.get("age"))}</td></tr>'
                        for v in sorted(rest, key=lambda x: x["name"].lower()))
    import present
    passport = [v for v in live if "passport" in ((v.get("age") or {}).get("value") or "").lower()]
    updated = max(checked, LAW_CHECKED)
    lede = (f"In New York you must be 21 to buy or drink alcohol. Whether you can walk in under 21 is up to each venue. "
            f"Of the {len(live)} venues we've checked, {len(in21)} let some under-21s in, at some times, with conditions.")
    body = present.guide_hero(
        "Under 21 in NYC: which bars and clubs let you in",
        f"Guide · updated {H['fmt_date'](updated)} · venue facts checked {H['fmt_date'](checked)}",
        updated, present.place_chips(in21) or ["21+", "ID"]) + present.answer_box(lede) + present.jump_nav([
            ("law", "The law"), ("admit", "Who gets in"), ("rest", "Everywhere else")]) + f"""
<div class="card" id="law"><ul class="clean">
<li>The law: no one may sell or give alcohol to anyone under 21 (<a href="{LAW_65}" rel="noopener">NY ABC Law §65</a>), and under-21s may not possess it intending to drink (<a href="{LAW_65C}" rel="noopener">§65-c</a>).</li>
<li>Entry age is each venue's own policy, and it often changes by night or event. Read the conditions, then check the event listing.</li>
<li>Bring a physical government photo ID.{' ' + str(len(passport)) + ' of the venues we have checked say a non-US ID must be a passport; see each venue page.' if passport else ''}</li></ul></div>
<h2 id="admit">Venues that admit some under-21s</h2>
<div class="scroll-x"><table class="compare"><thead><tr><th>Venue</th><th>Who gets in (as checked)</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2 id="rest">Everywhere else we've checked</h2>
<p>These say 21 or older, or haven't published an age.</p>
<div class="scroll-x"><table class="compare"><thead><tr><th>Venue</th><th>Age</th></tr></thead><tbody>{rest_rows}</tbody></table></div>
<p class="small">Each venue's age policy links to its sources on the venue page. Law text checked {H['fmt_date'](LAW_CHECKED)}. This isn't legal advice.</p>"""
    schema = {"@context": "https://schema.org", "@type": "Article", "headline": "Under 21 in NYC: which bars and clubs let you in",
              "dateModified": updated, "author": {"@type": "Person", "name": "Dan Herlehy"}}
    path = "/guides/under-21-nyc-bars-clubs.html"
    H["write"](path, H["page"]("Under 21 in NYC bars and clubs | NY Nightlife",
                               f"Which NYC bars and clubs admit under-21s, with each venue's exact age policy and sources. Checked {H['fmt_date'](checked)}.",
                               path, body, schema, "no-bar"))
    return path, updated


def _note_fits(note, day):
    """A note about one weekday only belongs in that weekday's table."""
    named = [d for d, full in (("fri", "Friday"), ("sat", "Saturday"), ("thu", "Thursday")) if note.startswith(full)]
    return not named or named[0] == day


def _after4(H, live):
    """Only venues whose own checked hours text says they run past 4am."""
    picks = {"nowadays": "the indoor room runs Friday 10pm to about 6am",
             "knockdown-center": "club nights can run as late as 5am"}
    by = {v["slug"]: v for v in live}
    bits = [f'{_vlink(H, by[s])}: {e(t)}{HOURS_CHIP.get((by[s].get("hours") or {}).get("status") or "", "")}'
            for s, t in picks.items() if s in by]
    return "; ".join(bits) + ". Drinks still stop at 4am." if bits else "none list hours past 4am."


def guide_closing(H, vs):
    live = [v for v in vs if v.get("status") != "closed"]
    checked = max(v.get("checked", "2026-10-18") for v in live)

    def late_table(day):
        rows = []
        for v in live:
            h = v.get("hours") or {}
            span = (h.get("week") or {}).get(day)
            if h.get("kind") == "fixed" and span:
                rows.append((close_mins(span), v, span, h))
        rows.sort(key=lambda r: (-r[0], r[1]["name"].lower()))
        return "".join(f'<tr><td data-label="Venue">{_vlink(H, v)}<div class="small">{e(v.get("neighborhood", ""))}</div></td>'
                       f'<td data-label="Hours">{e(span_text(span))}{HOURS_CHIP.get(h.get("status") or "", "")}'
                       + (f'<div class="small">{e(h["note"])}</div>' if h.get("note") and _note_fits(h["note"], day) else "") + '</td></tr>'
                       for _, v, span, h in rows)
    events = [v for v in live if (v.get("hours") or {}).get("kind") == "event"]
    import present
    updated = max(checked, LAW_CHECKED)
    body = present.guide_hero(
        "What time do NYC bars close?",
        f"Guide · updated {H['fmt_date'](updated)} · venue hours checked {H['fmt_date'](checked)}",
        updated, ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]) + present.answer_box(
        "4am. New York State law stops on-premises alcohol sales at 4am in all five boroughs, and drinks must be finished by 4:30am. Many places close earlier.") + present.jump_nav([
            ("law", "The rule"), ("after", "After 4am"), ("saturday", "Saturday"), ("thursday", "Thursday")]) + f"""
<div class="card" id="law"><ul class="clean">
<li>Bars and restaurants can't sell drinks for on-premises drinking from 4am to 8am, or 4am to 10am on Sunday (<a href="{LAW_106}" rel="noopener">NY ABC Law §106(5)</a>).</li>
<li>No one may drink on the premises more than half an hour after 4am (same section).</li>
<li>The State Liquor Authority lists 4am closing for Manhattan, Brooklyn, Queens, the Bronx and Staten Island (<a href="{SLA_HOURS}" rel="noopener">county closing hours</a>).</li>
<li>A venue's own license or choice can set earlier hours. That's why a club "open till 4am" may stop serving earlier.</li></ul></div>
<h2 id="after">Dancing after 4am</h2>
<p>The 4am rule is about selling alcohol, not about music. Some clubs keep going after the bar shuts: of the venues we've checked, {_after4(H, live)}</p>
<h2 id="saturday">Who stays open latest on a Saturday</h2>
<p>Saturday-night hours of the venues we've checked, latest first (times after midnight are Sunday morning).</p>
<div class="scroll-x"><table class="compare"><thead><tr><th>Venue</th><th>Saturday hours</th></tr></thead><tbody>{late_table('sat')}</tbody></table></div>
<h2 id="thursday">On a Thursday</h2>
<div class="scroll-x"><table class="compare"><thead><tr><th>Venue</th><th>Thursday hours</th></tr></thead><tbody>{late_table('thu')}</tbody></table></div>
<p>Event-night venues (no fixed hours, check each listing): {', '.join(_vlink(H, v) for v in events)}.</p>
<p>Out right now? <a href="{H['u']('/tonight/')}">See what's open tonight</a>.</p>
<p class="small">Hours come from each venue's checked page; tap through for sources. Law text checked {H['fmt_date'](LAW_CHECKED)}. This isn't legal advice.</p>"""
    schema = {"@context": "https://schema.org", "@type": "Article", "headline": "What time do NYC bars close?",
              "dateModified": updated, "author": {"@type": "Person", "name": "Dan Herlehy"}}
    path = "/guides/nyc-bar-closing-time.html"
    H["write"](path, H["page"]("NYC bar closing time: the 4am rule | NY Nightlife",
                               "NYC bars must stop serving at 4am under state law. Here's the rule, and the checked hours of bars and clubs open latest.",
                               path, body, schema, "no-bar"))
    return path, updated


# ---------------------------------------------------------------- changes log

TRACK = [("status", None, "Status"), ("dress", "answer", "Dress code"), ("age", "value", "Age"), ("cover", "value", "Cover"),
         ("getting_in", "value", "Getting in"), ("hours", "value", "Hours"), ("price", "value", "Drinks")]
SEED = [{"date": "2026-10-18", "slug": "", "text": "All 30 venues re-checked against their own sites and independent sources; every fact now shows its sources and status."},
        {"date": "2026-10-18", "slug": "brooklyn-mirage", "text": "Brooklyn Mirage marked closed. The site reopened as Pacha New York."},
        {"date": "2026-10-18", "slug": "musica-club", "text": "Musica Club NYC marked status unclear: official websites down, no upcoming events listed."}]


def _facts(v):
    out = {}
    for k, sub, _ in TRACK:
        if sub is None:
            out[k] = v.get(k) or ""
        else:
            f = v.get(k) or {}
            out[k] = [(f.get(sub) or "").strip(), f.get("status") or ""]
    return out


def update_changes(vs):
    """Compare each venue's facts with the last build's snapshot; record real changes, dated
    with the venue's own check date. Re-running with nothing changed adds nothing."""
    snap_p, log_p = ROOT / "data" / "facts-snapshot.json", ROOT / "data" / "changes.json"
    snap = json.loads(snap_p.read_text(encoding="utf-8")) if snap_p.exists() else None
    log = json.loads(log_p.read_text(encoding="utf-8")) if log_p.exists() else list(SEED)
    now = {v["slug"]: _facts(v) for v in vs}
    if snap is not None:
        for v in vs:
            old = snap.get(v["slug"])
            if old is None:
                log.append({"date": v.get("checked", ""), "slug": v["slug"], "text": f"{v['name']} added to the site."})
                continue
            for k, _, label in TRACK:
                if old.get(k) != now[v["slug"]][k]:
                    new = now[v["slug"]][k]
                    shown = new if isinstance(new, str) else (new[0] or "not found yet")
                    log.append({"date": v.get("checked", ""), "slug": v["slug"], "text": f"{v['name']}: {label.lower()} now “{shown}”."})
    snap_p.write_text(json.dumps(now, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    log_p.write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return sorted(log, key=lambda x: x["date"], reverse=True)


def _gid(c):
    """Stable per entry, so feed readers never show an old change as new."""
    import hashlib
    return hashlib.sha1((c["date"] + c["slug"] + c["text"]).encode("utf-8")).hexdigest()[:12]


def changes_pages(H, vs):
    log = update_changes(vs)
    by = {v["slug"]: v for v in vs}
    items = "".join(f'<li><span class="small">{H["fmt_date"](c["date"])}</span><br>{e(c["text"])}'
                    + (f' {_vlink(H, by[c["slug"]])} →' if c["slug"] in by else "") + "</li>" for c in log)
    latest = log[0]["date"] if log else "2026-10-18"
    u = H["u"]
    body = f"""<p class="eyebrow" style="margin-top:20px">Log · last change {H['fmt_date'](latest)}</p><h1>What changed</h1>
<p class="lede">Every change to a checked fact on this site: covers, dress codes, ages, hours, closures. Dated with the day we checked.</p>
<p><a href="{u('/feed.xml')}">Follow by RSS</a>{' · ' + '<a href="' + u('/tonight/') + '">Tonight</a>'}</p>
<ul class="clean changes">{items}</ul>
{newsletter_block(H)}"""
    schema = {"@context": "https://schema.org", "@type": "WebPage", "name": "What changed on NY Nightlife", "dateModified": latest}
    robots = "index,follow" if len(log) >= 8 else "noindex,follow"   # thin until there are real changes
    H["write"]("/changes/index.html", H["page"]("What changed: NYC bar & club fact updates | NY Nightlife",
                                                "A dated log of every change to the checked facts on NY Nightlife: covers, dress codes, ages, hours and closures.",
                                                "/changes/", body, schema, "no-bar", robots))
    # RSS 2.0, built with escaping (no raw HTML from anywhere)
    def rfc(d):
        return format_datetime(dt.datetime.fromisoformat(d).replace(hour=12, tzinfo=dt.timezone.utc))
    entries = ""
    for i, c in enumerate(log[:40]):
        link = f"{SITE}/venues/{c['slug']}.html" if c["slug"] in by else f"{SITE}/changes/"
        entries += (f"<item><title>{e(c['text'])}</title><link>{e(link)}</link>"
                    f"<guid isPermaLink=\"false\">nyn-change-{_gid(c)}</guid><pubDate>{rfc(c['date'])}</pubDate></item>\n")
    (H["OUT"] / "feed.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>\n'
        f"<title>NY Nightlife: what changed</title><link>{SITE}/changes/</link>"
        "<description>Changes to checked NYC bar and club facts: covers, dress codes, ages, hours, closures.</description>\n"
        f"{entries}</channel></rss>\n", encoding="utf-8", newline="\n")
    return latest if len(log) >= 8 else None


# ---------------------------------------------------------------- newsletter

KIT_PREFIX = "https://app.kit.com/forms/"


def newsletter_block(H):
    action = (config().get("kit_form_action") or "").strip()
    u = H["u"]
    if action.startswith(KIT_PREFIX):
        return f"""<div class="card news-signup"><h2>The weekly email</h2>
<p>What changed at the venues we track, who's open late, and new licenses. Free. One email a week, unsubscribe anytime.</p>
<form method="post" action="{e(action)}" class="signup"><label for="nl-email">Email</label>
<input id="nl-email" type="email" name="email_address" required autocomplete="email">
<button class="btn primary" type="submit">Sign up</button></form>
<p class="small">Sent with Kit. We only use your email for this newsletter. See <a href="{u('/privacy.html')}">privacy</a>.</p></div>"""
    return f"""<div class="card news-signup"><h2>Follow the changes</h2>
<p>A weekly email is planned. Until then, get every change to our checked facts by <a href="{u('/feed.xml')}">RSS</a>, or check <a href="{u('/changes/')}">What changed</a>.</p></div>"""
