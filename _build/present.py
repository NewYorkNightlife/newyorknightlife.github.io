"""HTML and schema fragments built only from checked venue facts or event rows."""
import datetime as dt
import html
import re
import urllib.parse

import events as evs

e = html.escape
SITE = "https://nynightlife.com"

MARK = {
    "music": "M", "comedy": "C", "club": "K", "nightlife": "N", "theatre": "A",
    "parks": "P", "festival": "F", "tour": "T", "cruise": "B",
}
CAT_LABEL = {
    "music": "Music", "comedy": "Comedy", "club": "Dance", "nightlife": "Nightlife",
    "theatre": "Theatre", "parks": "Parks", "festival": "Festival", "tour": "Tour",
    "cruise": "Cruise",
}


def words(text):
    return re.findall(r"[A-Za-z0-9$][A-Za-z0-9'’&$–-]*", text or "")


def _one(fact, key):
    return ((fact or {}).get(key) or "").strip()


def short_answer(v):
    """40–60 words from fields already on the venue. No new claims."""
    if v.get("status") == "closed":
        note = (v.get("status_note") or "It is marked closed on this site.").strip()
        text = (f"{v['name']} in {v.get('neighborhood', 'New York')} is marked closed. {note} "
                f"This page does not list it as open. Facts checked {v.get('checked', '')}.")
    else:
        place = ", ".join(x for x in (v.get("neighborhood"), v.get("borough")) if x) or "New York"
        dress = _one(v.get("dress"), "answer")
        if not dress or dress.lower() == "none published":
            dress_bit = "No dress code is posted"
        else:
            dress_bit = "Dress code: " + dress.rstrip(".")
        cover = _one(v.get("cover"), "value")
        cover_bit = ("Cover: " + cover.rstrip(".")) if cover else "No cover is listed"
        hours = _one(v.get("hours"), "value")
        hours_bit = ("Hours: " + hours.rstrip(".")) if hours else "Fixed hours are not listed"
        gi = _one(v.get("getting_in"), "value")
        gi_bit = gi.split(".")[0].strip() if gi else ""
        text = (f"{v['name']} is a {v.get('type') or 'venue'} in {place}. {dress_bit}. {cover_bit}. "
                f"{hours_bit}.")
        if gi_bit:
            text += " " + gi_bit.rstrip(".") + "."
        text += f" Facts checked {v.get('checked', '')}."
    w = text.split()
    if len(w) > 60:
        # Drop the getting-in clause, which is the long one, then hard-cap.
        text = re.sub(r" Hours:.*", "", text)
        hours = _one(v.get("hours"), "value")
        if hours:
            text = text.rstrip(".") + ". Hours: " + hours.rstrip(".") + f". Facts checked {v.get('checked', '')}."
        w = text.split()
        if len(w) > 60:
            text = " ".join(w[:58]).rstrip(".,") + "."
    if len(text.split()) < 40:
        addr = (v.get("address") or "").strip()
        if addr:
            text = text.rstrip(".") + f". Address: {addr}."
        if len(text.split()) < 40:
            text += " Confirm with the venue before you go, because door rules change."
    return re.sub(r"\s+", " ", text).strip()


def venue_faqs(v):
    """Visible Q&As. Empty facts stay 'not found', they are not filled in."""
    name = v["name"]
    out = []
    dress = v.get("dress") or {}
    ans = _one(dress, "answer")
    detail = _one(dress, "detail")
    if v.get("status") == "closed":
        out.append((f"Is {name} open?", (v.get("status_note") or "It is marked closed.").strip()))
    if not ans and not detail:
        dress_a = "We have not found a published dress code."
    elif ans.lower() == "none published":
        dress_a = "No dress code is posted. " + (detail or "Door staff still decide.")
    else:
        dress_a = ans if not detail or detail in ans else ans.rstrip(".") + ". " + detail
    out.append((f"What is the dress code at {name}?", dress_a))
    age = _one(v.get("age"), "value")
    out.append((f"How old do you have to be for {name}?",
                age or "We have not found a published age policy."))
    cover = _one(v.get("cover"), "value")
    out.append((f"Is there a cover at {name}?", cover or "No cover is listed in the sources we checked."))
    hours = _one(v.get("hours"), "value")
    out.append((f"What time does {name} close?",
                hours or "Fixed hours are not listed. Check the venue before you go."))
    gi = _one(v.get("getting_in"), "value")
    book = (v.get("getting_in") or {}).get("booking_url")
    if gi or book:
        extra = " Booking link is the venue's own page." if book else ""
        out.append((f"How do you get into {name}?", (gi or "See the venue's booking page.") + extra))
    return out[:6]


