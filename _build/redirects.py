"""Static redirects for URLs Google still requests after the Oct 2026 rebuild.

GitHub Pages has no server redirects. Each old path is a tiny HTML file:
noindex, a canonical link to the successor, a meta refresh, and location.replace.
Only paths with a clear successor are listed. Retired sections with no
replacement stay absent so the branded 404.html can answer them.
"""
import html
import json
import pathlib

SITE = "https://nynightlife.com"

# Old path (relative, index.html for a directory) -> new root-relative URL.
REDIRECTS = {
    # Borough, neighborhood, category, and ranking hubs the rebuild kept as stubs.
    "boroughs/index.html": "/venues/",
    "boroughs/bronx-nightlife.html": "/venues/",
    "boroughs/brooklyn-nightlife.html": "/venues/",
    "boroughs/manhattan-nightlife.html": "/venues/",
    "boroughs/queens-nightlife.html": "/venues/",
    "boroughs/staten-island-nightlife.html": "/venues/",
    "categories/index.html": "/venues/",
    "categories/best-nyc-bars.html": "/venues/",
    "categories/best-nyc-clubs.html": "/venues/",
    "categories/date-night-nyc-nightlife.html": "/venues/",
    "categories/edm-nightlife-nyc.html": "/venues/",
    "categories/hip-hop-nightlife-nyc.html": "/venues/",
    "categories/latin-nightlife-nyc.html": "/venues/",
    "categories/lgbtq-nightlife-nyc.html": "/venues/",
    "categories/live-music-nyc-nightlife.html": "/venues/",
    "neighborhoods/index.html": "/venues/",
    "neighborhoods/astoria-nightlife.html": "/venues/",
    "neighborhoods/bed-stuy-nightlife.html": "/venues/",
    "neighborhoods/bronx-nightlife-guide.html": "/venues/",
    "neighborhoods/bushwick-nightlife.html": "/venues/",
    "neighborhoods/chelsea-nightlife.html": "/venues/",
    "neighborhoods/cobble-hill-nightlife.html": "/venues/",
    "neighborhoods/crown-heights-nightlife.html": "/venues/",
    "neighborhoods/downtown-brooklyn-nightlife.html": "/venues/",
    "neighborhoods/dumbo-nightlife.html": "/venues/",
    "neighborhoods/east-village-nightlife.html": "/venues/",
    "neighborhoods/financial-district-nightlife.html": "/venues/",
    "neighborhoods/flushing-nightlife.html": "/venues/",
    "neighborhoods/forest-hills-nightlife.html": "/venues/",
    "neighborhoods/greenpoint-nightlife.html": "/venues/",
    "neighborhoods/harlem-nightlife.html": "/venues/",
    "neighborhoods/hells-kitchen-nightlife.html": "/venues/",
    "neighborhoods/jackson-heights-nightlife.html": "/venues/",
    "neighborhoods/long-island-city-nightlife.html": "/venues/",
    "neighborhoods/lower-east-side-nightlife.html": "/venues/",
    "neighborhoods/meatpacking-nightlife.html": "/venues/",
    "neighborhoods/midtown-nightlife.html": "/venues/",
    "neighborhoods/park-slope-nightlife.html": "/venues/",
    "neighborhoods/red-hook-nightlife.html": "/venues/",
    "neighborhoods/ridgewood-nightlife.html": "/venues/",
    "neighborhoods/soho-nightlife.html": "/venues/",
    "neighborhoods/staten-island-nightlife-guide.html": "/venues/",
    "neighborhoods/upper-east-side-nightlife.html": "/venues/",
    "neighborhoods/upper-west-side-nightlife.html": "/venues/",
    "neighborhoods/west-village-nightlife.html": "/venues/",
    "neighborhoods/williamsburg-nightlife.html": "/venues/",
    "rankings/index.html": "/venues/",
    "rankings/best-bars-in-nyc.html": "/venues/",
    "rankings/best-birthday-nightlife-nyc.html": "/venues/",
    "rankings/best-clubs-in-nyc.html": "/venues/",
    "rankings/best-edm-nights-nyc.html": "/venues/",
    "rankings/best-friday-night-spots-nyc.html": "/venues/",
    "rankings/best-hip-hop-nights-nyc.html": "/venues/",
    "rankings/best-late-night-food-near-clubs-nyc.html": "/venues/",
    "rankings/best-latin-nights-nyc.html": "/venues/",
    "rankings/best-nightlife-by-borough.html": "/venues/",
    "rankings/best-nightlife-under-50-nyc.html": "/venues/",
    "rankings/best-saturday-night-spots-nyc.html": "/venues/",
    "rankings/best-thursday-night-spots-nyc.html": "/venues/",
    "rankings/best-vip-experiences-nyc.html": "/venues/",
    "guides/bar-crawl-guide.html": "/venues/",
    "guides/best-nightlife-experiences.html": "/venues/",
    "guides/luxury-experiences-nyc.html": "/venues/",
    "guides/stay-near-nightlife.html": "/venues/",
    "guides/vip-club-access-nyc.html": "/venues/",
    "methodology/index.html": "/how-we-check.html",
    "methodology/editorial-policy.html": "/how-we-check.html",
    "methodology/how-we-rate-venues.html": "/how-we-check.html",
    "privacy-policy.html": "/privacy.html",
    "terms.html": "/about.html",
    "visitor-start-here.html": "/",
    # Stubs repointed once a real guide existed (PR #116 and this pass).
    "categories/rooftop-bars-nyc.html": "/guides/nyc-rooftop-bars.html",
    "categories/speakeasies-nyc.html": "/guides/nyc-speakeasies.html",
    "categories/comedy-nightlife-nyc.html": "/guides/nyc-comedy-clubs.html",
    "categories/after-hours-nyc.html": "/guides/nyc-bar-closing-time.html",
    "guides/index.html": "/guides/nyc-dress-codes.html",
    "guides/events-this-weekend.html": "/this-weekend/",
    "rankings/best-rooftops-in-nyc.html": "/guides/nyc-rooftop-bars.html",
    "rankings/best-bachelorette-nightlife-nyc.html": "/plans/bachelorette-night.html",
    # Deleted in the rebuild. These had no stub, so they 404 on the live site.
    "tonight/friday-night-nyc.html": "/tonight/",
    "tonight/saturday-night-nyc.html": "/tonight/",
    "tonight/things-to-do-in-nyc-tonight.html": "/tonight/",
    "weekend/index.html": "/this-weekend/",
    "weekend/nyc-nightlife-this-weekend.html": "/this-weekend/",
    "weekend/nyc-rooftop-weekend-guide.html": "/guides/nyc-rooftop-bars.html",
    "seasonal/new-years-eve-nyc-nightlife.html": "/guides/nyc-new-years-eve.html",
    "blog/rooftop-bars-manhattan.html": "/guides/nyc-rooftop-bars.html",
    "blog/getting-into-exclusive-clubs.html": "/guides/nyc-dress-codes.html",
    "blog/labor-day-weekend-2026-nyc-nightlife.html": "/this-weekend/",
    "things-to-do/nyc-night-cruises-and-ferry-experiences.html": "/plans/nyc-dinner-cruises.html",
}


