"""Hand-written pages for NY Nightlife v2: home, group playbooks, trust pages."""
import datetime as dt
import html
import json
import pathlib
import re
import urllib.parse

import affiliates

e = html.escape
ROOT = pathlib.Path(__file__).resolve().parent
SITE = "https://nynightlife.com"
FEATURED = ["death-and-co", "attaboy", "nebula", "ophelia-lounge", "the-back-room", "mr-purple"]


def playbook(page, write, u, actions, fmt_date, pb, H):
    path = f"/plans/{pb['slug']}.html"
    checked = fmt_date(pb["checked"])
    ph = pb["photo"]
    mx = pb["scale_max"]
    posters = ""
    srcs = []
    for o in pb["options"]:
        left, width = o["low"] / mx * 100, (o["high"] - o["low"]) / mx * 100
        tag = f'<span class="tag">{e(o["tag"])}</span>' if o.get("tag") else ""
        chip = '<span class="chip">1 source each</span>' if o.get("status") == "likely" else ""
        posters += f"""<div class="poster {e(o['style'])}"><div class="row"><span class="name">{e(o['name'])}{tag}</span>
<span class="price">${o['low']}–{o['high']}<span class="pp"> /person</span></span></div>
<div class="pbar" role="img" aria-label="${o['low']} to ${o['high']} per person on a $0 to ${mx} scale"><i style="left:{left:.1f}%;width:{max(width, 1.5):.1f}%"></i></div>
<div class="meta">{e(o['meta'])}</div>{chip}</div>"""
        srcs += [(o["name"], s["name"], s["url"]) for s in o["sources"]]
    c = pb["combo"]
    share_text = f"{pb['title']}: {c['label'].lower()} is about ${c['low']}–{c['high']} each. {SITE}{path}"
    credit = f'<a href="{e(ph["page"])}" rel="noopener">{e(ph["credit"])}</a> · {e(ph["license"])}'
    book = ""
    if pb["slug"] == "bachelorette-night":
        book = affiliates.block(
            affiliates.BACH, "nynightlife-bach", "bach", u, "Book a cruise",
            "Viator listings, separate from the checked prices above. " + affiliates.NOTE)
        book += (f'<a class="card-link" href="{u("/plans/nyc-dinner-cruises.html")}">'
                 f'<span>NYC dinner and sunset cruises<span class="sub">Piers, timing, and New Year\'s Eve 2026</span></span>'
                 f'<span class="go">Read →</span></a>')
        book += (f'<a class="card-link" href="{u("/plans/nyc-boat-party.html")}">'
                 f'<span>NYC boat party<span class="sub">The 18+ DJ cruise and the dinner boat</span></span>'
                 f'<span class="go">Read →</span></a>')
        book += (f'<a class="card-link" href="{u("/plans/bachelor-party.html")}">'
                 f'<span>Bachelor party ideas<span class="sub">Same harbor, plus comedy rooms and clubs</span></span>'
                 f'<span class="go">Read →</span></a>')
    import present
    media = H["picture"](pb["slug"], "Lower Manhattan skyline at sunset from New York Harbor",
                         "(min-width: 1040px) 1016px, calc(100vw - 36px)", eager=True)
    chips = ["Pier 83", "Pier 36", "New York Harbor"]
    body = present.guide_hero(pb["title"], f"Group playbook · party of {pb['group']}", pb["checked"], chips, media) + f"""
<p class="credit">Photo: {credit}</p>
{present.answer_box(f"Real prices from listings we checked, split per person for a group of {pb['group']}. Pick one or stack two.")}
{present.jump_nav([("prices", "Prices"), ("worked", "How we worked it out"), ("sources", "Sources")])}
<div class="scale" aria-hidden="true"><span>Per person</span><span>$0 · ${mx // 2} · ${mx}</span></div>
<div class="posters" id="prices">{posters}</div>
<div class="total"><span>{e(c['label'])}<span class="small" style="display:block">your night, each</span></span><b>${c['low']}–{c['high']}</b></div>
{book}
<h2 id="worked">How we worked it out</h2>
<p>Cruise prices are per ticket. Bus and yacht prices are the whole booking divided by {pb['group']} people, before tip, tolls and fees unless noted. Listing prices change by date and season, so confirm the total before you pay.</p>
{'' if pb.get('group') == 6 else f'<p>These prices are for a group of {pb["group"]}. With 6 people the bus and yacht cost more per head, and the cruise price does not change.</p>'}
<h2 id="sources">Sources</h2>
<p class="small">Checked {checked}.</p>
<ol class="sources">{''.join(f'<li>{e(o)}: <a href="{e(url)}" rel="nofollow noopener">{e(n)}</a></li>' for o, n, url in srcs)}</ol>"""
    btns = (f'<a class="btn primary" href="{e(pb["primary"]["url"])}" rel="nofollow noopener">{e(pb["primary"]["label"])}</a>'
            f'<a class="btn quiet" href="sms:?&amp;body={urllib.parse.quote(share_text)}">Text the split to the group</a>')
    disclose = f'Links go to the listings we checked. Any affiliate link is labeled. Prices checked {checked}.'
    schema = {"@context": "https://schema.org", "@type": "Article", "headline": pb["title"], "dateModified": pb["checked"],
              "author": {"@type": "Person", "name": "Dan Herlehy"}, "image": ph["url"]}
    title = f"{pb['title']}: real prices per person for {pb['group']} | NY Nightlife"
    if len(title) > 60:
        title = f"{pb['title']} for {pb['group']}: prices | NY Nightlife"
    write(path, page(title,
                     f"Sunset cruise, party bus or private yacht for a group of {pb['group']} in NYC: real listing prices split per person, with sources.",
                     path, body + actions(btns, disclose), schema, "tall-bar",
                     image="/img/og/" + pb["slug"] + ".jpg",
                     img_alt=pb["title"] + ": real prices per person"))


def age_bit(v):
    a = (v.get("age") or {}).get("value") or ""
    return f" · Age: {e(a)}" if a else ""


HOME_PHOTO = {"url": "https://commons.wikimedia.org/wiki/Special:FilePath/East_Village_Sidewalk_After_Dark_(New_York,_NY)_(5720189120).jpg?width=1200",
              "page": "https://commons.wikimedia.org/wiki/File:East_Village_Sidewalk_After_Dark_(New_York,_NY)_(5720189120).jpg",
              "credit": "takomabibelot, Wikimedia Commons", "license": "CC BY 2.0"}


def home(page, write, u, vs, H):
    import events
    import present
    by = {v["slug"]: v for v in vs}
    feat = [by[s] for s in FEATURED if s in by and by[s].get("status") != "closed"]
    cards = "".join(
        H["vcard"](v, v.get("neighborhood", ""),
                   "Dress: " + e((v.get("dress") or {}).get("answer") or "not found yet") + age_bit(v))
        for v in feat)
    n = len([v for v in vs if v.get("status") != "closed"])
    credit = f'<a href="{e(HOME_PHOTO["page"])}" rel="noopener">{e(HOME_PHOTO["credit"])}</a> · {e(HOME_PHOTO["license"])}'
    import extras
    snap = events.load_snapshot()
    now = events.local_now()
    tonight, week = present.split_events(snap.get("events") or [], now)
    late_rows, posters = extras.late_posters(vs, now)
    late = len(late_rows)
    fetched_at = snap.get("fetched_at") or ""
    fetched = fetched_at[:10] or now.date().isoformat()
    active = [ev for ev in (snap.get("events") or []) if ev.get("start") and not events.has_ended(ev, now)]
    week_n = len(active)
    live = present.hero_line(now, len(tonight), week_n, late)
    hero = H["picture"]("home", "An East Village sidewalk at night",
                        "(min-width: 900px) 1100px, 100vw", eager=True)
    note = ("NYC Parks events and permitted street festivals are from NYC Open Data. "
            "Music, comedy, theatre, and nightlife are added from Ticketmaster when that key is set. "
            "Ticketmaster images sit only beside that event, and the link is the event page. "
            f"Feed checked {fetched}.")
    short = present.home_short(now, n, len(tonight), late)
    attrs = present.night_attrs("home")
    shown = (tonight + week)[:6]
    if tonight:
        events_block = present.events_html(shown, "What's on in NYC tonight / this week", note,
                                           "No evening parks, festival, or ticketed listings are in the latest feed.", attrs)
    else:
        events_block = present.empty_night(week[:6], posters, note, attrs)
    body = f"""<section class="hero route-hero">{hero}<div class="hero-copy"><p class="eyebrow"><span class="line-mark" aria-hidden="true">N</span>New York City</p><h1>Tonight in New York</h1>
<p class="hero-live" data-night-line>{e(live)}</p>
<div class="inline-actions"><a class="btn primary" href="{u('/tonight/')}">What's on tonight</a><a class="btn ghost" href="{u('/this-weekend/')}">This weekend</a><a class="btn ghost" href="{u('/plans/')}">Plan a group night</a></div>
{present.route_html(heading=False)}
</div></section>
<p class="credit">Photo: {credit}</p>
{present.answer_box(short, "home", n)}
{events_block}
<h2>Beyond the bar</h2>
<p class="lede">Cruises, a boat party, a bachelor night, comedy rooms, and the door facts. Each page only states what we could verify.</p>
<a class="card-link" href="{u('/plans/nyc-dinner-cruises.html')}"><span>Dinner and sunset cruises<span class="sub">Piers and timing we could verify</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/plans/nyc-boat-party.html')}"><span>NYC boat party<span class="sub">DJ cruise, sunset sail, and the dinner boat</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/plans/bachelor-party.html')}"><span>Bachelor party ideas<span class="sub">A boat, a comedy room, or a checked club</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/guides/nyc-comedy-clubs.html')}"><span>NYC comedy clubs<span class="sub">Rooms we could verify, plus comedy in the feed</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/guides/nyc-dress-codes.html')}"><span>Dress codes<span class="sub">What {n} venues say, or that they say nothing</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/guides/nyc-bar-closing-time.html')}"><span>The 4am rule<span class="sub">When service stops, and who lists later hours</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/this-weekend/')}"><span>This weekend<span class="sub">Friday through Sunday, from the same feeds</span></span><span class="go">See the weekend →</span></a>
<a class="card-link" href="{u('/guides/nyc-speakeasies.html')}"><span>NYC speakeasies<span class="sub">Hidden doors we could check, and the walk-in rooms beside them</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/guides/nyc-rooftop-bars.html')}"><span>NYC rooftop bars<span class="sub">Hours and dress from the rooftops we have checked</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/guides/nyc-new-years-eve.html')}"><span>New Year's Eve 2026<span class="sub">Ball drop and cruises, only what the official pages say</span></span><span class="go">Read →</span></a>
<h2>Group nights</h2>
<a class="card-link" href="{u('/plans/')}"><span>Group nights<span class="sub">Bachelorette prices and the cruise guide</span></span><span class="go">Open →</span></a>
<a class="card-link" href="{u('/plans/bachelorette-night.html')}"><span>Bachelorette Night for 10<span class="sub">Cruise, party bus or yacht, priced per person</span></span><span class="go">See prices →</span></a>
{H['home_box']()}
<script defer src="{H['tonight_js']}"></script>
<h2>Most asked about</h2>
<div class="vlist two posters">{cards}</div>
{affiliates.block(affiliates.HOME, "nynightlife-home", "home", u, "Book a night out")}
<h2>Why trust this</h2>
<div class="card"><ul class="clean">
<li>Each fact is checked against the venue's own site or two independent sources.</li>
<li>If we can't confirm something, we say so, with an "unconfirmed" label.</li>
<li>Every page shows the date it was checked. We never pretend it's fresher.</li></ul>
<p><a href="{u('/how-we-check.html')}">How we check →</a></p></div>"""
    schema = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": "NY Nightlife", "url": SITE + "/",
         "dateModified": fetched},
        present.item_list("What's on", [(ev["title"], "/tonight/") for ev in shown]),
    ]
    schema += [s for s in (present.event_schema(ev) for ev in shown) if s]
    write("/index.html", page("Tonight in NYC: bars, events, door facts | NY Nightlife",
                              "What's on in NYC tonight and this week, plus dress code, age, and cover for checked bars and clubs.",
                              "/", body, schema, "no-bar", image="/img/og/site.jpg",
                              img_alt="Tonight in New York",
                              updated=events.refresh_stamp(fetched_at) or fetched,
                              updated_iso=fetched_at or fetched))