def faq_html(pairs):
    if not pairs:
        return ""
    rows = []
    for q, a in pairs:
        rows.append(f"<details class=\"qa\" open><summary>{e(q)}</summary><p>{e(a)}</p></details>")
    return '<section class="faq" id="questions"><h2>Questions</h2>' + "".join(rows) + "</section>"


def faq_schema(pairs):
    if not pairs:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in pairs
        ],
    }


def opening_hours(v):
    hours = v.get("hours") or {}
    week = hours.get("week") or {}
    if hours.get("kind") != "fixed" or not week:
        return None
    names = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday",
             "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}
    out = []
    for key, label in names.items():
        span = week.get(key)
        if not span or "late" in span:
            continue
        try:
            a, b = span.split("-")
            oh, om = (int(x) for x in a.split(":"))
            ch, cm = (int(x) for x in b.split(":"))
        except ValueError:
            continue
        out.append({
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": label,
            "opens": f"{oh % 24:02d}:{om:02d}",
            "closes": f"{ch % 24:02d}:{cm:02d}",
        })
    return out or None


def breadcrumb_schema(crumbs):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + path}
            for i, (name, path) in enumerate(crumbs)
        ],
    }


def crumbs_html(crumbs):
    if len(crumbs) < 2:
        return ""
    bits = []
    for i, (name, path) in enumerate(crumbs):
        if i:
            bits.append('<span class="sep" aria-hidden="true">/</span>')
        if i == len(crumbs) - 1:
            bits.append(f'<span aria-current="page">{e(name)}</span>')
        else:
            bits.append(f'<a href="{e(path)}">{e(name)}</a>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + "".join(bits) + "</nav>"


def item_list(name, pairs):
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "url": SITE + path}
            for i, (n, path) in enumerate(pairs)
        ],
    }


# Used only when the source event has no image of its own. It is this site's
# share card, not a photo of the event.
FALLBACK_IMAGE = SITE + "/img/og/site.jpg"


def _https(url):
    url = (url or "").strip()
    return url if url.startswith("https://") else ""


def _event_image(ev):
    """The source image when we have one, otherwise the site card."""
    local = ev.get("image_local") or ""
    if local.startswith("/"):
        return SITE + local
    if local.startswith("https://"):
        return local
    remote = _https(ev.get("image_url"))
    host = (urllib.parse.urlsplit(remote).hostname or "").lower() if remote else ""
    if ev.get("source") == "ticketmaster" and evs.tm_image_ok(remote):
        return remote
    if remote and (host == "nycgovparks.org" or host.endswith(".nycgovparks.org")):
        return remote
    return FALLBACK_IMAGE


def _event_description(ev):
    """A description the source wrote. The permit blurb and the Ticketmaster
    street address are not descriptions, so they stay out."""
    text = (ev.get("description") or "").strip()
    if not text and ev.get("source") == "nyc_parks":
        text = (ev.get("blurb") or "").strip()
    return text


