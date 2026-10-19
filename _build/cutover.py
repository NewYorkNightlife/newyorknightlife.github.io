"""One-time cutover (Oct 2026): retire the old site, keep its useful URLs as redirects.

Run from the site folder:  python _build/cutover.py
- git-removes retired sections (they stay in git history + the 2026-10-18 archive bundle)
- writes small redirect pages for old URLs that have a close new equivalent
- builds the new site into the root, then writes sitemap.xml and robots.txt
"""
import html
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT.parent
DOMAIN = "https://nynightlife.com"

# Old URL -> new URL (GitHub Pages has no server redirects, so these are refresh pages).
REDIRECT_DIRS = {"neighborhoods": "/venues/", "boroughs": "/venues/", "rankings": "/venues/",
                 "categories": "/venues/", "guides": "/venues/", "methodology": "/how-we-check.html"}
REDIRECT_FILES = {"privacy-policy.html": "/privacy.html", "terms.html": "/about.html",
                  "visitor-start-here.html": "/", "guides/index.html": "/guides/nyc-dress-codes.html"}
KEEP_IN_GUIDES = {"guides/nyc-dress-codes.html"}

RETIRE = ["blog", "tools", "things-to-do", "games", "visit-essentials", "visit", "scripts", "plan",
          "workflows", "transport", "tonight", "seasonal", "safety", "weekend", "ops", "ai", "venue-compare",
          "safe-late-night-transport", "night-planner", "docs", ".ops-logs", ".weekly-blog.lock",
          "ads.txt", "llms.txt", "css/chrome.css", "css/main.css", "css/revival.css", "js/main.js",
          "js/revival.js", "js/tonight-live.js", "data/tonight-feed.json", "sitemap.xml", "robots.txt"]


def git(*a):
    return subprocess.run(["git", *a], cwd=SITE, check=True, capture_output=True, text=True).stdout


def stub(target):
    t = html.escape(target)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Moved | NY Nightlife</title>
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{DOMAIN}{t}">
<meta http-equiv="refresh" content="0; url={t}">
</head><body><p>This page has moved: <a href="{t}">{DOMAIN}{t}</a></p></body></html>
"""


def main():
    tracked = set(git("ls-files").splitlines())
    redirects = dict(REDIRECT_FILES)
    for f in tracked:
        top = f.split("/")[0]
        if top in REDIRECT_DIRS and f.endswith(".html") and f not in KEEP_IN_GUIDES and f not in redirects:
            redirects[f] = REDIRECT_DIRS[top]
    removed = sorted(f for f in tracked if any(f == r or f.startswith(r + "/") for r in RETIRE))
    gone = sorted(set(removed) | {f for f in redirects if f in tracked})
    if gone:
        git("rm", "-r", "-q", "--", *gone)
    for f, target in sorted(redirects.items()):
        p = SITE / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(stub(target), encoding="utf-8", newline="\n")

    subprocess.run([sys.executable, str(ROOT / "build.py")], cwd=SITE, check=True)

    pages = []
    for p in sorted(SITE.rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        if rel.startswith(("_build/", "next/", "assets/")) or rel in redirects or rel == "404.html":
            continue
        url = "/" + rel
        if url.endswith("/index.html"):
            url = url[: -len("index.html")]
        pages.append(url)
    sm = "".join(f"<url><loc>{DOMAIN}{u}</loc><lastmod>2026-10-18</lastmod></url>\n" for u in pages)
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + sm + "</urlset>\n", encoding="utf-8", newline="\n")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8", newline="\n")

    (SITE / "_build" / "REMOVED-2026-10.txt").write_text(
        "Removed in the Oct 2026 rebuild (restore from git history or archive\\2026-10-18-pre-rebuild):\n"
        + "\n".join(removed) + "\n\nRedirected (old URL -> new):\n"
        + "\n".join(f"{k} -> {v}" for k, v in sorted(redirects.items())) + "\n", encoding="utf-8", newline="\n")
    print(f"removed {len(removed)} files, {len(redirects)} redirects, sitemap {len(pages)} pages")


if __name__ == "__main__":
    main()
