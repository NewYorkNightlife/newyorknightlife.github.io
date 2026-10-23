"""Pages added in the Oct 2026 "alive" pass: Tonight, two guides, the changes log + RSS,
weekly hours tables, and the newsletter block.

Static and built from checked data, except the Tonight sections that js/live.js fills from
data/live/*.json (written by the scheduled job, _build/live.py).
"""
import html
import json
import pathlib
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
    u = H["u"]
    body = f"""<p class="eyebrow" style="margin-top:20px">New York City · tonight</p><h1>Tonight</h1>
<p class="lede">Which of our checked venues are open tonight, tonight's forecast, nightlife headlines and new liquor licenses.</p>
<div id="tonight" class="live" aria-live="polite"><p class="small">Loading tonight's list…</p>
<noscript><p>This page needs JavaScript to work out what's open right now in New York time. Every venue's hours are on its own page: <a href="{u('/venues/')}">all venues</a>.</p></noscript></div>
<h2>Good to know</h2>
<ul class="clean"><li>NYC bars stop serving at 4am by state law. <a href="{u('/guides/nyc-bar-closing-time.html')}">Closing time, explained</a>.</li>
<li>Under 21? <a href="{u('/guides/under-21-nyc-bars-clubs.html')}">Which venues let you in</a>.</li>
<li>Dressing for the door: <a href="{u('/guides/nyc-dress-codes.html')}">every dress code in one table</a>.</li></ul>
{newsletter_block(H)}
<script defer src="{u('/js/live.js')}?v={H['LIVE_V']}"></script>"""
    H["write"]("/tonight/index.html", H["page"]("Tonight in NYC: what's open, forecast and nightlife headlines | NY Nightlife",
                                                "Which checked NYC bars and clubs are open tonight, the forecast, nightlife headlines and new liquor licenses.",
                                                "/tonight/", body, None, "no-bar", "noindex,follow"))


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
    passport = [v for v in live if "passport" in ((v.get("age") or {}).get("value") or "").lower()]
    updated = max(checked, LAW_CHECKED)
    body = f"""<p class="eyebrow" style="margin-top:20px">Guide · updated {H['fmt_date'](updated)} · venue facts checked {H['fmt_date'](checked)}</p>
<h1>Under 21 in NYC: which bars and clubs let you in</h1>
<p class="lede">In New York you must be 21 to buy or drink alcohol. Whether you can walk in under 21 is up to each venue. Of the {len(live)} venues we've checked, {len(in21)} let some under-21s in, at some times, with conditions.</p>
<div class="card"><ul class="clean">
<li>The law: no one may sell or give alcohol to anyone under 21 (<a href="{LAW_65}" rel="noopener">NY ABC Law §65</a>), and under-21s may not possess it intending to drink (<a href="{LAW_65C}" rel="noopener">§65-c</a>).</li>
<li>Entry age is each venue's own policy, and it often changes by night or event. Read the conditions, then check the event listing.</li>
<li>Bring a physical government photo ID.{' ' + str(len(passport)) + ' of the venues we have checked say a non-US ID must be a passport; see each venue page.' if passport else ''}</li></ul></div>
<h2>Venues that admit some under-21s</h2>
<div class="scroll-x"><table class="compare"><thead><tr><th>Venue</th><th>Who gets in (as checked)</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Everywhere else we've checked</h2>
<p>These say 21 or older, or haven't published an age.</p>
<div class="scroll-x"><table class="compare"><thead><tr><th>Venue</th><th>Age</th></tr></thead><tbody>{rest_rows}</tbody></table></div>
<p class="small">Each venue's age policy links to its sources on the venue page. Law text checked {H['fmt_date'](LAW_CHECKED)}. This isn't legal advice.</p>"""
    schema = {"@context": "https://schema.org", "@type": "Article", "headline": "Under 21 in NYC: which bars and clubs let you in",
              "dateModified": updated, "author": {"@type": "Person", "name": "Dan Herlehy"}}
    path = "/guides/under-21-nyc-bars-clubs.html"
    H["write"](path, H["page"]("Under 21 in NYC: which bars & clubs let you in (checked) | NY Nightlife",
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
    updated = max(checked, LAW_CHECKED)
    body = f"""<p class="eyebrow" style="margin-top:20px">Guide · updated {H['fmt_date'](updated)} · venue hours checked {H['fmt_date'](checked)}</p>
<h1>What time do NYC bars close?</h1>
<p class="lede">4am. New York State law stops on-premises alcohol sales at 4am in all five boroughs, and drinks must be finished by 4:30am. Many places close earlier.</p>
<div class="card"><ul class="clean">
<li>Bars and restaurants can't sell drinks for on-premises drinking from 4am to 8am, or 4am to 10am on Sunday (<a href="{LAW_106}" rel="noopener">NY ABC Law §106(5)</a>).</li>
<li>No one may drink on the premises more than half an hour after 4am (same section).</li>
<li>The State Liquor Authority lists 4am closing for Manhattan, Brooklyn, Queens, the Bronx and Staten Island (<a href="{SLA_HOURS}" rel="noopener">county closing hours</a>).</li>
<li>A venue's own license or choice can set earlier hours. That's why a club "open till 4am" may stop serving earlier.</li></ul></div>
<h2>Dancing after 4am</h2>
<p>The 4am rule is about selling alcohol, not about music. Some clubs keep going after the bar shuts: of the venues we've checked, {_after4(H, live)}</p>
<h2>Who stays open latest on a Saturday</h2>
<p>Saturday-night hours of the venues we've checked, latest first (times after midnight are Sunday morning).</p>
<div class="scroll-x"><table class="compare"><thead><tr><th>Venue</th><th>Saturday hours</th></tr></thead><tbody>{late_table('sat')}</tbody></table></div>
<h2>On a Thursday</h2>
<div class="scroll-x"><table class="compare"><thead><tr><th>Venue</th><th>Thursday hours</th></tr></thead><tbody>{late_table('thu')}</tbody></table></div>
<p>Event-night venues (no fixed hours, check each listing): {', '.join(_vlink(H, v) for v in events)}.</p>
<p>Out right now? <a href="{H['u']('/tonight/')}">See what's open tonight</a>.</p>
<p class="small">Hours come from each venue's checked page; tap through for sources. Law text checked {H['fmt_date'](LAW_CHECKED)}. This isn't legal advice.</p>"""
    schema = {"@context": "https://schema.org", "@type": "Article", "headline": "What time do NYC bars close?",
              "dateModified": updated, "author": {"@type": "Person", "name": "Dan Herlehy"}}
    path = "/guides/nyc-bar-closing-time.html"
    H["write"](path, H["page"]("What time do NYC bars close? 4am, and who stays open latest | NY Nightlife",
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
