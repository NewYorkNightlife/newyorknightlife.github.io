"""Affiliate markup: real Viator facts only, exact Klook portal links, sponsored rel.

Run after build.py (the Daily build does). The page scan reads the HTML that
build just wrote.
"""
import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import affiliates  # noqa: E402

REL = 'rel="sponsored nofollow noopener"'
PRICED = {"sunset-yacht": ("4.9", "105", "$86"), "drag": ("4.9", "22", "$49")}


def _fail(msg):
    print("FAIL", msg)
    return 1


def main():
    errors = 0
    u = lambda p: p
    home = affiliates.block(affiliates.HOME, "nynightlife-home", "home", u, "Book a night out")
    if home.count("<a ") != 9:
        errors += _fail(f"home block has {home.count('<a ')} anchors, want 8 offers + disclosure link")
    if home.count('class="card-link"') != 8 or home.count('href="/affiliate-disclosure.html"') != 1:
        errors += _fail("home block shape")
    for offer in affiliates.OFFERS:
        url = affiliates.href(offer, "nynightlife-home")
        for key, val in (("pid", "P00330813"), ("mcid", "42383"), ("medium", "link"), ("campaign", "nynightlife-home")):
            if f"{key}={val}" not in url:
                errors += _fail(f"{offer['id']} missing {key}={val}: {url}")
        if "viator.com" not in url:
            errors += _fail(f"{offer['id']} left viator")
        card = affiliates.block((offer["id"],), "nynightlife-x", "x", u)
        if REL not in card or 'target="_blank"' not in card:
            errors += _fail(f"{offer['id']} rel/target")
        if 'data-partner="viator"' not in card or 'data-placement="x"' not in card:
            errors += _fail(f"{offer['id']} tracking attrs")
        if offer["id"] in PRICED:
            for bit in PRICED[offer["id"]]:
                if bit not in card:
                    errors += _fail(f"{offer['id']} dropped fact {bit}")
        else:
            if re.search(r"\$\d|4\.\d", card):
                errors += _fail(f"{offer['id']} invented a rating or price: {card}")
    roof = affiliates.venue_block({"slug": "mr-purple", "type": "rooftop bar", "status": "open"}, u)
    if "nynightlife-rooftop" not in roof or 'data-placement="rooftop:mr-purple"' not in roof:
        errors += _fail("rooftop venue card")
    speak = affiliates.venue_block({"slug": "please-dont-tell", "type": "cocktail bar", "status": "open"}, u)
    if "nynightlife-speakeasy" not in speak:
        errors += _fail("speakeasy venue card")
    drag = affiliates.venue_block({"slug": "house-of-yes", "type": "club", "status": "open"}, u)
    if "$49" not in drag or "nynightlife-drag" not in drag:
        errors += _fail("drag venue card")
    plain = affiliates.venue_block({"slug": "nebula", "type": "club", "status": "open"}, u)
    if "nynightlife-nebula" not in plain or "searchResults" not in plain or 'data-placement="night:nebula"' not in plain:
        errors += _fail("club venue card")
    if "affiliate-disclosure.html" not in plain or 'rel="sponsored nofollow noopener"' not in plain:
        errors += _fail("club venue card missing disclosure or rel")
    closed = affiliates.venue_block({"slug": "mr-purple", "type": "rooftop bar", "status": "closed"}, u)
    unknown = affiliates.venue_block({"slug": "not-a-venue", "type": "club", "status": "open"}, u)
    mirage = affiliates.venue_block({"slug": "brooklyn-mirage", "type": "club", "status": "closed"}, u)
    if closed or unknown or mirage:
        errors += _fail("unexpected venue card")
    if len(affiliates.EXTRA_VENUE) != 17:
        errors += _fail(f"expected 17 venue cards, got {len(affiliates.EXTRA_VENUE)}")
    for slug, (offer, kind) in affiliates.EXTRA_VENUE.items():
        card = affiliates.venue_block({"slug": slug, "type": "club", "status": "open"}, u)
        if f"nynightlife-{slug}" not in card or f'data-placement="{kind}:{slug}"' not in card:
            errors += _fail(f"{slug} campaign or placement")
        if "searchResults" not in card or "/tours/" in card:
            errors += _fail(f"{slug} should be a search link, not a product URL")
        if offer not in card and affiliates.BY_ID[offer]["title"] not in card:
            errors += _fail(f"{slug} missing offer {offer}")
    cruises = affiliates.block(affiliates.CRUISES, "nynightlife-nyc-dinner-cruises", "nyc-dinner-cruises", u, "Book a cruise")
    if cruises.count('class="card-link"') != 4 or "searchResults" not in cruises:
        errors += _fail("cruise guide block")
    if cruises.count("searchResults") != 4 or "/tours/" in cruises or re.search(r"\$\d", cruises):
        errors += _fail("cruise guide invented a product or a price")
    if "affiliate-disclosure.html" not in cruises or "nynightlife-nyc-dinner-cruises" not in cruises:
        errors += _fail("cruise guide disclosure or campaign")
    for name, ids in (
        ("weekend", affiliates.WEEKEND),
        ("speakeasy guide", affiliates.SPEAKEASY_GUIDE),
        ("rooftop guide", affiliates.ROOFTOP_GUIDE),
        ("nye guide", affiliates.NYE_GUIDE),
    ):
        card = affiliates.block(ids, "nynightlife-t", "t", u, "Book")
        if card.count('class="card-link"') != len(ids):
            errors += _fail(f"{name} card count")
        if re.search(r"\$\d", card) or "/tours/" in card:
            errors += _fail(f"{name} invented a price or a product url")
        if "searchResults" not in card or "pid=P00330813" not in card:
            errors += _fail(f"{name} lost the viator search tag")
    allowed = {
        "https://affiliate.klook.com/redirect?aid=145278&aff_adid=1599979&k_site=https%3A%2F%2Fwww.klook.com%2Fen-US%2Fdestination%2Fc93-new-york%2F",
        "https://affiliate.klook.com/redirect?aid=145278&aff_adid=1599975&k_site=https%3A%2F%2Fwww.klook.com%2Fen-US%2Factivity%2F10784-harbor-lights-cruise-new-york%2F",
        "https://affiliate.klook.com/redirect?aid=145278&aff_adid=1599974&k_site=https%3A%2F%2Fwww.klook.com%2Fen-US%2Factivity%2F2964-top-of-the-rock-new-york%2F",
        "https://affiliate.klook.com/redirect?aid=145278&aff_adid=1599976&k_site=https%3A%2F%2Fwww.klook.com%2Fen-US%2Factivity%2F7705-lion-king-broadway-show-ticket-new-york%2F",
        "https://affiliate.klook.com/redirect?aid=145278&aff_adid=1599977&k_site=https%3A%2F%2Fwww.klook.com%2Fen-US%2Factivity%2F11167-new-york-city-pass-attractions-new-york%2F",
        "https://affiliate.klook.com/redirect?aid=145278&aff_adid=1599978&k_site=https%3A%2F%2Fwww.klook.com%2Fen-US%2Factivity%2F107217-new-york-all-inclusive-pass%2F",
    }
    prefix = "https://affiliate.klook.com/redirect?aid=145278"
    if len(affiliates.KLOOK_OFFERS) != 6 or {o["url"] for o in affiliates.KLOOK_OFFERS} != allowed:
        errors += _fail("Klook offer list is not the six approved portal links")
    if affiliates.KLOOK_AID != "145278":
        errors += _fail("Klook AID")
    for offer in affiliates.KLOOK_OFFERS:
        if not offer["url"].startswith(prefix) or offer["url"] not in allowed:
            errors += _fail(f"{offer['id']} is not an approved Klook href")
        if "pid=" in offer["url"] or "mcid=" in offer["url"]:
            errors += _fail(f"{offer['id']} gained a Viator parameter")

    def klook_hrefs(markup):
        return [html.unescape(h) for h in re.findall(r'href="([^"]+)"', markup) if "affiliate-disclosure" not in h]

    groups = (
        ("visitor", affiliates.KLOOK_VISITOR),
        ("ahead", affiliates.KLOOK_AHEAD),
        ("harbor", affiliates.KLOOK_HARBOR),
        ("show", affiliates.KLOOK_SHOW),
    )
    for name, ids in groups:
        card = affiliates.klook_block(ids, "klook:test", u, "Book ahead")
        hrefs = klook_hrefs(card)
        want = [affiliates.KLOOK_BY_ID[i]["url"] for i in ids]
        if hrefs != want:
            errors += _fail(f"{name} hrefs {hrefs}")
        for url in hrefs:
            if not url.startswith(prefix) or url not in allowed:
                errors += _fail(f"{name} href left the approved set: {url}")
        if card.count('data-partner="klook"') != len(ids) or card.count('class="card-link"') != len(ids):
            errors += _fail(f"{name} card count")
        if REL not in card or 'target="_blank"' not in card or 'data-placement="klook:test"' not in card:
            errors += _fail(f"{name} rel, target, or placement")
        if "affiliate-disclosure.html" not in card:
            errors += _fail(f"{name} missing disclosure")
        if re.search(r"\$\d|\b[0-5]\.\d\b", card):
            errors += _fail(f"{name} invented a rating or price: {card}")
        if "viator.com" in card or "<img" in card:
            errors += _fail(f"{name} mixed in Viator or an image")
    root = pathlib.Path(__file__).resolve().parent.parent
    placed = {
        "index.html": affiliates.KLOOK_VISITOR,
        "this-weekend/index.html": affiliates.KLOOK_AHEAD,
        "plans/index.html": affiliates.KLOOK_AHEAD,
        "guides/nyc-holiday-nights.html": affiliates.KLOOK_AHEAD,
        "guides/nyc-new-years-eve.html": affiliates.KLOOK_AHEAD,
        "plans/nyc-dinner-cruises.html": affiliates.KLOOK_HARBOR,
        "plans/nyc-boat-party.html": affiliates.KLOOK_HARBOR,
        "plans/bachelor-party.html": affiliates.KLOOK_SHOW,
    }
    seen = []
    for path in sorted(root.rglob("*.html")):
        if "_build" in path.parts or ".git" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        found = [html.unescape(h) for h in re.findall(r'href="(https://affiliate\.klook\.com[^"]*)"', text)]
        if not found:
            continue
        seen.append(rel)
        for url in found:
            if not url.startswith(prefix) or url not in allowed:
                errors += _fail(f"{rel} klook href is not one of the six: {url}")
        if rel in placed:
            want = [affiliates.KLOOK_BY_ID[i]["url"] for i in placed[rel]]
            if found != want:
                errors += _fail(f"{rel} klook hrefs {found}")
            if 'data-partner="klook"' not in text or 'rel="sponsored nofollow noopener"' not in text:
                errors += _fail(f"{rel} klook card missing partner or rel")
            if "Affiliate disclosure." not in text:
                errors += _fail(f"{rel} klook card missing disclosure")
        else:
            errors += _fail(f"{rel} has a Klook link and was not a chosen page")
    missing = [rel for rel in placed if rel not in seen]
    if missing:
        errors += _fail("built pages missing Klook: " + ", ".join(missing))
    disclosure = (root / "affiliate-disclosure.html").read_text(encoding="utf-8")
    if "Klook" not in disclosure or "145278" not in disclosure or "Viator" not in disclosure or "P00330813" not in disclosure:
        errors += _fail("affiliate disclosure does not name Klook alongside Viator")
    redirect = root / "things-to-do" / "nyc-night-cruises-and-ferry-experiences.html"
    redir = redirect.read_text(encoding="utf-8")
    if "affiliate.klook.com" in redir or "noindex" not in redir:
        errors += _fail("night-cruise redirect should stay a noindex redirect; Harbor Lights belongs on the cruise guide")
    js = root.joinpath("analytics.js").read_text(encoding="utf-8")
    if 'AFFILIATE = ["viator.com", "affiliate.klook.com"]' not in js or "affiliate.placement" not in js or "affiliate.partner" not in js:
        errors += _fail("analytics.js does not record viator and klook partner and placement")
    if errors:
        print(f"{errors} failed")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