def simple(page, write, path, title, desc, h1, html_body):
    body = f'<p class="eyebrow" style="margin-top:20px">NY Nightlife</p><h1>{e(h1)}</h1>{html_body}'
    write(path, page(title, desc, path, body, None, "no-bar"))


def trust_pages(page, write, u):
    simple(page, write, "/about.html", "About NY Nightlife", "Who runs NY Nightlife and how it works.", "About",
           f"""<p class="lede">NY Nightlife is a small, independent guide to getting into New York bars and clubs: what to wear, how old you need to be, whether there's a cover, and how the door works.</p>
<p>It's run by Dan Herlehy. Research and drafting are done with AI tools; every fact is tied to a source you can click, and Dan reviews changes before they go live. Pages that haven't had that review yet say "editor review pending".</p>
<p>We don't take payment for coverage. Some links may earn us a commission; those are labeled. See <a href="{u('/affiliate-disclosure.html')}">affiliate disclosure</a> and <a href="{u('/how-we-check.html')}">how we check</a>.</p>
<p>Spot something wrong? <a href="mailto:hello@nynightlife.com">hello@nynightlife.com</a>.</p>""")
    simple(page, write, "/how-we-check.html", "How we check facts | NY Nightlife", "Our method for checking NYC bar and club door facts.", "How we check",
           """<p class="lede">The short version: we'd rather say "not found" than guess.</p>
<h2>What counts as checked</h2>
<ul class="clean"><li><b>Confirmed</b>: stated by the venue itself, or two independent sources agree.</li>
<li><b>1 source</b>: one decent source says so. Treat it as likely.</li>
<li><b>Unconfirmed</b>: sources disagree or are weak.</li>
<li><b>Not found yet</b>: we couldn't find it. We leave it blank instead of inventing it.</li></ul>
<h2>Dates</h2><p>Every page shows when it was checked. The date changes only when we re-check, never automatically.</p>
<h2>Who reviews</h2><p>AI tools help gather and draft facts. "Reviewed by Dan" appears only on pages Dan has approved; others say "editor review pending".</p>
<h2>Door reports</h2><p>If you went and something was different, email us. We never hide negative reports, only spam.</p>
<h2>Prices</h2><p>Prices come from the listing or venue on the date shown, include fees where the seller shows them, and change often. Confirm before you pay.</p>""")
    simple(page, write, "/affiliate-disclosure.html", "Affiliate disclosure | NY Nightlife", "How NY Nightlife may earn money.", "Affiliate disclosure",
           """<p class="lede">Some links on NY Nightlife may be affiliate links. If you book through one, we may earn a commission at no extra cost to you.</p>
<p>Booking links to Viator are affiliate links (partner ID P00330813). They are marked sponsored. You pay the price Viator shows; we don't add a fee.</p>
<p>Affiliate links are labeled where they appear. Commissions never decide what a page says: dress codes, ages and prices are reported as the sources show them, including when that's bad news for a venue.</p>
<p>We don't accept payment for reviews or rankings. If we ever sell a sponsored placement, it will be labeled "Sponsored".</p>""")
    simple(page, write, "/privacy.html", "Privacy | NY Nightlife", "What NY Nightlife collects.", "Privacy",
           """<p class="lede">We keep this simple.</p>
<ul class="clean"><li>We count page visits and link clicks with privacy-friendly analytics that don't set cookies or identify you.</li>
<li>We don't run ad trackers.</li>
<li>Nyla, our chat helper, runs in your browser. What you type isn't sent or saved anywhere. If you ask her out loud, your browser's own speech service (Google in Chrome, Apple in Safari) turns your voice into text; we never receive or keep your audio. Her spoken answers are short recordings made ahead of time and loaded from this site like a picture, so playing one tells our host no more than opening a page does. She only remembers when she last said hello and whether her voice is on.</li>
<li>Our fonts are served from this site, so loading a page no longer sends your IP address to Google.</li>
<li>Our analytics provider, PostHog, does receive page views and clicks from US servers. It sets no cookies, doesn't identify you, and honours Do Not Track. Add <code>?notrack=1</code> to any URL to opt out.</li>
<li>The Tonight page and the home page's tonight box load their data from this site and from GitHub (raw.githubusercontent.com), where our scheduled job saves it. GitHub sees your IP address like any web host. The job fetches the forecast (National Weather Service), headlines and liquor-license data itself, so your browser never contacts those services.</li>
<li>The weekly email, once it starts, will be sent with Kit (kit.com). If you sign up, Kit stores your email address to send it; you confirm by email first, every email has an unsubscribe link, and we delete your address on request.</li>
<li>If you click through to a booking site, that site has its own privacy policy and may set its own cookies.</li>
<li>When the build has a Ticketmaster key, concert, comedy, theatre, and nightlife listings on the homepage and Tonight page come from the Ticketmaster Discovery API. They are refreshed about daily and past events are dropped. Ticket links go to that event's page. Event images are loaded from Ticketmaster beside that listing and are not kept as a photo library. Continuing to Ticketmaster is covered by Ticketmaster's own privacy policy.</li>
<li>If you email us, we use your email only to reply.</li></ul>
<p>Questions: <a href="mailto:privacy@nynightlife.com">privacy@nynightlife.com</a>.</p>""")
    simple(page, write, "/contact.html", "Contact | NY Nightlife", "Contact NY Nightlife.", "Contact",
           """<p class="lede">Corrections, door reports and everything else: <a href="mailto:hello@nynightlife.com">hello@nynightlife.com</a>.</p>
<p>Venues: if something on your page is wrong, tell us with a link to where it's stated and we'll fix it.</p>""")
    miss = f"""<header class="guide-hero">
<div class="route-glow" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></div>
<div class="guide-hero-copy">
<p class="eyebrow">404 · off the route</p>
<h1>Not on this line.</h1>
<p class="lede">That page moved or never existed.</p>
</div></header>
<nav class="jump-nav miss-links" aria-label="Keep going">
<a href="{u('/tonight/')}">Tonight</a>
<a href="{u('/this-weekend/')}">This weekend</a>
<a href="{u('/guides/nyc-speakeasies.html')}">Speakeasies</a>
<a href="{u('/guides/nyc-rooftop-bars.html')}">Rooftop bars</a>
<a href="{u('/guides/nyc-new-years-eve.html')}">New Year's Eve</a>
<a href="{u('/guides/nyc-dress-codes.html')}">Dress codes</a>
</nav>"""
    write("/404.html", page("Page not found | NY Nightlife", "This page doesn't exist.", "/404.html",
                            miss, None, "no-bar signal-404", "noindex"))


HARBOR_PHOTO = {
    "url": "https://commons.wikimedia.org/wiki/Special:FilePath/Sunset_over_the_Lower_Manhattan_skyline_as_seen_from_New_York_Harbor_-_20200904.jpg?width=1200",
    "page": "https://commons.wikimedia.org/wiki/File:Sunset_over_the_Lower_Manhattan_skyline_as_seen_from_New_York_Harbor_-_20200904.jpg",
    "credit": "Andre Carrotflower, Wikimedia Commons",
    "license": "CC BY-SA 4.0",
}


