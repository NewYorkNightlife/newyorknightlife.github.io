"""Viator affiliate links approved 2026-11-09 (partner P00330813, mcid 42383).

Ratings, review counts and prices are copied from that list. Search links have
none, and this module never invents them.
"""
import html
import urllib.parse

e = html.escape

PID = "P00330813"
MCID = "42383"
PARTNER = "viator"

# Slugs whose own checked facts describe a speakeasy or a hidden-door bar.
# SpeakeasyGo (a ticketing site) does not count.
SPEAKEASY_SLUGS = ("employees-only", "the-back-room", "please-dont-tell")
# Closest checked venue to a drag night: costumes, "dress to express", cabaret tables.
DRAG_SLUGS = ("house-of-yes",)

OFFERS = (
    {
        "id": "night-tours",
        "title": "NYC night tours",
        "go": "See tours",
        "url": "https://www.viator.com/searchResults/all?text=New+York+City+night+tours",
    },
    {
        "id": "sunset-yacht",
        "title": "Sunset cocktail cruise",
        "detail": "Small yacht",
        "rating": "4.9",
        "reviews": "105",
        "from_price": "$86",
        "go": "Book",
        "url": "https://www.viator.com/tours/New-York-City/New-York-City-Sunset-Cruise-on-small-yacht/d687-6288P50",
    },
    {
        "id": "sunset-dinner",
        "title": "Sunset and dinner cruises",
        "go": "See cruises",
        "url": "https://www.viator.com/searchResults/all?text=New+York+City+sunset+dinner+cruise",
    },
    {
        "id": "sunset-cruise",
        "title": "Sunset cruises",
        "go": "See cruises",
        "url": "https://www.viator.com/searchResults/all?text=New+York+City+sunset+cruise",
    },
    {
        "id": "dinner-cruise",
        "title": "Dinner cruises",
        "go": "See cruises",
        "url": "https://www.viator.com/searchResults/all?text=New+York+City+dinner+cruise",
    },
    {
        "id": "jazz-brunch",
        "title": "Jazz and brunch cruises",
        "go": "See cruises",
        "url": "https://www.viator.com/searchResults/all?text=New+York+City+jazz+brunch+cruise",
    },
    {
        "id": "bar-crawls",
        "title": "NYC bar crawls",
        "go": "See crawls",
        "url": "https://www.viator.com/searchResults/all?text=NYC+bar+crawl",
    },
    {
        "id": "comedy",
        "title": "Comedy shows",
        "go": "See shows",
        "url": "https://www.viator.com/searchResults/all?text=New+York+City+comedy+show+tickets",
    },
    {
        "id": "rooftop-speakeasy",
        "title": "Rooftop and speakeasy tours",
        "go": "See tours",
        "url": "https://www.viator.com/searchResults/all?text=New+York+City+rooftop+tour+speakeasy+tour",
    },
    {
        "id": "drag",
        "title": "Drag bar crawl",
        "detail": "Fabulous Drag Night",
        "rating": "4.9",
        "reviews": "22",
        "from_price": "$49",
        "go": "Book",
        "url": "https://www.viator.com/tours/New-York-City/Fabulous-Drag-Night/d687-247404P1",
    },
    {
        "id": "nye",
        "title": "NYE cruises",
        "go": "See cruises",
        "url": "https://www.viator.com/searchResults/all?text=NYC+New+Years+Eve+cruise+open+bar+fireworks",
    },
)
BY_ID = {o["id"]: o for o in OFFERS}

HOME = ("sunset-yacht", "sunset-dinner", "night-tours", "bar-crawls", "comedy", "rooftop-speakeasy", "drag", "nye")
TONIGHT = ("night-tours", "bar-crawls", "comedy")
BACH = ("sunset-yacht", "sunset-dinner")
# Search links only. The priced yacht product stays on home and the bachelorette page.
CRUISES = ("sunset-cruise", "dinner-cruise", "nye", "jazz-brunch")