def event_schema(ev):
    """Event JSON-LD only when we have a real start time from the source.

    endDate, description, price, currency, and availability are omitted when
    the source did not provide them. image falls back to the site card.
    """
    if not ev.get("start") or ev.get("listing") or ev.get("source") == "viator":
        return None
    place = ev.get("venue_name") or "New York"
    loc = {
        "@type": "Place",
        "name": place,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": ev.get("borough") or "New York",
            "addressRegion": "NY",
            "addressCountry": "US",
        },
    }
    if ev.get("lat") is not None and ev.get("lng") is not None:
        loc["geo"] = {"@type": "GeoCoordinates", "latitude": ev["lat"], "longitude": ev["lng"]}
    data = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": ev.get("title"),
        "startDate": ev.get("start"),
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": loc,
        "image": _event_image(ev),
    }
    if ev.get("end"):
        data["endDate"] = ev["end"]
    desc = _event_description(ev)
    if desc:
        data["description"] = desc
    url = _https(ev.get("url"))
    if url:
        data["url"] = url
    org = {"nyc_parks": "NYC Parks", "nyc_permits": "NYC permitted event",
           "ticketmaster": "Ticketmaster"}.get(ev.get("source"))
    if org:
        organizer = {"@type": "Organization", "name": org}
        if url:
            organizer["url"] = url
        data["organizer"] = organizer
    if url:
        offer = {"@type": "Offer", "url": url}
        if ev.get("price_min") is not None:
            offer["price"] = ev["price_min"]
        currency = (ev.get("price_currency") or "").strip()
        if currency:
            offer["priceCurrency"] = currency
        availability = (ev.get("offer_availability") or "").strip()
        if availability.startswith("https://schema.org/"):
            offer["availability"] = availability
        data["offers"] = offer
    return data


def _when(ev):
    start = evs.parse_when(ev.get("start"))
    if not start:
        return ""
    hour = start.hour % 12 or 12
    minute = f":{start.minute:02d}" if start.minute else ""
    ap = "am" if start.hour < 12 else "pm"
    return start.strftime("%a %b ") + str(start.day) + f" · {hour}{minute}{ap}"


def event_card(ev):
    cat = ev.get("category") or "parks"
    mark = MARK.get(cat, "P")
    label = CAT_LABEL.get(cat, "Event")
    where = " · ".join(x for x in (ev.get("venue_name"), ev.get("borough")) if x)
    when = _when(ev)
    alt = e((ev.get("title") or "Event") + (" at " + ev["venue_name"] if ev.get("venue_name") else ""))
    src = ev.get("image_local") or ""
    if not src and ev.get("source") == "ticketmaster" and evs.tm_image_ok(ev.get("image_url") or ""):
        src = ev["image_url"]
    if src:
        w, h = ev.get("image_w") or 640, ev.get("image_h") or 360
        media = (f'<img src="{e(src)}" alt="{alt}" width="{int(w)}" height="{int(h)}" '
                 f'loading="lazy" decoding="async">')
    else:
        media = f'<span class="mark" aria-hidden="true">{e(mark)}</span>'
    price = ""
    if ev.get("price_min") is not None:
        width = max(4, min(100, float(ev["price_min"]) / 150 * 100))
        price = (f'<span class="pbar" role="img" aria-label="from ${ev["price_min"]:.0f} on a $0 to $150 scale">'
                 f'<i style="left:0;width:{width:.1f}%"></i></span>'
                 f'<span class="price">from ${ev["price_min"]:.0f}</span>')
    elif ev.get("source") == "nyc_parks":
        price = '<span class="price">NYC Parks listing</span>'
    source = ""
    if ev.get("source") == "ticketmaster":
        source = '<span class="price">Tickets via Ticketmaster</span>'
    href = ev.get("url") or "/tonight/"
    external = href.startswith("http")
    rel = ' rel="noopener" target="_blank"' if external else ""
    kicker = " · ".join(x for x in (label, when) if x)
    return (
        f'<a class="pcard rise" data-cat="{e(cat)}" href="{e(href)}"{rel}>'
        f'<span class="pcard-media cat-{e(cat)}">{media}</span>'
        f'<span class="pcard-body"><span class="kicker">{e(kicker)}</span>'
        f'<span class="t">{e(ev.get("title") or "Event")}</span>'
        f'<span class="m">{e(where)}</span>{price}{source}</span></a>'
    )


def _section_open(attrs):
    extra = f" {attrs}" if attrs else ""
    return f'<section class="whats-on"{extra}>'