def cruise_guide(page, write, u, actions, fmt_date, H):
    """Dinner, sunset, jazz/brunch, and NYE cruises. Facts only from pages we opened
    or from the Oct 18 bachelorette check. No prices beyond that check."""
    path = "/plans/nyc-dinner-cruises.html"
    checked = "2026-11-11"
    ph = HARBOR_PHOTO
    credit = f'<a href="{e(ph["page"])}" rel="noopener">{e(ph["credit"])}</a> · {e(ph["license"])}'
    book = affiliates.block(
        affiliates.CRUISES, "nynightlife-nyc-dinner-cruises", "nyc-dinner-cruises", u,
        "Book a cruise",
        "Viator listings, separate from the facts above. " + affiliates.NOTE,
        heading_id="book")
    import present
    media = H["picture"]("bachelorette-night", "Lower Manhattan skyline at sunset from New York Harbor",
                         "(min-width: 1040px) 1016px, calc(100vw - 36px)", eager=True)
    sailings = (
        present.static_poster(
            "Harbor Lights", "",
            [("Place", "Pier 83, Midtown"), ("Hours", "2 hours, 7pm most of the year"), ("Vibe", "Sightseeing, full bar")],
            "2 hours from Pier 83, Midtown (83 North River Piers, New York, NY 10036). Live narration, a full bar, and concessions. It leaves at 7pm for most of the year and at 6pm from January through March.",
            "H", photo="circle-line-pier-83")
        +         present.static_poster(
            "Statue at Sunset", "",
            [("Place", "Pier 16, South Street Seaport"), ("Hours", "About 90 minutes"), ("Vibe", "Music and drinks")],
            "About 90 minutes from Pier 16 at the South Street Seaport (89 South Street, New York, NY 10038). Music and drinks, no narration. Departure time moves with sunset.",
            "S", photo="pier-16-seaport")
        +         present.static_poster(
            "Sip 'N Groove", "",
            [("Place", "Pier 83"), ("Hours", "2 hours"), ("Vibe", "18+ DJ cruise")],
            "2 hours from Pier 83, with a live DJ and a full bar. 18+.",
            "G", photo="circle-line-pier-83")
    )
    body = present.guide_hero("NYC Dinner & Sunset Cruises", "Guide · New York Harbor", checked,
                              ["Pier 83", "Pier 16", "Pier 61", "Midtown"], media) + f"""
<p class="credit">Photo: {credit}</p>
{present.answer_box("Where sunset, dinner, jazz, brunch, and New Year's Eve cruises leave from, and how long the sailings we could verify actually run. If a fact is missing, we did not confirm it.")}
{present.jump_nav([("sunset", "Sunset"), ("dinner", "Dinner"), ("jazz", "Jazz and brunch"), ("nye", "New Year's Eve"), ("book", "Book"), ("sources", "Sources")])}
<h2 id="sunset">Sunset cruises</h2>
<p>Circle Line publishes three evening cruises. Checked on the operator's pages, Nov 11, 2026.</p>
<div class="vlist two posters">{sailings}</div>
<p>Circle Line says Harbor Lights and Statue at Sunset can work for families comfortable with an evening departure. Sip 'N Groove is 18 and older. Those three pages do not publish a dress code. Harbor Lights has open-air decks, so bring a layer for that sailing.</p>
<p>On Oct 18, 2026 we checked two public sunset and harbor tickets, Circle Line Harbor Lights and the Grande Mariner DJ sunset cruise from Pier 36 (21+), at about $48–$55 a person. That number is from those listings on that date. It is not a dinner-cruise price. The same check is on <a href="{u('/plans/bachelorette-night.html')}">Bachelorette Night for 10</a>. The party cruise and the dinner boat are on <a href="{u('/plans/nyc-boat-party.html')}">NYC boat party</a>.</p>
<h2 id="dinner">Dinner cruises</h2>
<p>A dinner cruise is a different ticket from a sightseeing cruise that happens to sell drinks. NYC Tourism lists City Cruises Signature Dining at Pier 61, Chelsea Piers, West 23rd Street and 12th Avenue, and marks that listing wheelchair accessible. The tourism page does not say how long the cruise runs or what to wear.</p>
<p>Other dinner boats leave from other piers and set their own dress codes. Read the listing for the boat you book. We are not publishing a dinner-cruise price.</p>
<h2 id="jazz">Jazz and brunch cruises</h2>
<p>Jazz cruises and brunch cruises are separate listings. Pier, length, what is included, and dress code change by boat. We have not confirmed one jazz or brunch sailing's details on this page.</p>
<h2 id="nye">New Year's Eve 2026</h2>
<p>New Year's Eve 2026 is Thursday, December 31. A sunset or dinner cruise on another night is not a New Year's Eve ticket. Boats that night are sold as their own sailings.</p>
<p>The pier, the hours, the dress code, and the price belong to that sailing's listing. We have not checked one NYE boat's price for this page. Book the NYE listing and read it, including whether fireworks are included or only a view when conditions allow.</p>
<p>Alcohol is 21+ in New York on every boat. <a href="{u('/guides/under-21-nyc-bars-clubs.html')}">Under 21 in NYC</a> explains the rule. Boarding age is separate and is printed on the ticket.</p>
{book}
<h2 id="sources">Sources</h2>
<p class="small">Circle Line and NYC Tourism checked {fmt_date(checked)}. The $48–$55 tickets were checked Oct 18, 2026.</p>
<ol class="sources">
<li>Circle Line Harbor Lights: <a href="https://www.circleline.com/sightseeing-cruises/harbor-lights" rel="nofollow noopener">Harbor Lights cruise</a></li>
<li>Circle Line evening cruises: <a href="https://www.circleline.com/about/nyc-cruise-guide/NYC-Sunset-and-Night-Cruises-Compared" rel="nofollow noopener">Sunset and night cruises compared</a></li>
<li>City Cruises Signature Dining: <a href="https://www.nyctourism.com/restaurants/city-cruises-signature-dining/" rel="nofollow noopener">NYC Tourism listing, Pier 61</a></li>
<li>Public sunset or harbor ticket, Oct 18, 2026: <a href="https://www.tripster.com/detail/circle-line-harbor-lights-sightseeing-cruise-new-york" rel="nofollow noopener">Tripster: Circle Line Harbor Lights</a></li>
<li>Public sunset or harbor ticket, Oct 18, 2026: <a href="https://www.travelocity.com/things-to-do/circle-line-new-york-harbor-lights-evening-cruise.a255366.activity-details" rel="nofollow noopener">Travelocity: Circle Line Harbor Lights</a></li>
<li>Public sunset or harbor ticket, Oct 18, 2026: <a href="https://boomertravel.tripster.com/detail/nyc-sunset-cruise-grande-mariner.md" rel="nofollow noopener">Tripster: Grande Mariner sunset cruise</a></li>
</ol>"""
    btns = (f'<a class="btn primary" href="#book">See cruise listings</a>'
            f'<a class="btn quiet" href="{u("/plans/bachelorette-night.html")}">Bachelorette prices</a>')
    disclose = f"Affiliate links are labeled. Listing prices change. Facts checked {fmt_date(checked)}."
    schema = {"@context": "https://schema.org", "@type": "Article",
              "headline": "NYC Dinner & Sunset Cruises", "dateModified": checked,
              "author": {"@type": "Person", "name": "Dan Herlehy"}, "image": ph["url"]}
    write(path, page("NYC Dinner & Sunset Cruises | NY Nightlife",
                     "Sunset, dinner, and New Year's Eve cruises in NYC: piers and timing we could verify, plus Viator listings. Checked Nov 11, 2026.",
                     path, body + actions(btns, disclose), schema, "tall-bar",
                     image="/img/og/nyc-dinner-cruises.jpg",
                     img_alt="NYC Dinner & Sunset Cruises"))
    return path, checked


def plans_hub(page, write, u):
    import present
    body = present.guide_hero(
        "Plan a group night", "Group nights", "2026-11-16",
        ["Harbor", "Comedy", "Clubs"]) + present.answer_box(
        "Checked pages for a group of 10, a harbor cruise, a boat party, and a bachelor night. Each one only states what we could verify.") + present.jump_nav([
            ("weekend", "This weekend"), ("bach", "Bachelorette"), ("cruises", "Cruises"),
            ("boat", "Boat party"), ("bachelor", "Bachelor party"), ("comedy", "Comedy")]) + """
<a class="card-link" id="weekend" href="/this-weekend/"><span>This weekend<span class="sub">Friday through Sunday from the same event feeds as Tonight.</span></span><span class="go">See the weekend →</span></a>
<a class="card-link" id="bach" href="/plans/bachelorette-night.html"><span>Bachelorette Night for 10<span class="sub">Cruise, party bus, or yacht, priced per person. Checked Oct 18, 2026.</span></span><span class="go">See prices →</span></a>
<a class="card-link" id="cruises" href="/plans/nyc-dinner-cruises.html"><span>NYC dinner and sunset cruises<span class="sub">Piers, timing, and what we did not confirm. Checked Nov 11, 2026.</span></span><span class="go">Read →</span></a>
<a class="card-link" id="boat" href="/plans/nyc-boat-party.html"><span>NYC boat party<span class="sub">DJ cruise, sunset sail, and the dinner boat. Checked Nov 16, 2026.</span></span><span class="go">Read →</span></a>
<a class="card-link" id="bachelor" href="/plans/bachelor-party.html"><span>Bachelor party ideas<span class="sub">A boat, a comedy room, or a checked club. Checked Nov 16, 2026.</span></span><span class="go">Read →</span></a>
<a class="card-link" id="comedy" href="/guides/nyc-comedy-clubs.html"><span>NYC comedy clubs<span class="sub">Rooms the clubs publish, plus comedy in the feed.</span></span><span class="go">Read →</span></a>
"""
    write("/plans/index.html", page("Group nights in NYC | NY Nightlife",
                                    "Bachelorette prices, NYC boat party, bachelor party ideas, and a checked guide to dinner and sunset cruises.",
                                    "/plans/", body, None, "no-bar", updated="2026-11-16"))


