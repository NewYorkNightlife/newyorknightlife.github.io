"""Hand-written pages for NY Nightlife v2: home, group playbooks, trust pages."""
import html
import json
import pathlib
import urllib.parse

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
    body = H["plate"](pb["slug"], pb["title"], f"Group playbook · party of {pb['group']}", credit=credit,
                      alt="Lower Manhattan skyline at sunset from New York Harbor",
                      style="margin-top:12px") + f"""
<p class="lede">Real prices from listings we checked, split per person for a group of {pb['group']}. Pick one or stack two.</p>
<div class="scale" aria-hidden="true"><span>Per person</span><span>$0 · ${mx // 2} · ${mx}</span></div>
<div class="posters">{posters}</div>
<div class="total"><span>{e(c['label'])}<span class="small" style="display:block">your night, each</span></span><b>${c['low']}–{c['high']}</b></div>
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
    write(path, page(f"{pb['title']}: real prices per person for {pb['group']} | NY Nightlife",
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
    by = {v["slug"]: v for v in vs}
    feat = [by[s] for s in FEATURED if s in by and by[s].get("status") != "closed"]
    cards = "".join(
        H["vcard"](v, v.get("neighborhood", ""),
                   "Dress: " + e((v.get("dress") or {}).get("answer") or "not found yet") + age_bit(v))
        for v in feat)
    n = len([v for v in vs if v.get("status") != "closed"])
    credit = f'<a href="{e(HOME_PHOTO["page"])}" rel="noopener">{e(HOME_PHOTO["credit"])}</a> · {e(HOME_PHOTO["license"])}'
    body = H["plate"]("home", "NY Nightlife", "New York City", title="Know before you go.", credit=credit,
                      alt="An East Village sidewalk at night", style="margin-top:12px") + f"""
<p class="lede">Dress code, age, cover and how to get in for {n} NYC bars and clubs. Every fact shows its source and the date we checked it.</p>
<div class="inline-actions"><a class="btn primary" href="{u('/venues/')}">Find a venue</a><a class="btn ghost" href="{u('/guides/nyc-dress-codes.html')}">All dress codes</a></div>
{H['home_box']()}
<h2>Most asked about</h2>
<div class="vlist two">{cards}</div>
<h2>Guides</h2>
<a class="card-link" href="{u('/guides/nyc-bar-closing-time.html')}"><span>What time do NYC bars close?<span class="sub">The 4am rule, and who stays open latest</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/guides/under-21-nyc-bars-clubs.html')}"><span>Under 21 in NYC<span class="sub">Which bars and clubs let you in, and on what terms</span></span><span class="go">Read →</span></a>
<a class="card-link" href="{u('/changes/')}"><span>What changed<span class="sub">Every update to our checked facts, by date</span></span><span class="go">See log →</span></a>
<div class="split">
<div><h2>Planning for a group?</h2>
<a class="card-link" href="{u('/plans/bachelorette-night.html')}"><span>Bachelorette Night for 10<span class="sub">Cruise, party bus or yacht, priced per person</span></span><span class="go">See prices →</span></a></div>
<div><h2>Why trust this</h2>
<div class="card"><ul class="clean">
<li>Each fact is checked against the venue's own site or two independent sources.</li>
<li>If we can't confirm something, we say so, with an "unconfirmed" label.</li>
<li>Every page shows the date it was checked. We never pretend it's fresher.</li></ul>
<p><a href="{u('/how-we-check.html')}">How we check →</a></p></div></div>
</div>"""
    schema = {"@context": "https://schema.org", "@type": "WebSite", "name": "NY Nightlife", "url": SITE + "/"}
    write("/index.html", page("NY Nightlife: NYC bar & club dress codes, age & cover, checked",
                              "Know before you go: dress code, age, cover and how to get in for NYC bars and clubs, with sources and dates.",
                              "/", body, schema, "no-bar", image="/img/og/site.jpg",
                              img_alt="NY Nightlife: know before you go"))


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
<p>Affiliate links are labeled where they appear. Commissions never decide what a page says: dress codes, ages and prices are reported as the sources show them, including when that's bad news for a venue.</p>
<p>We don't accept payment for reviews or rankings. If we ever sell a sponsored placement, it will be labeled "Sponsored".</p>""")
    simple(page, write, "/privacy.html", "Privacy | NY Nightlife", "What NY Nightlife collects.", "Privacy",
           """<p class="lede">We keep this simple.</p>
<ul class="clean"><li>We count page visits and link clicks with privacy-friendly analytics that don't set cookies or identify you.</li>
<li>We don't run ad trackers.</li>
<li>Nyla, our chat helper, runs in your browser. What you type isn't sent or saved anywhere; she only remembers when she last said hello, so she doesn't pop up on every page.</li>
<li>Our fonts are served from this site, so loading a page no longer sends your IP address to Google.</li>
<li>Our analytics provider, PostHog, does receive page views and clicks from US servers. It sets no cookies, doesn't identify you, and honours Do Not Track. Add <code>?notrack=1</code> to any URL to opt out.</li>
<li>The Tonight page and the home page's tonight box load their data only from this site. A scheduled job (run on GitHub) fetches the forecast from the National Weather Service, plus headlines and liquor-license data, and saves them here, so your browser never contacts those services.</li>
<li>The weekly email, once it starts, will be sent with Kit (kit.com). If you sign up, Kit stores your email address to send it; you confirm by email first, every email has an unsubscribe link, and we delete your address on request.</li>
<li>If you click through to a booking site, that site has its own privacy policy and may set its own cookies.</li>
<li>If you email us, we use your email only to reply.</li></ul>
<p>Questions: <a href="mailto:privacy@nynightlife.com">privacy@nynightlife.com</a>.</p>""")
    simple(page, write, "/contact.html", "Contact | NY Nightlife", "Contact NY Nightlife.", "Contact",
           """<p class="lede">Corrections, door reports and everything else: <a href="mailto:hello@nynightlife.com">hello@nynightlife.com</a>.</p>
<p>Venues: if something on your page is wrong, tell us with a link to where it's stated and we'll fix it.</p>""")
    write("/404.html", page("Page not found | NY Nightlife", "This page doesn't exist.", "/404.html",
                            f'<h1 style="margin-top:24px">Not here.</h1><p class="lede">That page moved or never existed.</p><div class="inline-actions"><a class="btn primary" href="{u("/venues/")}">Find a venue</a><a class="btn ghost" href="{u("/")}">Home</a></div>',
                            None, "no-bar", "noindex"))


def build(page, write, u, actions, fmt_date, vs, H):
    for f in sorted((ROOT / "data" / "playbooks").glob("*.json")):
        playbook(page, write, u, actions, fmt_date, json.loads(f.read_text(encoding="utf-8")), H)
    home(page, write, u, vs, H)
    trust_pages(page, write, u)
