"""Affiliate markup: real Viator facts only, sponsored rel, placement campaigns.

Run: python _build/test_affiliates.py
"""
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
    closed = affiliates.venue_block({"slug": "mr-purple", "type": "rooftop bar", "status": "closed"}, u)
    if plain or closed:
        errors += _fail("unexpected venue card")
    js = pathlib.Path(__file__).resolve().parent.parent.joinpath("analytics.js").read_text(encoding="utf-8")
    if 'AFFILIATE = ["viator.com"]' not in js or "affiliate.placement" not in js or "affiliate.partner" not in js:
        errors += _fail("analytics.js does not record viator partner and placement")
    if errors:
        print(f"{errors} failed")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