def image_credits(page, write):
    import json
    import pathlib
    rows = []
    root = pathlib.Path(__file__).resolve().parent
    for f in sorted((root / "data" / "venues").glob("*.json")):
        v = json.loads(f.read_text(encoding="utf-8"))
        ph = v.get("photo") or {}
        if not ph.get("credit"):
            continue
        rows.append((v["name"], ph.get("credit", ""), ph.get("license", ""), ph.get("license_url", ""), ph.get("page") or ph.get("url", ""), ph.get("depicts", "")))
    places = root / "data" / "place_photos.json"
    if places.exists():
        for ph in json.loads(places.read_text(encoding="utf-8"))["places"].values():
            rows.append((ph["name"], ph.get("credit", ""), ph.get("license", ""), ph.get("license_url", ""), ph.get("page") or ph.get("url", ""), ph.get("depicts", "")))
    rows.append(("Homepage hero", HOME_PHOTO["credit"], HOME_PHOTO["license"], "https://creativecommons.org/licenses/by/2.0/", HOME_PHOTO["page"], "East Village sidewalk at night"))
    rows.append(("Harbor photograph", HARBOR_PHOTO["credit"], HARBOR_PHOTO["license"], "https://creativecommons.org/licenses/by-sa/4.0/", HARBOR_PHOTO["page"], "Lower Manhattan skyline from the harbor"))
    items = ""
    for name, credit, lic, lurl, src, depicts in rows:
        bit = f"<li><b>{e(name)}</b>: {e(credit)}"
        if lic:
            bit += f' · <a href="{e(lurl)}" rel="license noopener">{e(lic)}</a>' if lurl else f" · {e(lic)}"
        if src:
            bit += f' · <a href="{e(src)}" rel="noopener">source page</a>'
        if depicts:
            bit += f" · {e(depicts)}"
        items += bit + "</li>"
    body = f"""<p class="eyebrow">Credits</p><h1>Image credits</h1>
<p class="lede">Photographs on this site are ones we have a license to store, from Wikimedia Commons and Flickr under the Creative Commons licenses linked below. Each one is credited to its author, resized and cropped by us. Where a photo shows the building or the street outside rather than the room, the note says so. Ticketmaster event images, when a listing has one, are loaded from Ticketmaster next to that event and are not saved here.</p>
<ul class="clean">{items}</ul>"""
    write("/image-credits.html", page("Image credits | NY Nightlife",
                                     "Photograph credits and licenses for images stored on NY Nightlife.",
                                     "/image-credits.html", body, None, "no-bar", updated="2026-11-21"))


MONEY_CHECKED = "2026-11-16"


def _money_page(page, write, path, title, desc, body, faqs, image_alt, checked=None):
    import present
    checked = checked or MONEY_CHECKED
    schema = [
        {"@context": "https://schema.org", "@type": "Article", "headline": title.split("|")[0].strip(),
         "dateModified": checked, "author": {"@type": "Person", "name": "Dan Herlehy"}},
        present.faq_schema(faqs),
    ]
    if len(title) > 60:
        raise SystemExit(f"title over 60 characters ({len(title)}): {title}")
    write(path, page(title, desc, path, body, schema, "tall-bar", img_alt=image_alt, updated=checked))


def comedy_events(rows, now, parse_when):
    """Showtime rows that are comedy and have not already ended. Listings with no
    real start (Viator products) stay out. `now` is timezone-aware."""
    kept = []
    cutoff = now - dt.timedelta(hours=6)
    for ev in rows or []:
        if ev.get("listing") or not ev.get("start"):
            continue
        cat = (ev.get("category") or "").lower()
        blob = f"{ev.get('title') or ''} {ev.get('venue_name') or ''}".lower()
        if cat != "comedy" and not re.search(r"\bcomedy\b", blob):
            continue
        start = parse_when(ev.get("start"))
        if not start or start < cutoff:
            continue
        kept.append(ev)
    kept.sort(key=lambda r: r.get("start") or "")
    return kept[:8]


def _comedy_feed():
    import events
    snap = events.load_snapshot()
    rows = comedy_events(snap.get("events") or [], events.local_now(), events.parse_when)
    return rows, (snap.get("fetched_at") or "")[:10] or "unknown"


def boat_party(page, write, u, actions, H, vs):
    """Boat party and sunset cruise. Facts opened on the operators' sites on MONEY_CHECKED."""
    import present
    path = "/plans/nyc-boat-party.html"
    book = affiliates.block(
        ("sunset-cruise", "dinner-cruise", "jazz-brunch"),
        "nynightlife-nyc-boat-party", "nyc-boat-party", u, "Book a boat",
        "Viator listings, separate from the facts above. " + affiliates.NOTE,
        heading_id="book")
    faqs = [
        ("What counts as an NYC boat party?",
         "Circle Line describes Sip 'N Groove as an 18+ live-DJ party cruise from Pier 83, built for groups, birthdays, and a night out. Harbor Lights and Statue at Sunset are sightseeing cruises. City Cruises' Signature Dinner Cruise is a 2.5-hour dinner with a live DJ from Pier 61."),
        ("Where do the sunset cruises leave from?",
         "Circle Line's Harbor Lights leaves from Pier 83, 83 North River Piers, New York, NY 10036. Statue at Sunset leaves from Pier 16, 89 South Street, New York, NY 10038. City Cruises' Signature Dinner Cruise boards at Pier 61, Chelsea Piers, West 23rd Street and 12th Avenue."),
        ("What time is sunset on the boat?",
         "Circle Line's schedule lists Harbor Lights at 7pm in off-peak, shoulder, and peak seasons, and at 5pm in the winter season it dates January 5 to March 5. Its comparison page instead says 6pm from January through March. Statue at Sunset is the sailing timed near sunset, and that departure moves with the season. Check the operator's calendar for the date you want."),
        ("Can a group book together?",
         "Circle Line's Harbor Lights page says groups of 15 or more can ask for special pricing, and that drinks and catered food can be added. It does not publish the group rate. City Cruises says the dinner cruise holds a table for the party size and that children are welcome, with infants under three cruising free."),
    ]
    by = {v["slug"]: v for v in vs}
    land = "".join(H["poster"](by[slug], "") for slug in ("marquee-new-york", "le-bain", "the-dead-rabbit") if slug in by)
    body = present.guide_hero("NYC boat party", "Guide · New York Harbor", MONEY_CHECKED,
                              ["Pier 83", "Pier 16", "Pier 61", "Midtown"]) + f"""
{present.answer_box("For an NYC boat party, Circle Line's Sip 'N Groove is the 18+ DJ cruise from Pier 83. Harbor Lights (Pier 83, 2 hours) and Statue at Sunset (Pier 16, about 90 minutes) are sightseeing cruises. City Cruises' Signature Dinner Cruise is 2.5 hours from Pier 61 with a dinner buffet, a live DJ, and a casual dress code. We are not publishing a ticket price. Checked " + MONEY_CHECKED + ".")}
{present.jump_nav([("party", "The party cruise"), ("sunset", "Sunset"), ("dinner", "Dinner"), ("land", "On land"), ("book", "Book"), ("questions", "Questions"), ("sources", "Sources")])}
<p class="lede">A ticketed night on the harbor, not a private yacht quote. These are the sailings the operators describe, checked {MONEY_CHECKED}.</p>
<h2 id="party">The party cruise</h2>
<p>Circle Line's own comparison of its evening cruises calls Sip 'N Groove a two-hour 18+ party cruise from Pier 83 with a live DJ and a full bar. The same page says it fits birthdays, bachelorette weekends, and groups of friends. It does not list a clock time or a dress code. Alcohol service is still 21+ in New York. <a href="{u('/guides/under-21-nyc-bars-clubs.html')}">Under 21 in NYC</a> cites the statute. Boarding age is the 18+ rule printed for this sailing.</p>
<h2 id="sunset">Sunset and night sightseeing</h2>
<p>Harbor Lights is a two-hour narrated cruise from Pier 83 with open-air decks, a full bar, and concessions. Circle Line's Harbor Lights page says groups of 15 or more can get special pricing, and that cocktails, beer, wine, soft drinks, and catered food can be added. It does not print that price.</p>
<p>On the schedule page, Harbor Lights is 7pm in the off-peak, shoulder, and peak seasons, and 5pm in the winter season dated January 5 to March 5. The evening-cruise comparison instead says 7pm most of the year and 6pm from January through March. Both pages say the calendar is what to book against, and the schedule page says times can change and that holiday sailings replace the regular cruise.</p>
<p>Statue at Sunset is about 90 minutes from Pier 16 at the South Street Seaport, with music and drinks and no narration. Its departure is the one Circle Line moves to stay near sunset. The schedule lists it as limited in winter, about 4:00–5:30pm off-peak, about 6:00–7:00pm in the shoulder, and about 7:30pm at peak.</p>
<p>The same comparison says Harbor Lights and Statue at Sunset can work for families who are fine with an evening departure. Sip 'N Groove is 18 and older. None of those three write a dress code.</p>
<p>A Holiday Harbor Lights cruise is listed on the Harbor Lights page for November 27, 2026 through January 3, 2027. That is a separate sailing from the regular Harbor Lights cruise.</p>
<p>Public sunset tickets we priced on October 18, 2026, and the piers we had already written up, are on <a href="{u('/plans/nyc-dinner-cruises.html')}">NYC dinner and sunset cruises</a> and <a href="{u('/plans/bachelorette-night.html')}">Bachelorette Night for 10</a>. A bachelor group using the same boats is on <a href="{u('/plans/bachelor-party.html')}">bachelor party ideas</a>.</p>
<h2 id="dinner">Dinner cruise</h2>
<p>City Cruises' Signature Dinner Cruise page says the sailing is 2.5 hours from Pier 61, Chelsea Piers, West 23rd Street and 12th Avenue, New York, NY. Boarding is 30 minutes before the start. The page lists a dinner buffet, a live DJ, alcoholic drinks for sale, a casual dress code, a table for the party, and an open-air rooftop lounge. Children are welcome and infants under three cruise free. The page shows a starting price that changes with the date, so this guide does not print a number.</p>
<h2 id="land">If the night continues on land</h2>
<p>Door facts for clubs and bars we have checked, including dress and cover, are on the venue pages. Nothing here claims they are next to a pier.</p>
<div class="vlist two posters">{land}</div>
<p><a href="{u('/guides/nyc-dress-codes.html')}">Dress codes</a> for the venues on this site</p>
{book}
{present.faq_html(faqs)}
<h2 id="sources">Sources</h2>
<p class="small">Checked {MONEY_CHECKED}.</p>
<ol class="sources">
<li>Circle Line Harbor Lights: <a href="https://www.circleline.com/sightseeing-cruises/harbor-lights" rel="nofollow noopener">Harbor Lights cruise</a></li>
<li>Circle Line evening cruises: <a href="https://www.circleline.com/about/nyc-cruise-guide/NYC-Sunset-and-Night-Cruises-Compared" rel="nofollow noopener">Sunset and night cruises compared</a></li>
<li>Circle Line schedule: <a href="https://www.circleline.com/schedule" rel="nofollow noopener">2026 cruise schedule</a></li>
<li>City Cruises Signature Dinner Cruise: <a href="https://citycruises.com/tickets/new-york-city/new-york-signature-dinner-cruise" rel="nofollow noopener">Signature Dinner Cruise</a></li>
</ol>"""
    btns = (f'<a class="btn primary" href="#book">See boat listings</a>'
            f'<a class="btn quiet" href="{u("/plans/nyc-dinner-cruises.html")}">Cruise guide</a>')
    disclose = f"Affiliate links are labeled. Listing prices change. Facts checked {MONEY_CHECKED}."
    _money_page(page, write, path,
                "NYC boat party and sunset cruise | NY Nightlife",
                "NYC boat party and sunset cruise: Circle Line's DJ cruise, Harbor Lights, Statue at Sunset, and City Cruises' dinner boat. Checked 2026-11-16.",
                body + actions(btns, disclose), faqs,
                "NYC boat party and sunset cruise")
    return path, MONEY_CHECKED