def events_html(rows, heading, note, empty, attrs=""):
    if not rows:
        return (_section_open(attrs) + f"<h2>{e(heading)}</h2><p>{e(empty)}</p>"
                f"<p class=\"small\">{e(note)}</p></section>")
    cards = "".join(event_card(ev) for ev in rows)
    return (_section_open(attrs) + f"<h2>{e(heading)}</h2>"
            f"<p class=\"small\">{e(note)}</p><div class=\"pcards\">{cards}</div></section>")


def _initial(name):
    stripped = re.sub(r"^(the|a|an)\s+", "", (name or "").strip(), flags=re.I)
    for c in stripped:
        if c.isalnum():
            return c.upper()
    return "N"


def venue_poster(v, when):
    """A checked venue in the same poster frame as an event card."""
    slug = v.get("slug") or ""
    href = "/venues/" + slug + ".html" if slug else "/venues/"
    where = " · ".join(x for x in (v.get("neighborhood") or v.get("hood"), when) if x)
    return (
        f'<a class="pcard rise" data-cat="nightlife" href="{e(href)}">'
        f'<span class="pcard-media cat-nightlife"><span class="mark" aria-hidden="true">{e(_initial(v.get("name")))}</span></span>'
        f'<span class="pcard-body"><span class="kicker">Open past midnight</span>'
        f'<span class="t">{e(v.get("name") or "Venue")}</span>'
        f'<span class="m">{e(where)}</span></span></a>'
    )


def empty_night(next_rows, posters, note, attrs):
    """No bare zero. The night section shows what is next and who is open late."""
    parts = [_section_open(attrs), "<h2>Tonight</h2>",
             "<p>Nothing in the 5pm–5am window is still ahead in the latest feed.</p>",
             f'<p class="small">{e(note)}</p>']
    if next_rows:
        parts.append('<h2 class="as-h3">Next up</h2>')
        parts.append('<div class="pcards">' + "".join(event_card(ev) for ev in next_rows) + "</div>")
    if posters:
        parts.append('<h2 class="as-h3">Open past midnight</h2>')
        parts.append(f'<div class="pcards">{posters}</div>')
    parts.append("</section>")
    return "".join(parts)


def night_attrs(page):
    return (f'data-night-events data-night-page="{page}" '
            'data-events="/data/events.json" data-venues="/data/venues.json"')


def hero_line(now, tonight_n, week_n, late_n):
    facts = evs.night_facts(now)
    bits = [f"{facts['short']} {facts['iso']}"]
    bits.append(f"{tonight_n} tonight" if tonight_n else "Nothing listed tonight")
    if week_n:
        bits.append(f"{week_n} this week")
    if late_n:
        bits.append(f"{late_n} open past midnight")
    return " · ".join(bits)


def home_short(now, venues_n, tonight_n, late_n):
    facts = evs.night_facts(now)
    base = (f"Tonight in New York, this site lists {venues_n} checked bars and clubs "
            "and the public events we could pull for this week. ")
    if tonight_n and late_n:
        mid = (f"{tonight_n} of those events fall in tonight's 5pm to 5am window, "
               f"and {late_n} venues list hours past midnight on {facts['long']}. ")
    elif tonight_n:
        mid = f"{tonight_n} of those events fall in tonight's 5pm to 5am window. "
    else:
        mid = ("None of those events start in tonight's 5pm to 5am window. "
               "The next listings are below, with the venues that stay open past midnight"
               + (f" on {facts['long']}" if late_n else "") + ". ")
    return base + mid + "Dress code, age, and cover stay on each venue page with the date we checked them."


def weekend_events(rows, now):
    """Fri 5am through Mon 5am, minus anything that has already ended.

    Viator product rows stay off this list. The page has its own labeled
    Viator cards, and a product is not a show time.
    """
    begin, end = evs.weekend_window(now)
    kept = []
    for ev in rows or []:
        if ev.get("listing") or ev.get("source") == "viator" or not ev.get("start"):
            continue
        start = evs.parse_when(ev.get("start"))
        if not start or evs.has_ended(ev, now, start):
            continue
        start = start.astimezone(evs.NY)
        if begin <= start < end:
            kept.append(ev)
    kept.sort(key=lambda r: (r.get("start") or "", r.get("id") or ""))
    return kept