# Open venues that had no affiliate card. One existing search link each.
# (offer id, placement prefix). Campaign is nynightlife-<slug>.
# Hidden-door and cocktail rooms → the speakeasy/rooftop tour search.
# Le Bain is a rooftop club. Dead Rabbit is a FiDi cocktail bar → bar crawl.
# Clubs, listening rooms, and ticketed halls → night tours.
# Comedy and the priced yacht/drag products are not used here: none of these
# pages are a comedy club or that specific tour.
EXTRA_VENUE = {
    "attaboy": ("rooftop-speakeasy", "speakeasy"),
    "beauty-and-essex": ("rooftop-speakeasy", "speakeasy"),
    "death-and-co": ("rooftop-speakeasy", "speakeasy"),
    "the-dead-rabbit": ("bar-crawls", "crawl"),
    "le-bain": ("rooftop-speakeasy", "rooftop"),
    "bossa-nova-civic-club": ("night-tours", "night"),
    "elsewhere": ("night-tours", "night"),
    "good-room": ("night-tours", "night"),
    "knockdown-center": ("night-tours", "night"),
    "marquee-new-york": ("night-tours", "night"),
    "musica-club": ("night-tours", "night"),
    "nebula": ("night-tours", "night"),
    "nowadays": ("night-tours", "night"),
    "pacha-new-york": ("night-tours", "night"),
    "paragon": ("night-tours", "night"),
    "public-records": ("night-tours", "night"),
    "the-box": ("night-tours", "night"),
}

NOTE = "We may earn a commission when you book through these links, at no extra cost to you."
NOTE_ONE = "We may earn a commission when you book through this link, at no extra cost to you."


def href(offer, campaign):
    parts = urllib.parse.urlsplit(offer["url"])
    kept = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
            if k not in ("pid", "mcid", "medium", "campaign")]
    query = urllib.parse.urlencode(kept + [
        ("pid", PID), ("mcid", MCID), ("medium", "link"), ("campaign", campaign)])
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def _sub(offer):
    bits = []
    if offer.get("detail"):
        bits.append(offer["detail"])
    if offer.get("rating"):
        bits.append(f'{offer["rating"]} · {offer["reviews"]} reviews · from {offer["from_price"]}')
    return " · ".join(bits) if bits else "Viator"


def _card(offer, campaign, placement):
    return (
        f'<a class="card-link" href="{e(href(offer, campaign))}" '
        f'rel="sponsored nofollow noopener" target="_blank" '
        f'data-partner="{PARTNER}" data-placement="{e(placement)}" data-track="{e(offer["title"])}">'
        f'<span>{e(offer["title"])}<span class="sub">{e(_sub(offer))}</span></span>'
        f'<span class="go">{e(offer["go"])} →</span></a>'
    )


def block(ids, campaign, placement, u, heading=None, note=None, heading_id=None):
    """A compact group of existing card-links, plus the FTC line."""
    links = "".join(_card(BY_ID[i], campaign, placement) for i in ids)
    if heading:
        hid = f' id="{e(heading_id)}"' if heading_id else ""
        h = f"<h2{hid}>{e(heading)}</h2>"
    else:
        h = ""
    cls = "book-grid" if len(ids) > 1 else "book-one"
    line = note or (NOTE if len(ids) > 1 else NOTE_ONE)
    return (
        f'{h}<div class="{cls}">{links}</div>'
        f'<p class="aff-note">{line} <a href="{u("/affiliate-disclosure.html")}">Affiliate disclosure.</a></p>'
    )


def venue_block(v, u):
    """One related Viator card on a venue page, or nothing."""
    if v.get("status") == "closed":
        return ""
    slug = v["slug"]
    if v.get("type") == "rooftop bar":
        return block(("rooftop-speakeasy",), "nynightlife-rooftop", f"rooftop:{slug}", u)
    if slug in SPEAKEASY_SLUGS:
        return block(("rooftop-speakeasy",), "nynightlife-speakeasy", f"speakeasy:{slug}", u)
    if slug in DRAG_SLUGS:
        return block(("drag",), "nynightlife-drag", f"drag:{slug}", u)
    extra = EXTRA_VENUE.get(slug)
    if extra:
        offer, kind = extra
        return block((offer,), f"nynightlife-{slug}", f"{kind}:{slug}", u)
    return ""