def bachelor_party(page, write, u, actions, H, vs):
    """Bachelor party ideas limited to operator facts and pages already on this site."""
    import present
    path = "/plans/bachelor-party.html"
    book = affiliates.block(
        ("bar-crawls", "comedy", "sunset-cruise", "night-tours"),
        "nynightlife-bachelor-party", "bachelor-party", u, "Book a piece of the night",
        "Viator listings, separate from the checked pages above. " + affiliates.NOTE,
        heading_id="book")
    faqs = [
        ("What are NYC bachelor party ideas you actually checked?",
         "A harbor boat, a comedy club, or a nightclub that already has a fact page here. Circle Line's Sip 'N Groove is an 18+ DJ cruise. Comedy Cellar, Gotham Comedy Club, The Stand, and New York Comedy Club publish their rooms on their own sites. This page does not sell a package or a price."),
        ("Is a boat a good bachelor plan?",
         "Sip 'N Groove is the Circle Line sailing written for groups and birthdays. It is 18+, two hours, from Pier 83, with a live DJ and a full bar. The dinner cruise from Pier 61 is a separate ticket with a casual dress code. Details and sources are on the boat party page."),
        ("Where do the per-person prices live?",
         "The only per-person split on this site is Bachelorette Night for a group of 10, checked October 18, 2026. With 6 people the bus and yacht on that page cost more per head. This bachelor page does not repeat those listing prices."),
        ("What should the group wear?",
         "City Cruises prints a casual dress code for its Signature Dinner Cruise. Circle Line's evening pages we checked do not print one. Clubs are different: use the dress-code table and the venue page before you go."),
    ]
    by = {v["slug"]: v for v in vs}
    clubs = "".join(H["poster"](by[slug], "") for slug in ("marquee-new-york", "house-of-yes", "nebula") if slug in by)
    body = present.guide_hero("NYC bachelor party", "Guide · group night", MONEY_CHECKED,
                              ["Pier 83", "Chelsea", "Bushwick", "Comedy"]) + f"""
{present.answer_box("NYC bachelor party ideas on this site are a boat, a comedy room, or a club we have already checked. Circle Line's Sip 'N Groove is an 18+ DJ cruise from Pier 83. Comedy Cellar, Gotham, The Stand, and New York Comedy Club publish their own addresses. Covers and dress codes for clubs stay on the venue pages. Checked " + MONEY_CHECKED + ".")}
{present.jump_nav([("water", "On the water"), ("comedy", "Comedy"), ("clubs", "Clubs"), ("prices", "Prices"), ("book", "Book"), ("questions", "Questions"), ("sources", "Sources")])}
<p class="lede">Three kinds of plan we could verify. No package price, and no ranking.</p>
<h2 id="water">Start on the water</h2>
<p>The boat we can describe from the operator is on <a href="{u('/plans/nyc-boat-party.html')}">NYC boat party</a>. Short version: Sip 'N Groove is Circle Line's 18+ DJ cruise from Pier 83, and City Cruises runs a 2.5-hour dinner with a DJ from Pier 61. <a href="{u('/plans/nyc-dinner-cruises.html')}">Dinner and sunset cruises</a> has the sightseeing piers.</p>
<h2 id="comedy">Comedy</h2>
<p>A show is a simpler group plan than a club door. Addresses, Comedy Cellar's published prices, and any comedy row in the events feed are on <a href="{u('/guides/nyc-comedy-clubs.html')}">NYC comedy clubs</a>.</p>
<h2 id="clubs">Clubs we have already checked</h2>
<p>These are not a ranking. Each page has the cover, dress code, age, and hours we could source, plus the date that page was checked. Read the page before you promise the group a yes at the door. Marquee New York is in Chelsea. House of Yes is in Bushwick.</p>
<div class="vlist two posters">{clubs}</div>
<p><a href="{u('/guides/nyc-dress-codes.html')}">Dress codes</a> and <a href="{u('/guides/nyc-bar-closing-time.html')}">when service stops</a></p>
<h2 id="prices">A priced split, if you want numbers</h2>
<p>We have not built a bachelor price sheet. <a href="{u('/plans/bachelorette-night.html')}">Bachelorette Night for 10</a> splits a cruise, a party bus, and a small yacht per person from listings checked October 18, 2026. Those listings are not bachelor-only. With 6 people the bus and yacht on that page cost more per head, and a per-ticket cruise does not.</p>
{book}
{present.faq_html(faqs)}
<h2 id="sources">Sources</h2>
<p class="small">Checked {MONEY_CHECKED}. Club door facts stay on the venue pages, which name their own sources.</p>
<ol class="sources">
<li>Circle Line evening cruises: <a href="https://www.circleline.com/about/nyc-cruise-guide/NYC-Sunset-and-Night-Cruises-Compared" rel="nofollow noopener">Sunset and night cruises compared</a></li>
<li>City Cruises Signature Dinner Cruise: <a href="https://citycruises.com/tickets/new-york-city/new-york-signature-dinner-cruise" rel="nofollow noopener">Signature Dinner Cruise</a></li>
<li>Comedy Cellar: <a href="https://www.comedycellar.com/" rel="nofollow noopener">showtimes and prices</a> and <a href="https://www.comedycellar.com/contact-us/" rel="nofollow noopener">entrances</a></li>
<li>Gotham Comedy Club: <a href="https://gothamcomedyclub.com/" rel="nofollow noopener">Gotham Comedy Club</a></li>
<li>The Stand: <a href="https://www.thestandnyc.com/" rel="nofollow noopener">The Stand</a></li>
<li>New York Comedy Club: <a href="https://www.newyorkcomedyclub.com/" rel="nofollow noopener">New York Comedy Club</a></li>
</ol>"""
    btns = (f'<a class="btn primary" href="{u("/plans/nyc-boat-party.html")}">Boat party</a>'
            f'<a class="btn quiet" href="{u("/guides/nyc-comedy-clubs.html")}">Comedy clubs</a>')
    disclose = f"Affiliate links are labeled. We did not invent a bachelor package price. Facts checked {MONEY_CHECKED}."
    _money_page(page, write, path,
                "NYC bachelor party ideas | NY Nightlife",
                "NYC bachelor party ideas we could verify: an 18+ harbor cruise, comedy clubs, and nightclubs with checked door facts.",
                body + actions(btns, disclose), faqs,
                "NYC bachelor party ideas")
    return path, MONEY_CHECKED