def _evening_day(start):
    start = start.astimezone(evs.NY)
    if start.hour < 5:
        start -= dt.timedelta(days=1)
    return start.date()


def weekend_html(rows, now, note, attrs=""):
    """Day groups for the baked weekend page. JS replaces this for the visitor's clock."""
    if not rows:
        return (_section_open(attrs) + "<h2>This weekend</h2>"
                "<p>No listing in the Friday-through-Sunday window is still ahead in the latest feed.</p>"
                f'<p class="small">{e(note)}</p></section>')
    groups, order = {}, []
    for ev in rows:
        day = _evening_day(evs.parse_when(ev.get("start")))
        if day not in groups:
            groups[day] = []
            order.append(day)
        groups[day].append(ev)
    parts = [_section_open(attrs), "<h2>This weekend</h2>", f'<p class="small">{e(note)}</p>']
    for day in order:
        label = f"{evs.WD_LONG[day.weekday()]} {evs.MONTHS[day.month - 1]} {day.day}"
        cards = "".join(event_card(ev) for ev in groups[day])
        parts.append(f'<h2 class="as-h3">{e(label)}</h2><div class="pcards">{cards}</div>')
    parts.append("</section>")
    return "".join(parts)


def weekend_line(now, n):
    facts = evs.weekend_facts(now)
    count = "Nothing listed" if not n else (f"{n} event" if n == 1 else f"{n} events")
    return f"Fri–Sun {facts['span']} · {count}"


def weekend_short(now, n):
    """Keep the wording in step with weekendShort() in tonight.js."""
    facts = evs.weekend_facts(now)
    when = (f"{facts['fri_long']} {facts['fri_mon']} {facts['fri_day']} through "
            f"{facts['sun_long']} {facts['sun_mon']} {facts['sun_day']}")
    if n == 1:
        mid = "The feeds list 1 event in that window that has not already ended. "
    elif n:
        mid = f"The feeds list {n} events in that window that have not already ended. "
    else:
        mid = ("No listing in the feeds starts in that window and is still ahead. "
               "Venues that list hours past midnight are below. ")
    return (f"This weekend in New York is {when}, from Friday at 5am through Monday at 5am. "
            + mid
            + "Listings come from NYC Open Data and Ticketmaster when a key is set. "
            "A missing show means the feed did not include it. Bar service still stops at 4am under state law.")


def tonight_short(now, tonight_n, more_n):
    facts = evs.night_facts(now)
    phrase = f"{facts['long']} {facts['mon']} {facts['day']}"
    if tonight_n and more_n:
        lead = (f"On {phrase}, the feeds we checked list {tonight_n} events between 5pm and 5am New York time, "
                f"and {more_n} more through the coming week. ")
    elif tonight_n:
        lead = f"On {phrase}, the feeds we checked list {tonight_n} events between 5pm and 5am New York time. "
    else:
        lead = (f"On {phrase}, no listing in the feeds starts between 5pm and 5am New York time and is still ahead. "
                "The next events are below, with the venues that list hours past midnight. ")
    return (lead + "Below that, the open-now list uses each venue's checked weekly hours. "
            "Bar service in the city still stops at 4am under state law. "
            "A missing listing means the feed did not include it, not that the night is empty.")


def route_html(heading=True):
    """Clock of the night, 5pm to the 4am close. Not a listing of shows."""
    line = """<ol class="route" data-live aria-label="Tonight from 5pm to 4am">
<li data-hour="17"><b>5</b><span>Early</span><time>5pm</time></li>
<li data-hour="20"><b>M</b><span>Music</span><time>8pm</time></li>
<li data-hour="22"><b>C</b><span>Comedy</span><time>10pm</time></li>
<li data-hour="24"><b>S</b><span>Bars</span><time>12am</time></li>
<li data-hour="26"><b>L</b><span>Late</span><time>2am</time></li>
<li data-hour="28"><b>4</b><span>Close</span><time>4am</time></li>
</ol>"""
    if not heading:
        return line
    return """<section class="route-block" id="line"><h2>The night, as a line</h2>
<p class="small">A route line, not a listing. Stops run from 5pm to the 4am close. The lit stop is the current part of the evening in New York.</p>
""" + line + "</section>"


