"""Hand-written pages for NY Nightlife v2: home, group playbooks, trust pages."""
import html
import json
import pathlib
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
    body = H["plate"](pb["slug"], pb["title"], f"Group playbook · party of {pb['group']}", credit=credit,
                      alt="Lower Manhattan skyline at sunset from New York Harbor",
                      style="margin-top:12px") + f"""
<p class="lede">Real prices from listings we checked, split per person for a group of {pb['group']}. Pick one or stack two.</p>
<div class="scale" aria-hidden="true"><span>Per person</span><span>$0 · ${mx // 2} · ${mx}</span></div>
<div class="posters">{posters}</div>
<div class="total"><span>{e(c['label'])}<span class="small" style="display:block">your night, each</span></span><b>${c['low']}–{c['high']}</b></div>
{book}
<h2>How we worked it out</h2>
<p>Cruise prices are per ticket. Bus and yacht prices are the whole booking divided by {pb['group']} people, before tip, tolls and fees unless noted. Listing prices change by date and season, so confirm the total before you pay.</p>
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
    snap = events.load_snapshot()
    now = events.local_now()
    tonight, week = present.split_events(snap.get("events") or [], now)
    shown = (tonight + week)[:6]
    late = 0
    key = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][now.weekday()]
    for v in vs:
        if v.get("status") == "closed":
            continue
        span = ((v.get("hours") or {}).get("week") or {}).get(key)
        if span and __import__("extras").close_mins(span) >= 24 * 60:
            late += 1
    fetched = (snap.get("fetched_at") or "")[:10] or now.date().isoformat()
    week_n = len(snap.get("events") or [])
    if tonight:
        count_bit = f"{len(tonight)} tonight · {week_n} this week"
    else:
        count_bit = f"{week_n} this week"
    live = f'{now.strftime("%a")} {now.date().isoformat()} · {count_bit} · {late} open past midnight'
    hero = H["picture"]("home", "An East Village sidewalk at night",
                        "(min-width: 900px) 1100px, 100vw", eager=True)
    note = ("NYC Parks events and permitted street festivals are from NYC Open Data. "
            "Music, comedy, theatre, and nightlife are added from Ticketmaster when that key is set. "
            "Ticketmaster images sit only beside that event, and the link is the event page. "
            f"Feed checked {fetched}.")
    short = (f"Tonight in New York, this site lists {n} checked bars and clubs and the public events we could pull for this week. "
             f"{len(tonight)} of those events fall in tonight's 5pm to 5am window, and {late} venues list hours past midnight on {now.strftime('%A')}. "
             "Dress code, age, and cover stay on each venue page with the date we checked them.")
    body = f"""<section class="hero">{hero}<div class="hero-copy"><p class="eyebrow">New York City</p><h1>Tonight in New York</h1>
<p class="hero-live">{e(live)}</p>
<div class="inline-actions"><a class="btn primary" href="{u('/tonight/')}">What's on tonight</a><a class="btn ghost" href="{u('/plans/')}">Plan a group night</a></div>
</div></section>
<p class="credit">Photo: {credit}</p>
{present.answer_box(short)}
{present.events_html(shown, "What's on in NYC tonight / this week", note, "No evening parks, festival, or ticketed listings are in the latest feed.")}
{present.route_html()}
<h2>Beyond the bar</h2>
<p class="lede">Cruises, a comedy booking link, and the door facts. The cruise page only states what we could verify.</p>
<a class="card-link" href="{u('/plans/nyc-dinner-cruises.html')}"><span>Dinner and sunset cruises<span class="sub">Piers and timing we could verify</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/guides/nyc-dress-codes.html')}"><span>Dress codes<span class="sub">What {n} venues say, or that they say nothing</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/guides/nyc-bar-closing-time.html')}"><span>The 4am rule<span class="sub">When service stops, and who lists later hours</span></span><span class="go">Read →</span></a>
<h2>Group nights</h2>
<a class="card-link" href="{u('/plans/')}"><span>Group nights<span class="sub">Bachelorette prices and the cruise guide</span></span><span class="go">Open →</span></a>
<a class="card-link" href="{u('/plans/bachelorette-night.html')}"><span>Bachelorette Night for 10<span class="sub">Cruise, party bus or yacht, priced per person</span></span><span class="go">See prices →</span></a>
{H['home_box']()}
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
                              img_alt="Tonight in New York", updated=fetched))


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
<li>Nyla, our chat helper, runs in your browser. What you type isn't sent or saved anywhere; she only remembers when she last said hello, so she doesn't pop up on every page.</li>
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
    write("/404.html", page("Page not found | NY Nightlife", "This page doesn't exist.", "/404.html",
                            f'<h1 style="margin-top:24px">Not here.</h1><p class="lede">That page moved or never existed.</p><div class="inline-actions"><a class="btn primary" href="{u("/venues/")}">Find a venue</a><a class="btn ghost" href="{u("/")}">Home</a></div>',
                            None, "no-bar", "noindex"))


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
    body = H["plate"]("bachelorette-night", "NYC Dinner & Sunset Cruises", "Guide · New York Harbor",
                      credit=credit,
                      alt="Lower Manhattan skyline at sunset from New York Harbor",
                      style="margin-top:12px") + f"""
<p class="lede">Where sunset, dinner, jazz, brunch, and New Year's Eve cruises leave from, and how long the sailings we could verify actually run. If a fact is missing, we did not confirm it.</p>
<h2>Sunset cruises</h2>
<p>Circle Line publishes three evening cruises. Checked on the operator's pages, Nov 11, 2026.</p>
<ul class="clean">
<li><b>Harbor Lights</b>: 2 hours from Pier 83, Midtown (83 North River Piers, New York, NY 10036). Live narration, a full bar, and concessions. It leaves at 7pm for most of the year and at 6pm from January through March.</li>
<li><b>Statue at Sunset</b>: about 90 minutes from Pier 16 at the South Street Seaport (89 South Street, New York, NY 10038). Music and drinks, no narration. Departure time moves with sunset.</li>
<li><b>Sip 'N Groove</b>: 2 hours from Pier 83, with a live DJ and a full bar. 18+.</li>
</ul>
<p>Circle Line says Harbor Lights and Statue at Sunset can work for families comfortable with an evening departure. Sip 'N Groove is 18 and older. Those three pages do not publish a dress code. Harbor Lights has open-air decks, so bring a layer for that sailing.</p>
<p>On Oct 18, 2026 we checked two public sunset and harbor tickets, Circle Line Harbor Lights and the Grande Mariner DJ sunset cruise from Pier 36 (21+), at about $48–$55 a person. That number is from those listings on that date. It is not a dinner-cruise price. The same check is on <a href="{u('/plans/bachelorette-night.html')}">Bachelorette Night for 10</a>.</p>
<h2>Dinner cruises</h2>
<p>A dinner cruise is a different ticket from a sightseeing cruise that happens to sell drinks. NYC Tourism lists City Cruises Signature Dining at Pier 61, Chelsea Piers, West 23rd Street and 12th Avenue, and marks that listing wheelchair accessible. The tourism page does not say how long the cruise runs or what to wear.</p>
<p>Other dinner boats leave from other piers and set their own dress codes. Read the listing for the boat you book. We are not publishing a dinner-cruise price.</p>
<h2>Jazz and brunch cruises</h2>
<p>Jazz cruises and brunch cruises are separate listings. Pier, length, what is included, and dress code change by boat. We have not confirmed one jazz or brunch sailing's details on this page.</p>
<h2>New Year's Eve 2026</h2>
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
    body = """<p class="eyebrow">Group nights</p><h1>Plan a group night</h1>