def comedy_clubs(page, write, u, actions, H, vs):
    """Comedy rooms from the clubs' own sites, plus comedy rows in the events feed."""
    import present
    path = "/guides/nyc-comedy-clubs.html"
    rows, fetched = _comedy_feed()
    note = ("Comedy rows are events in the latest feed whose category or title says comedy. "
            "Ticketmaster links are that event's page, with no affiliate tag. "
            f"Feed checked {fetched}.")
    book = affiliates.block(
        ("comedy",), "nynightlife-nyc-comedy-clubs", "nyc-comedy-clubs", u, "Book a comedy show",
        "Viator search, separate from the clubs above. " + affiliates.NOTE_ONE,
        heading_id="book")
    faqs = [
        ("Which comedy clubs did you verify?",
         "Comedy Cellar (117 MacDougal Street, plus Village Underground and Fat Black Pussycat at 130 West 3rd Street), Gotham Comedy Club at 208 West 23rd Street, The Stand at 116 East 16th Street and The Stand West at 407 West 15th Street, and New York Comedy Club at 241 East 24th Street, 85 East 4th Street, and 236 West 78th Street. This page does not rank them."),
        ("What does Comedy Cellar charge?",
         "On 2026-11-16 the Comedy Cellar homepage listed a two-item minimum per person (food, a drink, or a bottle of water). Friday and Saturday shows were $25, Thursday and Sunday shows $18, and Monday to Wednesday shows $15, with New Joke Night at $10 and Hot Soup Comedy at $20. Holidays and special events were $25. Check the homepage before you go."),
        ("Does The Stand have a drink minimum?",
         "The Stand's homepage says its cocktails do not come with a two-drink minimum. That is the club's line, not a price. The site lists hours of Monday to Thursday 12pm to 12am, Friday 12pm to 2am, Saturday 11am to 2am, and Sunday 11am to 12am."),
        ("Where are tonight's comedy shows?",
         "The list on this page is whatever the events feed marked as comedy, or titled as comedy, and that has not already ended. If it is empty, the feed did not include one. Lineups on the club sites change and are not copied here."),
    ]
    by = {v["slug"]: v for v in vs}
    nearby = "".join(
        H["poster"](by[slug], "")
        for slug in ("death-and-co", "attaboy", "please-dont-tell") if slug in by)
    rooms = (
        present.static_poster(
            "Comedy Cellar", "https://www.comedycellar.com/",
            [("Place", "117 MacDougal Street"), ("Price", "Fri and Sat $25"), ("Vibe", "Stand-up")],
            "Two-item minimum per person. Friday and Saturday shows were $25 on " + MONEY_CHECKED + ".",
            "C", external=True, photo="comedy-cellar")
        + present.static_poster(
            "Gotham Comedy Club", "https://gothamcomedyclub.com/",
            [("Place", "208 West 23rd Street"), ("Price", "Not published on the pages we opened"), ("Vibe", "Stand-up")],
            "208 West 23rd Street, between 7th and 8th Avenues. No cover or dress code on the pages we opened.",
            "G", external=True, photo="gotham-comedy-club")
        + present.static_poster(
            "The Stand", "https://www.thestandnyc.com/",
            [("Place", "East 16th Street and West 15th Street"), ("Hours", "Friday 12pm to 2am"), ("Vibe", "Stand-up")],
            "No two-drink minimum. Monday to Thursday 12pm to 12am, Friday 12pm to 2am, Saturday 11am to 2am, Sunday 11am to 12am.",
            "S", external=True, photo="the-stand-nyc")
        + present.static_poster(
            "New York Comedy Club", "https://www.newyorkcomedyclub.com/",
            [("Place", "Midtown, East Village, Upper West Side"), ("Vibe", "Stand-up")],
            "Three rooms: 241 East 24th Street, 85 East 4th Street, and 236 West 78th Street.",
            "N", external=True, photo="new-york-comedy-club")
    )
    body = present.guide_hero("NYC comedy clubs", "Guide · stand-up", MONEY_CHECKED,
                              ["MacDougal St", "West 23rd St", "East 16th St", "East 24th St"]) + f"""
{present.answer_box("Comedy Cellar, Gotham Comedy Club, The Stand, and New York Comedy Club all publish a New York room on their own sites. Comedy Cellar prints show prices and a two-item minimum. The Stand says it has no two-drink minimum. This page does not call any of them the best. Comedy events from the live feed are listed when the feed has them. Checked " + MONEY_CHECKED + ".")}
{present.jump_nav([("rooms", "The rooms"), ("cellar", "Comedy Cellar"), ("gotham", "Gotham"), ("stand", "The Stand"), ("nycc", "New York Comedy Club"), ("feed", "In the feed"), ("book", "Book"), ("questions", "Questions"), ("sources", "Sources")])}
<p class="lede">Four clubs, using only what their own sites said on {MONEY_CHECKED}. No ranking, and no copied lineup.</p>
<div class="vlist two posters" id="rooms">{rooms}</div>
<h2 id="cellar">Comedy Cellar</h2>
<p>The homepage is the price list. On {MONEY_CHECKED} it said every show has a two-item minimum per person, and that the item can be food, a drink, or a bottle of water. Friday and Saturday shows were $25. Thursday and Sunday shows were $18. Monday to Wednesday shows were $15, except New Joke Night at $10 and Hot Soup Comedy at $20. Holidays and special events were $25.</p>
<p>The contact page gives two entrances. 117 MacDougal Street is the Comedy Cellar and the Olive Tree Cafe. 130 West 3rd Street is the Village Underground and Fat Black Pussycat, which has a bar and a lounge. The phone on that page is 212-254-3480. It tells ticket holders to bring the QR code from the reservation email to the entrance named in that email.</p>
<h2 id="gotham">Gotham Comedy Club</h2>
<p>Gotham's site lists the club at 208 West 23rd Street, between 7th and 8th Avenues, New York, NY 10011, phone 212-367-9000. The same pages describe pub food, a liquor selection that includes 30 kinds of vodka, and a wine list. The schedule names the main room and The Vintage Lounge, including a Kids 'N Comedy show. It does not publish a cover or a dress code on the pages we opened, so those are omitted.</p>
<h2 id="stand">The Stand</h2>
<p>The Stand's site lists two rooms: 116 East 16th Street, New York, NY 10003 (212-677-2600) and The Stand West at 407 West 15th Street, New York, NY 10011. Under hours it lists Monday to Thursday 12pm–12am, Friday 12pm–2am, Saturday 11am–2am, and Sunday 11am–12am. The cocktails line says they do not need a two-drink minimum. The contact page points private-party questions to a private parties page. We did not copy that page's packages.</p>
<h2 id="nycc">New York Comedy Club</h2>
<p>New York Comedy Club's site lists three rooms and three phones: Midtown at 241 East 24th Street, New York, NY 10010, (212) 696-5233; East Village at 85 East 4th Street, New York, NY 10003, (212) 994-9828; Upper West Side at 236 West 78th Street, New York, NY 10024, (973) 222-7422. The homepage is a changing lineup, so this guide does not repeat the bill.</p>
<h2 id="feed">Comedy in the events feed</h2>
{present.events_html(rows, "Comedy coming up", note, "No upcoming comedy listing is in the latest feed. That means the feed did not include one, not that the clubs are dark.")}
<h2 id="around">Around the show</h2>
<p>These are checked bars and the rules that actually apply after you leave the club. They are not comedy venues. Death &amp; Co, Attaboy, and Please Don't Tell:</p>
<div class="vlist two posters">{nearby}</div>
<p><a href="{u('/guides/nyc-dress-codes.html')}">Dress codes</a>, <a href="{u('/guides/nyc-bar-closing-time.html')}">the 4am rule</a>, and <a href="{u('/guides/under-21-nyc-bars-clubs.html')}">under 21</a></p>
<p><a href="{u('/tonight/')}">Tonight</a> for the rest of the feed, and <a href="{u('/plans/bachelor-party.html')}">bachelor party ideas</a> if the show is the group's plan</p>
{book}
{present.faq_html(faqs)}
<h2 id="sources">Sources</h2>
<p class="small">Checked {MONEY_CHECKED}. Show bills on these sites change; the addresses and the Comedy Cellar price list are what we wrote down.</p>
<ol class="sources">
<li>Comedy Cellar showtimes and prices: <a href="https://www.comedycellar.com/" rel="nofollow noopener">comedycellar.com</a></li>
<li>Comedy Cellar entrances: <a href="https://www.comedycellar.com/contact-us/" rel="nofollow noopener">contact page</a></li>
<li>Gotham Comedy Club: <a href="https://gothamcomedyclub.com/" rel="nofollow noopener">gothamcomedyclub.com</a> and <a href="https://gothamcomedyclub.com/contact/" rel="nofollow noopener">contact</a></li>
<li>The Stand: <a href="https://www.thestandnyc.com/" rel="nofollow noopener">thestandnyc.com</a> and <a href="https://thestandnyc.com/contact-us" rel="nofollow noopener">contact</a></li>
<li>New York Comedy Club: <a href="https://www.newyorkcomedyclub.com/" rel="nofollow noopener">newyorkcomedyclub.com</a></li>
</ol>"""
    btns = (f'<a class="btn primary" href="#book">Comedy tickets</a>'
            f'<a class="btn quiet" href="{u("/tonight/")}">Tonight</a>')
    disclose = f"Affiliate links are labeled. Club prices are copied only where the club printed them. Facts checked {MONEY_CHECKED}."
    _money_page(page, write, path,
                "NYC comedy clubs | NY Nightlife",
                "Comedy Cellar, Gotham Comedy Club, The Stand, and New York Comedy Club from their own sites, plus comedy events in the live feed.",
                body + actions(btns, disclose), faqs,
                "NYC comedy clubs")
    return path, MONEY_CHECKED


def _field(v, key, field):
    """A checked fact plus the same chip the venue page uses. Empty stays empty."""
    f = v.get(key) or {}
    val = (f.get(field) or "").strip()
    if not val:
        return ""
    chip = {"likely": ' <span class="chip">1 source</span>',
            "unconfirmed": ' <span class="chip">unconfirmed</span>'}.get(f.get("status") or "", "")
    return e(val) + chip


def _pick(vs, slugs):
    by = {v["slug"]: v for v in vs}
    missing = [s for s in slugs if s not in by or by[s].get("status") == "closed"]
    if missing:
        raise SystemExit("guide is missing an open venue: " + ", ".join(missing))
    return [by[s] for s in slugs]


def _checked(venues):
    return max((v.get("checked") or "2026-10-18") for v in venues)


def _posters(H, venues, answer_fn):
    card = H.get("poster") or H["vcard"]
    cards = "".join(card(v, answer_fn(v)) for v in venues)
    return f'<div class="vlist two posters">{cards}</div>'


def _notes(venues):
    rows = [v for v in venues if (v.get("status_note") or "").strip()]
    if not rows:
        return ""
    bits = "".join(f'<p><b>{e(v["name"])}.</b> {e(v["status_note"])}</p>' for v in rows)
    return f'<div class="card">{bits}</div>'