def answer_box(text, summary="", checked=None):
    bits = []
    if summary:
        bits.append(f'data-night-summary="{e(summary)}"')
    if checked is not None:
        bits.append(f'data-checked="{int(checked)}"')
    attr = (" " + " ".join(bits)) if bits else ""
    return f'<aside class="short-answer"{attr}><p class="label">Short answer</p><p>{e(text)}</p></aside>'


def split_events(rows, now):
    """Tonight is the 5pm–5am window, minus anything that has already ended.

    The rest of the week follows. A long-running listing that started before
    tonight sorts after the events that have not started yet, so it does not
    lead "Next up".
    """
    tonight, upcoming, earlier = [], [], []
    begin, end = evs.night_window(now)
    for ev in rows or []:
        start = evs.parse_when(ev.get("start"))
        if not start or evs.has_ended(ev, now, start):
            continue
        if begin <= start < end:
            tonight.append(ev)
        elif start >= end:
            upcoming.append(ev)
        else:
            earlier.append(ev)
    tonight.sort(key=lambda r: r.get("start") or "")
    upcoming.sort(key=lambda r: r.get("start") or "")
    earlier.sort(key=lambda r: r.get("start") or "")
    return tonight, upcoming + earlier


def place_chips(venues, limit=6):
    """Neighborhoods first, then boroughs. Empty and duplicate labels are dropped."""
    hoods, boros, seen = [], [], set()
    for v in venues:
        hood = (v.get("neighborhood") or "").strip()
        boro = (v.get("borough") or "").strip()
        if hood and hood not in seen:
            seen.add(hood)
            hoods.append(hood)
        if boro and boro not in seen:
            seen.add(boro)
            boros.append(boro)
    return (hoods + boros)[:limit]


def guide_hero(title, eyebrow, updated, chips, media=""):
    """Dark route hero for a guide or plan. `media` is optional already-built picture HTML."""
    chip_html = "".join(f"<li>{e(c)}</li>" for c in chips if c)
    klass = "guide-hero has-photo" if media else "guide-hero"
    media_html = f'<div class="guide-hero-media">{media}</div>' if media else ""
    return (
        f'<header class="{klass}">'
        f'<div class="route-glow" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></div>'
        f"{media_html}"
        f'<div class="guide-hero-copy">'
        f'<p class="fresh">Updated <time datetime="{e(updated)}">{e(updated)}</time></p>'
        f'<p class="eyebrow">{e(eyebrow)}</p>'
        f"<h1>{e(title)}</h1>"
        f'<ul class="hood-chips">{chip_html}</ul>'
        f"</div></header>"
    )


def jump_nav(items):
    """In-page links. Sticky on desktop, a sideways chip row on a phone."""
    links = "".join(f'<a href="#{e(i)}">{e(n)}</a>' for i, n in items)
    return f'<nav class="jump-nav" aria-label="On this page">{links}</nav>'


def static_poster(name, href, facts, blurb, initial, external=False):
    """A poster for a place that is not one of our venue pages. Facts are copied, not invented.

    A missing href keeps the same card without a link, for a sailing described on this page.
    """
    cells = "".join(f"<div><dt>{e(label)}</dt><dd>{e(value)}</dd></div>" for label, value in facts if value)
    text = f'<span class="a">{e(blurb)}</span>' if blurb else ""
    inner = (
        f'<span class="vthumb pattern" aria-hidden="true"><span class="initial">{e(initial)}</span></span>'
        f'<span class="vtext"><span class="t">{e(name)}</span>'
        f'<dl class="poster-facts">{cells}</dl>{text}</span>'
    )
    if not href:
        return f'<article class="vcard poster-card">{inner}</article>'
    rel = ' rel="nofollow noopener"' if external else ""
    return f'<a class="vcard poster-card" href="{e(href)}"{rel}>{inner}</a>'