def redirect_html(target):
    """noindex refresh page. Canonical points at the successor, not this URL."""
    if not target.startswith("/") or target.startswith("//"):
        raise SystemExit(f"redirect target must be a site path: {target}")
    quoted = html.escape(target, quote=True)
    canon = SITE + target
    js = json.dumps(target)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Moved | NY Nightlife</title>
<meta name="description" content="This page has moved.">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{html.escape(canon, quote=True)}">
<meta http-equiv="refresh" content="0; url={quoted}">
<meta name='impact-site-verification' value='59f0bf98-cda3-4aaf-9bd2-b750205147c8'>
<script>location.replace({js});</script>
</head>
<body>
<p>This page has moved: <a href="{quoted}">{html.escape(canon)}</a></p>
</body>
</html>
"""


def write_redirects(out):
    """Write every redirect. Refuse to replace a real article."""
    out = pathlib.Path(out)
    for rel, target in sorted(REDIRECTS.items()):
        dest = out / rel
        if dest.exists():
            old = dest.read_text(encoding="utf-8", errors="ignore")
            if 'http-equiv="refresh"' not in old and "<h1" in old.lower():
                raise SystemExit(f"refusing to overwrite a real page with a redirect: {rel}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(redirect_html(target), encoding="utf-8", newline="\n")
    return len(REDIRECTS)