def speakeasies(page, write, u, actions, H, vs):
    """Hidden-door facts copied from venue pages. No venue is called a speakeasy unless the door fact says so."""
    import present
    order = ("please-dont-tell", "the-back-room", "attaboy", "employees-only", "death-and-co")
    venues = _pick(vs, order)
    checked = _checked(venues)
    path = "/guides/nyc-speakeasies.html"

    def answer(v):
        # Hours sit on the poster facts. This line is the door, which is the guide's point.
        return _field(v, "getting_in", "value")

    book = affiliates.block(
        affiliates.SPEAKEASY_GUIDE, "nynightlife-nyc-speakeasies", "nyc-speakeasies", u,
        "Book a tour",
        "Viator search, separate from the bars above. " + affiliates.NOTE,
        heading_id="book")
    faqs = [
        ("Which doors are actually hidden?",
         "Three of the checked rooms describe a door that is not a normal street entrance. Please Don't Tell is entered through the phone booth inside Crif Dogs. The Back Room is entered through the Lower East Side Toy Company gate. Attaboy is the unmarked AB 134 buzzer. Employees Only and Death & Co are walk-in cocktail bars. Their pages do not describe a hidden door."),
        ("Is Mr. Purple a speakeasy?",
         "No. Mr. Purple's checked type is rooftop bar. Its getting-in line names SpeakeasyGo as the events booking page. This site does not treat that ticketing link as a speakeasy. The rooftop guide has the door facts."),
        ("Do these bars take reservations?",
         "It depends on the room, and the card copies the checked line. Please Don't Tell says to book on Resy. Attaboy takes limited reservations and is otherwise first-come at the buzzer. The Back Room says walk-ins are welcome and reservations run through the venue site. Employees Only's bar is walk-in. Death & Co says walk-ins are welcome, with limited reservations."),
        ("What time do they close?",
         "Each card copies the checked hours. Employees Only lists daily 6pm to 4am. State law still stops on-premises alcohol sales at 4am. Holiday hours can differ from the weekly hours. Confirm on the venue page before you go."),
    ]
    body = present.guide_hero("NYC speakeasies", f"Guide · checked {checked}", checked, present.place_chips(venues)) + f"""
<p class="lede">Hidden doors we could check, then two walk-in cocktail bars on the same list. Mr. Purple is a rooftop, so it is not here. Nothing on this page is a ranking.</p>
{present.answer_box("Three checked rooms publish a door that is not a normal street entrance: Please Don't Tell through the phone booth inside Crif Dogs, The Back Room through the Lower East Side Toy Company gate, and Attaboy at the unmarked AB 134 buzzer. Employees Only and Death & Co are walk-in cocktail bars on this page. Mr. Purple is a rooftop bar, so it is not listed here as a speakeasy. Checked " + checked + ".")}
{present.jump_nav([("line", "The night"), ("doors", "The doors"), ("book", "Book a tour"), ("questions", "Questions"), ("sources", "Sources")])}
{present.route_html()}
<h2 id="doors">The doors</h2>
<p class="small">Getting in, then hours. Both lines are copied from the venue page. Dress, age, cover, and the source links stay on that page.</p>
{_posters(H, venues, answer)}
<p>Mr. Purple is a rooftop bar in the checked data, not a hidden-door room. It is on the <a href="{u('/guides/nyc-rooftop-bars.html')}">rooftop guide</a>. <a href="{u('/venues/mr-purple.html')}">Mr. Purple door facts</a>.</p>
<p>The same checked set, for a different question: <a href="{u('/guides/nyc-dress-codes.html')}">dress codes</a>, <a href="{u('/guides/nyc-bar-closing-time.html')}">the 4am rule</a>, <a href="{u('/tonight/')}">tonight</a>, and <a href="{u('/this-weekend/')}">this weekend</a>.</p>
{book}
{present.faq_html(faqs)}
<h2 id="sources">Sources</h2>
<p class="small">Venue facts checked {checked}. Each venue page lists the links behind the lines above. We did not add a door, a price, or a ranking that those pages do not already state.</p>"""
    btns = (f'<a class="btn primary" href="#book">See tours</a>'
            f'<a class="btn quiet" href="{u("/guides/nyc-rooftop-bars.html")}">Rooftop bars</a>')
    _money_page(page, write, path,
                "NYC speakeasies | NY Nightlife",
                "NYC speakeasy doors we could check: Please Don't Tell, The Back Room, and Attaboy, plus the walk-in cocktail bars beside them.",
                body + actions(btns, f"Affiliate links are labeled. Door facts checked {checked}."),
                faqs, "NYC speakeasies", checked=checked)
    return path, checked


def rooftop_bars(page, write, u, actions, H, vs):
    """Every open rooftop in the venue data, plus Le Bain, which is a club with a rooftop tag."""
    import present
    order = ("230-fifth-rooftop", "harriets-rooftop", "le-bain", "magic-hour-rooftop", "mr-purple",
             "ophelia-lounge", "phd-rooftop-lounge", "somewhere-nowhere", "westlight")
    venues = _pick(vs, order)
    checked = _checked(venues)
    path = "/guides/nyc-rooftop-bars.html"

    def answer(v):
        # Hours, including a weather note, are on the poster. Dress stays as the line under them.
        dress = _field(v, "dress", "answer")
        return ("Dress: " + dress) if dress else ""

    book = affiliates.block(
        affiliates.ROOFTOP_GUIDE, "nynightlife-nyc-rooftop-bars", "nyc-rooftop-bars", u,
        "Book a rooftop tour",
        "Viator search, separate from the rooftops above. " + affiliates.NOTE,
        heading_id="book")
    faqs = [
        ("Which rooftop bars did you check?",
         "230 Fifth, Harriet's Rooftop, Le Bain, Magic Hour, Mr. Purple, Ophelia Lounge, PHD Rooftop Lounge, Somewhere Nowhere, and Westlight. Le Bain is filed as a club with a rooftop tag. The others are rooftop bars. This page does not rank them."),
        ("Is there a cover?",
         "It is not one number. 230 Fifth publishes $15 on Friday and $20 on Saturday from 8pm, checked " + checked + ". Le Bain lists no cover for the standing room and a minimum on tables. PHD's cover is unconfirmed. The other pages say none listed, a table minimum, or that a ticket price is not published. Read the venue page."),
        ("What if the weather is bad?",
         "Harriet's hours say the rooftop opens weather permitting. We do not have a weather rule for the others. 230 Fifth's hours are unconfirmed and say Friday has no published closing time."),
        ("Are they 21+?",
         "Not all of them, and not all night. 230 Fifth is 21+ Friday and Saturday after 7pm. Westlight is all ages until 6pm and 21+ after. Magic Hour is 21+ except weekend brunch. Several pages publish no age. The age line on the venue page is the one we checked."),
    ]
    body = present.guide_hero("NYC rooftop bars", f"Guide · checked {checked}", checked, present.place_chips(venues)) + f"""
<p class="lede">The rooftop bars in the checked set, plus Le Bain. Hours and dress on each card are copied from that venue's page. This is not a best-of list.</p>
{present.answer_box("Nine checked places are rooftops: 230 Fifth, Harriet's Rooftop, Le Bain, Magic Hour, Mr. Purple, Ophelia Lounge, PHD Rooftop Lounge, Somewhere Nowhere, and Westlight. Le Bain is a club with a rooftop tag. The others are rooftop bars. Hours and dress on the cards are copied from those pages. This is not a ranking. Checked " + checked + ".")}
{present.jump_nav([("line", "The night"), ("roofs", "The rooftops"), ("book", "Book a tour"), ("questions", "Questions"), ("sources", "Sources")])}
{present.route_html()}
<h2 id="roofs">The rooftops</h2>
<p class="small">Hours, then dress. A chip means the venue page did not confirm that line. Age, cover, and sources stay on the venue page.</p>
{_posters(H, venues, answer)}
{_notes(venues)}
<p>Hidden doors, separate from rooftops: <a href="{u('/guides/nyc-speakeasies.html')}">NYC speakeasies</a>. Also <a href="{u('/guides/nyc-dress-codes.html')}">dress codes</a>, <a href="{u('/tonight/')}">tonight</a>, and <a href="{u('/this-weekend/')}">this weekend</a>.</p>
{book}
{present.faq_html(faqs)}
<h2 id="sources">Sources</h2>
<p class="small">Venue facts checked {checked}. Each venue page lists the links behind the lines above.</p>"""
    btns = (f'<a class="btn primary" href="#book">See tours</a>'
            f'<a class="btn quiet" href="{u("/guides/nyc-speakeasies.html")}">Speakeasies</a>')
    _money_page(page, write, path,
                "NYC rooftop bars | NY Nightlife",
                "NYC rooftop bars we have checked: hours and dress for 230 Fifth, Westlight, Magic Hour, PHD, Harriet's, Le Bain, and the others.",
                body + actions(btns, f"Affiliate links are labeled. Rooftop facts checked {checked}."),
                faqs, "NYC rooftop bars", checked=checked)
    return path, checked


NYE_CHECKED = "2026-11-19"
LAW_106 = "https://www.nysenate.gov/legislation/laws/ABC/106"
SLA_HOURS = "https://sla.ny.gov/county-closing-hours"
TSQ_FAQ = "https://www.timessquarenyc.org/nye/nye-faq"
MOME_NYE = "https://www.nyc.gov/site/mome/press-card/press-card-nye-2027.page"
CIRCLE_NYE = "https://www.circleline.com/nyc-new-years-eve-cruises"


