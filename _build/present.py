"""HTML and schema fragments built only from checked venue facts or event rows."""
import html
import re

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
    return "<section class=\"faq\"><h2>Questions</h2>" + "".join(rows) + "</section>"


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


def event_schema(ev):
    """Event JSON-LD only when we have a real start time from the source."""
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
    }
    if ev.get("end"):
        data["endDate"] = ev["end"]
    if ev.get("url"):
        data["url"] = ev["url"]
    if ev.get("image_local"):
        data["image"] = SITE + ev["image_local"]
    org = {"nyc_parks": "NYC Parks", "nyc_permits": "NYC permitted event",
           "ticketmaster": "Ticketmaster"}.get(ev.get("source"))
    if org:
        data["organizer"] = {"@type": "Organization", "name": org}
    if ev.get("price_min") is not None and ev.get("url"):
        data["offers"] = {
            "@type": "Offer", "url": ev["url"], "price": ev["price_min"],
            "priceCurrency": "USD", "availability": "https://schema.org/InStock",
        }
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


def events_html(rows, heading, note, empty):
    if not rows:
        return f"<section class=\"whats-on\"><h2>{e(heading)}</h2><p>{e(empty)}</p><p class=\"small\">{e(note)}</p></section>"
    cards = "".join(event_card(ev) for ev in rows)
    return (f'<section class="whats-on"><h2>{e(heading)}</h2>'
            f'<p class="small">{e(note)}</p><div class="pcards">{cards}</div></section>')


def route_html():
    return """<section class="route-block"><h2>The night, as a line</h2>
<p class="small">A route line, not a listing. The lit stop is the current part of the evening in New York.</p>
<ol class="route" data-live>
<li data-hour="20"><b>M</b><span>Music</span><time>8pm</time></li>
<li data-hour="22"><b>C</b><span>Comedy</span><time>10pm</time></li>
<li data-hour="24"><b>S</b><span>Bar</span><time>12am</time></li>
<li data-hour="26"><b>R</b><span>Late</span><time>2am</time></li>
</ol></section>"""


def answer_box(text):
    return f'<aside class="short-answer"><p class="label">Short answer</p><p>{e(text)}</p></aside>'


def split_events(rows, now):
    tonight, week = [], []
    for ev in rows or []:
        start = evs.parse_when(ev.get("start"))
        if evs.in_tonight(start, now):
            tonight.append(ev)
        else:
            week.append(ev)
    tonight.sort(key=lambda r: r.get("start") or "")
    week.sort(key=lambda r: r.get("start") or "")
    return tonight, week