<p class="lede">Two pages we have actually checked: a per-person price split for a group of 10, and a cruise guide that only states piers and timing we could verify.</p>
<a class="card-link" href="/plans/bachelorette-night.html"><span>Bachelorette Night for 10<span class="sub">Cruise, party bus, or yacht, priced per person. Checked Oct 18, 2026.</span></span><span class="go">See prices →</span></a>
<a class="card-link" href="/plans/nyc-dinner-cruises.html"><span>NYC dinner and sunset cruises<span class="sub">Piers, timing, and what we did not confirm. Checked Nov 11, 2026.</span></span><span class="go">Read →</span></a>
"""
    write("/plans/index.html", page("Group nights in NYC | NY Nightlife",
                                    "Bachelorette prices per person and a checked guide to NYC dinner and sunset cruises.",
                                    "/plans/", body, None, "no-bar", updated="2026-11-11"))


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
        rows.append((v["name"], ph.get("credit", ""), ph.get("license", ""), ph.get("license_url", ""), ph.get("url", ""), ph.get("depicts", "")))
    rows.append(("Homepage hero", HOME_PHOTO["credit"], HOME_PHOTO["license"], "https://creativecommons.org/licenses/by/2.0/", HOME_PHOTO["page"], "East Village sidewalk at night"))
    rows.append(("Harbor photograph", HARBOR_PHOTO["credit"], HARBOR_PHOTO["license"], "https://creativecommons.org/licenses/by-sa/4.0/", HARBOR_PHOTO["page"], "Lower Manhattan skyline from the harbor"))
    items = ""
    for name, credit, lic, lurl, src, depicts in rows:
        bit = f"<li><b>{e(name)}</b>: {e(credit)}"
        if lic:
            bit += f' · <a href="{e(lurl)}" rel="license noopener">{e(lic)}</a>' if lurl else f" · {e(lic)}"
        if src:
            bit += f' · <a href="{e(src)}" rel="noopener">source file</a>'
        if depicts:
            bit += f" · {e(depicts)}"
        items += bit + "</li>"
    body = f"""<p class="eyebrow">Credits</p><h1>Image credits</h1>
<p class="lede">Photographs on this site are ones we have a license to store. Venue pages without one use a CSS cover, not a stand-in photo. Ticketmaster event images, when a listing has one, are loaded from Ticketmaster next to that event and are not saved here.</p>
<ul class="clean">{items}</ul>"""
    write("/image-credits.html", page("Image credits | NY Nightlife",
                                     "Photograph credits and licenses for images stored on NY Nightlife.",
                                     "/image-credits.html", body, None, "no-bar", updated="2026-11-11"))


def build(page, write, u, actions, fmt_date, vs, H):
    for f in sorted((ROOT / "data" / "playbooks").glob("*.json")):
        playbook(page, write, u, actions, fmt_date, json.loads(f.read_text(encoding="utf-8")), H)
    cruise = cruise_guide(page, write, u, actions, fmt_date, H)
    plans_hub(page, write, u)
    image_credits(page, write)
    home(page, write, u, vs, H)
    trust_pages(page, write, u)
    return [cruise, ("/plans/", "2026-11-11"), ("/image-credits.html", "2026-11-11")]