def new_years_eve(page, write, u, actions, H, vs):
    """NYE 2026 from pages opened on NYE_CHECKED, plus venue facts already in the repo. No prices."""
    import present
    _pick(vs, ("magic-hour-rooftop", "phd-rooftop-lounge", "employees-only"))
    path = "/guides/nyc-new-years-eve.html"
    book = affiliates.block(
        affiliates.NYE_GUIDE, "nynightlife-nyc-new-years-eve", "nyc-new-years-eve", u,
        "Book an NYE cruise or tour",
        "Viator search, separate from the operator pages above. " + affiliates.NOTE,
        heading_id="book")
    faqs = [
        ("When is New Year's Eve 2026?",
         "Thursday, December 31, 2026. New York City's Mayor's Office of Media and Entertainment dates the 2027 Times Square ball drop that day. The Times Square Alliance FAQ, checked the same day as this page, calls the season New Year's Eve 2027."),
        ("What time is the ball drop?",
         "The Times Square Alliance FAQ says the celebration begins shortly before 6:00pm EST, the ball is raised at about 6:00pm EST, and at 11:59pm EST it starts a 60-second descent from the flagpole at One Times Square. Viewing areas open at 3pm, first come, first served, with no ticket. The same FAQ also tells people to watch a webcast at 6pm on December 31 and calls that stream the NYE 2026 celebration."),
        ("What time do NYC bars close on New Year's Eve?",
         "4am, according to the closing-time guide on this site. That guide cites New York ABC Law section 106(5): no on-premises alcohol sales from 4am to 8am, and no drinking on the premises more than half an hour after 4am. The guide's citation does not describe a New Year's Eve exception. December 31, 2026 is a Thursday, so the Sunday-morning rule in that section is not the one in effect that night. Many venues close earlier. Weekly hours on a venue page are not an NYE schedule."),
        ("How much is an NYE cruise?",
         "Circle Line's New Year's Eve page does not print a price, and this guide does not invent one. The page describes two Pier 83 sailings for ringing in 2027 and does not print a calendar date. Read the operator's listing. Viator links below are a separate search."),
    ]
    body = present.guide_hero("New Year's Eve 2026", f"Guide · official pages checked {NYE_CHECKED}", NYE_CHECKED,
                              ["Times Square", "Midtown", "Pier 83"]) + f"""
<p class="lede">The ball drop, two cruises, and the 4am rule. Only what an official page or a checked venue page actually says. No prices.</p>
{present.answer_box("New Year's Eve 2026 is Thursday, December 31. New York City dates the Times Square ball drop that night. The Alliance FAQ says the ball goes up around 6:00pm EST and starts a 60-second descent at 11:59pm EST, and that the outdoor viewing areas open at 3pm with no ticket. On-premises alcohol sales still stop at 4am. This page does not publish a cruise or party price. Official pages checked " + NYE_CHECKED + ".")}
{present.jump_nav([("line", "The night"), ("ball", "Ball drop"), ("cruises", "Cruises"), ("parties", "Parties and bars"), ("close", "4am"), ("book", "Book"), ("questions", "Questions"), ("sources", "Sources")])}
{present.route_html()}
<h2 id="ball">Times Square ball drop</h2>
<p>New York City's <a href="{MOME_NYE}" rel="nofollow noopener">press-card page</a> titles the event the 2027 New Year's Eve ball drop and dates it Thursday, Dec. 31, 2026. That page is about press credentials, not about public viewing.</p>
<p>The <a href="{TSQ_FAQ}" rel="nofollow noopener">Times Square Alliance FAQ</a>, checked {NYE_CHECKED}, opens with New Year's Eve 2027. It says the ball descends from a flagpole at the top of One Times Square, best seen along Broadway from 43rd Street to 50th Street and along Seventh Avenue as far north as 59th Street. The celebration begins shortly before 6:00pm EST. At about 6:00pm EST the ball is raised. At 11:59pm EST it makes a 60-second descent. Viewing areas open at 3pm on a first-come, first-served basis. The FAQ says no ticket is needed and that no public viewing space is for sale. Access points it lists: 45th, 49th, 52nd, and 56th Streets, from 6th Avenue and from 8th Avenue.</p>
<p>The same FAQ says all bags are searched. It says backpacks, large bags, umbrellas, lawn chairs, alcohol, drones, and weapons are not permitted, and that there are no portable restrooms in Times Square during the celebration. The designated viewing area for people with disabilities is at 44th Street and Broadway, reached from the southwest corner of 44th Street and 6th Avenue.</p>
<p>One line on that FAQ does not match the heading. It says to join the webcast at 6pm on December 31 for the NYE 2026 celebration. The City page above dates the drop December 31, 2026. Read the Alliance page again before you go. This guide does not copy the performer list on the FAQ. The FAQ does not date that list to December 31, 2026.</p>
<p>The FAQ also says Notify NYC takes the keyword NEWYEARSEVE at 692692 for weather and street alerts. It says message and data rates may apply.</p>
<h2 id="cruises">Cruises</h2>
<p><a href="{CIRCLE_NYE}" rel="nofollow noopener">Circle Line's New Year's Eve page</a>, checked {NYE_CHECKED}, describes two sailings for ringing in 2027. Both board at Pier 83, Midtown, 83 North River Piers, New York, NY 10036, at 9:00pm, and run 10:00pm to 1:00am. The dinner cruise is all ages and lists a buffet, an open bar, a dessert display, a live DJ, a champagne toast, and fireworks views. The party cruise is 21+ and lists a live DJ, an open standard bar, passed appetizers, a champagne toast at midnight, and fireworks views near the Statue of Liberty. That page does not print a calendar date or a ticket price, so this guide does not either. <a href="{u('/plans/nyc-dinner-cruises.html')}">Dinner and sunset cruises</a> has the other piers we have checked, and says a sunset cruise on another night is not an NYE ticket.</p>
<h2 id="parties">Parties and bars</h2>
<p>The Alliance FAQ says some restaurants and hotels in Times Square hold private parties that need a ticket bought ahead. It warns that multi-venue, pay-one-price, all-access passes have advertised movement through Times Square that police checkpoints have not allowed. This page does not list those parties and does not repeat a price.</p>
<p>Checked rooms, if the night continues indoors. Their weekly hours are not an NYE schedule. Holiday hours can differ, and we have not re-checked them for December 31.</p>
<ul class="clean">
<li><a href="{u('/venues/magic-hour-rooftop.html')}">Magic Hour</a>, the Times Square rooftop we have checked</li>
<li><a href="{u('/venues/phd-rooftop-lounge.html')}">PHD Rooftop Lounge</a>. When we checked it on 2026-10-18, a New Year's Eve 2026 ticket-terms page was one source for the 21+ line. This guide does not copy that ticket's price or start time. The venue page also notes a generic closed-for-the-season pop-up that does not name the venue.</li>
<li><a href="{u('/venues/employees-only.html')}">Employees Only</a>, which lists a bar open daily until 4am on the weekly hours we checked</li>
<li><a href="{u('/guides/nyc-rooftop-bars.html')}">Rooftop bars</a>, <a href="{u('/guides/nyc-speakeasies.html')}">speakeasies</a>, and <a href="{u('/guides/nyc-dress-codes.html')}">dress codes</a></li>
</ul>
<h2 id="close">Last call is still 4am</h2>
<p>The <a href="{u('/guides/nyc-bar-closing-time.html')}">closing-time guide</a> cites <a href="{LAW_106}" rel="noopener">NY ABC Law §106(5)</a>: no on-premises alcohol sales from 4am to 8am, or from 4am to 10am on Sunday, and no drinking on the premises more than half an hour after 4am. It says the State Liquor Authority's <a href="{SLA_HOURS}" rel="noopener">county closing hours</a> list 4am for all five boroughs. That guide checked the law text on 2026-10-23. Its citation of section 106(5) does not describe a New Year's Eve exception. A venue can close earlier. <a href="{u('/this-weekend/')}">This weekend</a> is the Friday-to-Sunday feed, which is a different night from December 31.</p>
{book}
{present.faq_html(faqs)}
<h2 id="sources">Sources</h2>
<p class="small">Times Square Alliance, NYC Media and Entertainment, and Circle Line checked {NYE_CHECKED}. The alcohol statute was checked 2026-10-23 on the closing-time guide. Venue pages were checked 2026-10-18. No price from any of those pages is reprinted here.</p>
<ol class="sources">
<li>Times Square Alliance, New Year's Eve FAQ: <a href="{TSQ_FAQ}" rel="nofollow noopener">timessquarenyc.org/nye/nye-faq</a></li>
<li>NYC Mayor's Office of Media and Entertainment, 2027 ball drop press cards: <a href="{MOME_NYE}" rel="nofollow noopener">nyc.gov, dated Thursday, Dec. 31, 2026</a></li>
<li>Circle Line, New Year's Eve cruises: <a href="{CIRCLE_NYE}" rel="nofollow noopener">circleline.com/nyc-new-years-eve-cruises</a></li>
<li>NY ABC Law §106: <a href="{LAW_106}" rel="noopener">nysenate.gov</a></li>
<li>State Liquor Authority county closing hours: <a href="{SLA_HOURS}" rel="noopener">sla.ny.gov/county-closing-hours</a></li>
</ol>"""
    btns = (f'<a class="btn primary" href="#book">NYE cruises</a>'
            f'<a class="btn quiet" href="{u("/guides/nyc-bar-closing-time.html")}">4am rule</a>')
    _money_page(page, write, path,
                "NYC New Year's Eve 2026 | NY Nightlife",
                "New Year's Eve 2026 in NYC: Times Square ball drop basics, Circle Line's NYE cruises, and the 4am close. No invented prices.",
                body + actions(btns, f"Affiliate links are labeled. Official pages checked {NYE_CHECKED}. No prices copied."),
                faqs, "New Year's Eve in NYC", checked=NYE_CHECKED)
    return path, NYE_CHECKED


def build(page, write, u, actions, fmt_date, vs, H):
    for f in sorted((ROOT / "data" / "playbooks").glob("*.json")):
        playbook(page, write, u, actions, fmt_date, json.loads(f.read_text(encoding="utf-8")), H)
    cruise = cruise_guide(page, write, u, actions, fmt_date, H)
    boat = boat_party(page, write, u, actions, H, vs)
    bachelor = bachelor_party(page, write, u, actions, H, vs)
    comedy = comedy_clubs(page, write, u, actions, H, vs)
    speak = speakeasies(page, write, u, actions, H, vs)
    roofs = rooftop_bars(page, write, u, actions, H, vs)
    nye = new_years_eve(page, write, u, actions, H, vs)
    plans_hub(page, write, u)
    image_credits(page, write)
    home(page, write, u, vs, H)
    trust_pages(page, write, u)
    return [cruise, boat, bachelor, comedy, speak, roofs, nye,
            ("/plans/", MONEY_CHECKED), ("/image-credits.html", "2026-11-11")]
