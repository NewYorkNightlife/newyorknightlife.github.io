"""Honest page dates for sitemap lastmod, JSON-LD dateModified, and visible Updated lines.

A date is the newest of:
  - the last git commit (America/New_York) that touched that page's content
    inputs: its data files, photographs, and the template function that writes
    the body
  - for pages rebuilt from the live event feed, the New York date on which the
    rendered listings actually changed

The same-day rebuild of an unchanged feed keeps the previous date. A lastmod
is never "today" just because the build ran. Checked-fact dates (the day a
door fact was verified) stay in the copy; they are not lastmod.

The ledger (_build/data/freshness.json) remembers the content hash and the
date it last changed. Daily build restores a newer copy from the Actions
cache when one exists, because that job does not commit. Checkout must be
full history (fetch-depth: 0); a shallow clone cannot see these dates.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
LEDGER = ROOT / "data" / "freshness.json"
SITE = "https://nynightlife.com"
try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
except Exception:
    NY = dt.timezone(dt.timedelta(hours=-5))

PAGE_TYPES = {"WebPage", "Article", "CollectionPage", "WebSite"}
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_GIT_ISO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})")
_CACHE: dict = {}


def today_ny() -> str:
    return dt.datetime.now(NY).date().isoformat()


def _ny_day(iso: str) -> str:
    text = iso.strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(NY).date().isoformat()


def _git(*args: str) -> str:
    key = args
    if key in _CACHE:
        return _CACHE[key]
    proc = subprocess.run(
        ["git", *args], cwd=REPO, text=True, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        _CACHE[key] = ""
        _CACHE[("err",) + args] = (proc.stderr or proc.stdout or "").strip()
        return ""
    _CACHE[key] = proc.stdout
    return proc.stdout


def assert_full_history() -> None:
    shallow = _git("rev-parse", "--is-shallow-repository").strip()
    if shallow == "true":
        raise SystemExit(
            "freshness: this checkout is shallow, so commit dates would be wrong. "
            "GitHub Actions must checkout with fetch-depth: 0."
        )
    if not _git("rev-parse", "--is-inside-work-tree").strip() == "true":
        raise SystemExit("freshness: not a git checkout; refusing to invent lastmod dates")


def _date_from_git_output(text: str) -> str | None:
    """Use only the first line. `git log -L` prints a diff after the format,
    and that diff can contain older timestamps."""
    first = ""
    for line in (text or "").splitlines():
        if line.strip():
            first = line.strip()
            break
    match = _GIT_ISO.fullmatch(first)
    if not match:
        return None
    return _ny_day(match.group(0))


def git_date_for_paths(paths: list[str]) -> str | None:
    existing = [p for p in paths if (REPO / p).is_file()]
    if not existing:
        return None
    text = _git("log", "-1", "--format=%cI", "--", *existing)
    return _date_from_git_output(text)


def git_date_for_range(rel: str, start: int, end: int) -> str | None:
    if end < start:
        end = start
    text = _git("log", "-1", "--format=%cI", "-L", f"{start},{end}:{rel}")
    found = _date_from_git_output(text)
    if found:
        return found
    err = _CACHE.get(("err", "log", "-1", "--format=%cI", "-L", f"{start},{end}:{rel}"), "")
    raise SystemExit(f"freshness: no commit date for {rel}:{start}-{end}. {err}")


def _lines(rel: str) -> list[str]:
    return (REPO / rel).read_text(encoding="utf-8").splitlines()


def function_range(rel: str, name: str) -> tuple[int, int]:
    lines = _lines(rel)
    start = None
    for i, line in enumerate(lines):
        if line.startswith(f"def {name}("):
            start = i + 1
            break
    if start is None:
        raise SystemExit(f"freshness: def {name} is not in {rel}")
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("def ") or lines[j].startswith("class "):
            end = j
            break
    return start, end


def call_span(rel: str, needle: str) -> tuple[str, int, int]:
    """Lines of one simple() call, so a privacy edit does not date About
    and the 404 markup after Contact does not date Contact."""
    lines = _lines(rel)
    start = None
    for i, line in enumerate(lines):
        if needle in line:
            start = i + 1
            break
    if start is None:
        raise SystemExit(f"freshness: {needle!r} not found in {rel}")
    end = start
    for j in range(start - 1, len(lines)):
        if '""")' in lines[j]:
            end = j + 1
            break
    return rel, start, end


def _files_named_in(rel: str, name: str) -> list[str]:
    start, end = function_range(rel, name)
    text = "\n".join(_lines(rel)[start - 1:end])
    slugs = set(re.findall(r"/venues/([a-z0-9-]+)\.html", text))
    slugs.update(re.findall(r'photo="([a-z0-9-]+)"', text))
    slugs.update(re.findall(r'picture\(\s*"([a-z0-9-]+)"', text))
    # Slug tuples ("attaboy", "le-bain") are data inputs even when the href is built later.
    for token in re.findall(r'"([a-z0-9-]+)"', text):
        if ((ROOT / "data" / "venues" / f"{token}.json").is_file()
                or (ROOT / "img" / f"{token}.jpg").is_file()):
            slugs.add(token)
    out = []
    for slug in sorted(slugs):
        for rel_path in (f"_build/data/venues/{slug}.json", f"_build/img/{slug}.jpg"):
            if (REPO / rel_path).is_file():
                out.append(rel_path)
    return out


def _all_venue_files() -> list[str]:
    files = [f"_build/data/venues/{p.name}" for p in sorted((ROOT / "data" / "venues").glob("*.json"))]
    files += [f"_build/img/{p.name}" for p in sorted((ROOT / "img").glob("*.jpg"))
              if (ROOT / "data" / "venues" / f"{p.stem}.json").is_file()]
    return files


def inputs_for(path: str) -> list:
    """Content inputs for one sitemap URL. The shared document shell (scripts,
    analytics, cache-bust query strings) is not an input: a voice-script hash
    change is not a content change."""
    specs: list = []

    def fn(rel: str, name: str) -> None:
        start, end = function_range(rel, name)
        specs.append((rel, start, end))

    def files(paths: list[str]) -> None:
        specs.append(tuple(paths))

    if path.startswith("/venues/") and path.endswith(".html"):
        slug = path.rsplit("/", 1)[1][:-5]
        files([f"_build/data/venues/{slug}.json", f"_build/img/{slug}.jpg"])
        fn("_build/build.py", "venue_page")
        fn("_build/build.py", "plate")
        fn("_build/extras.py", "week_table")
        return specs

    if path == "/venues/":
        files(_all_venue_files())
        fn("_build/build.py", "venues_index")
        fn("_build/build.py", "vcard")
        fn("_build/build.py", "poster_card")
        return specs

    if path == "/":
        fn("_build/pages.py", "home")
        fn("_build/night_map.py", "markup")
        fn("_build/present.py", "events_html")
        files(["_build/img/home.jpg", "_build/data/boroughs.geojson", "_build/data/venue_geo.json"])
        import pages
        featured = []
        for slug in pages.FEATURED:
            featured += [f"_build/data/venues/{slug}.json", f"_build/img/{slug}.jpg"]
        files(featured)
        return specs

    if path in ("/tonight/", "/this-weekend/"):
        fn("_build/extras.py", "tonight_page" if path == "/tonight/" else "weekend_page")
        fn("_build/present.py", "events_html")
        fn("_build/extras.py", "late_posters" if path == "/tonight/" else "weekend_late")
        files(_all_venue_files())
        return specs

    guides = {
        "/guides/nyc-dress-codes.html": ("_build/build.py", "dress_hub", True),
        "/guides/under-21-nyc-bars-clubs.html": ("_build/extras.py", "guide_under21", True),
        "/guides/nyc-bar-closing-time.html": ("_build/extras.py", "guide_closing", True),
        "/guides/nyc-speakeasies.html": ("_build/pages.py", "speakeasies", False),
        "/guides/nyc-rooftop-bars.html": ("_build/pages.py", "rooftop_bars", False),
        "/guides/nyc-comedy-clubs.html": ("_build/pages.py", "comedy_clubs", False),
        "/guides/nyc-new-years-eve.html": ("_build/pages.py", "new_years_eve", False),
        "/guides/nyc-holiday-nights.html": ("_build/pages.py", "holiday_nights", False),
        "/plans/nyc-dinner-cruises.html": ("_build/pages.py", "cruise_guide", False),
        "/plans/nyc-boat-party.html": ("_build/pages.py", "boat_party", False),
        "/plans/bachelor-party.html": ("_build/pages.py", "bachelor_party", False),
        "/plans/": ("_build/pages.py", "plans_hub", False),
        "/image-credits.html": ("_build/pages.py", "image_credits", True),
    }
    if path in guides:
        rel, name, every = guides[path]
        fn(rel, name)
        fn("_build/present.py", "guide_hero")
        if every:
            files(_all_venue_files())
            if path == "/image-credits.html" and (ROOT / "data" / "place_photos.json").is_file():
                files(["_build/data/place_photos.json"])
        else:
            files(_files_named_in(rel, name))
        return specs

    if path.startswith("/plans/") and path.endswith(".html"):
        slug = path.rsplit("/", 1)[1][:-5]
        fn("_build/pages.py", "playbook")
        fn("_build/present.py", "guide_hero")
        named = [f"_build/data/playbooks/{slug}.json", f"_build/img/{slug}.jpg"]
        files(named)
        return specs

    trust = {
        "/about.html": '"/about.html"',
        "/how-we-check.html": '"/how-we-check.html"',
        "/affiliate-disclosure.html": '"/affiliate-disclosure.html"',
        "/privacy.html": '"/privacy.html"',
        "/contact.html": '"/contact.html"',
    }
    if path in trust:
        specs.append(call_span("_build/pages.py", trust[path]))
        return specs

    if path == "/changes/":
        fn("_build/extras.py", "changes_pages")
        files(["_build/data/changes.json", "_build/data/facts-snapshot.json"])
        return specs

    raise SystemExit(f"freshness: no content inputs declared for {path}")


def git_date(path: str) -> str:
    dates = []
    for spec in inputs_for(path):
        if isinstance(spec, tuple) and len(spec) == 3 and isinstance(spec[1], int):
            dates.append(git_date_for_range(spec[0], spec[1], spec[2]))
        else:
            paths = list(spec) if isinstance(spec, tuple) else [spec]
            found = git_date_for_paths(paths)
            if found:
                dates.append(found)
    dates = [d for d in dates if d]
    if not dates:
        raise SystemExit(f"freshness: no git date for {path}")
    return max(dates)


def content_hash(html: str) -> str:
    text = html
    text = re.sub(r"\?v=[0-9a-fA-F]+", "", text)
    text = re.sub(r'"dateModified"\s*:\s*"[^"]*"', '"dateModified":""', text)
    # A WebPage node that exists only to carry dateModified is not content.
    text = re.sub(
        r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "WebPage", "url": "https://nynightlife\.com[^"]*", "dateModified": ""\}</script>\n?',
        "", text)
    text = re.sub(
        r'<p class="fresh">Updated <time datetime="[^"]*">[^<]*</time></p>',
        "", text)
    text = re.sub(
        r'<p class="updated"[^>]*data-feed-updated="[^"]*"[^>]*>.*?</p>',
        "", text, flags=re.S)
    text = re.sub(
        r'<p class="updated"[^>]*>Updated \d{4}-\d{2}-\d{2}</p>',
        "", text)
    text = re.sub(
        r'<p class="hero-live"[^>]*>.*?</p>',
        "", text, flags=re.S)
    text = re.sub(r"Feed checked \d{4}-\d{2}-\d{2}", "Feed checked", text)
    text = re.sub(r"(<p class=\"eyebrow\">[^<]*?updated )[A-Z][a-z]{2} \d{1,2}, \d{4}",
                  r"\1", text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest


def html_file(out: pathlib.Path, path: str) -> pathlib.Path:
    rel = path.strip("/")
    if path == "/" or path.endswith("/"):
        return (out / rel / "index.html") if rel else (out / "index.html")
    return out / rel


def load_ledger() -> dict:
    if not LEDGER.is_file():
        return {}
    try:
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    pages = data.get("pages") if isinstance(data, dict) else None
    return pages if isinstance(pages, dict) else {}


def save_ledger(pages: dict) -> None:
    body = {"version": 1, "pages": {k: pages[k] for k in sorted(pages)}}
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(body, indent=1) + "\n", encoding="utf-8", newline="\n")


def _fmt(iso: str) -> str:
    year, month, day = iso.split("-")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[int(month) - 1]} {int(day)}, {year}"


def head_hash(out: pathlib.Path, path: str) -> str | None:
    """Hash of the page committed at HEAD, or None if that path is new."""
    file = html_file(out, path)
    try:
        rel = file.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return None
    proc = subprocess.run(
        ["git", "show", f"HEAD:{rel}"], cwd=REPO, capture_output=True, check=False,
    )
    if proc.returncode != 0 or not proc.stdout:
        return None
    return content_hash(proc.stdout.decode("utf-8", errors="replace"))


def resolve(path: str, html: str, previous: dict, out: pathlib.Path) -> tuple[str, str]:
    """Return (lastmod, content hash).

    A missing ledger entry is a seed: the date is the git date. If that render
    already differs from the HTML committed at HEAD, the difference was observed
    in this build, so the date is today (still never earlier than the git date).
    """
    digest = content_hash(html)
    git_day = git_date(path)
    prev = previous.get(path) if isinstance(previous.get(path), dict) else None
    if prev and prev.get("hash") == digest and _DATE.fullmatch(str(prev.get("lastmod") or "")):
        last = max(git_day, prev["lastmod"])
        return last, digest
    if prev is None:
        old = head_hash(out, path)
        if old and old != digest:
            return max(git_day, today_ny()), digest
        return git_day, digest
    # The rendered body changed. Git names the commit when an input moved.
    # Otherwise this build is the first time we saw the new listings.
    if git_day > str(prev.get("lastmod") or ""):
        return git_day, digest
    return max(git_day, today_ny()), digest


def patch_html(html: str, path: str, lastmod: str) -> str:
    found = False

    def repl_script(match: re.Match) -> str:
        nonlocal found
        raw = match.group(1)
        if found:
            return match.group(0)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return match.group(0)
        items = data if isinstance(data, list) else [data]
        if not any(isinstance(item, dict) and item.get("@type") in PAGE_TYPES for item in items):
            return match.group(0)
        found = True
        if re.search(r'"dateModified"\s*:', raw):
            raw = re.sub(r'"dateModified"\s*:\s*"[^"]*"', f'"dateModified": "{lastmod}"', raw, count=1)
        else:
            raw = re.sub(
                r'("@type"\s*:\s*"(?:WebPage|Article|CollectionPage|WebSite)")',
                rf'\1, "dateModified": "{lastmod}"', raw, count=1)
        return f'<script type="application/ld+json">{raw}</script>'

    html = re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl_script, html, flags=re.S)
    if not found:
        block = (
            '<script type="application/ld+json">'
            + json.dumps({
                "@context": "https://schema.org", "@type": "WebPage",
                "url": SITE + path, "dateModified": lastmod,
            }, ensure_ascii=False)
            + "</script>\n"
        )
        html = html.replace("</head>", block + "</head>", 1)

    html = re.sub(
        r'(<p class="fresh">Updated <time datetime=")[^"]*(">)[^<]*(</time></p>)',
        rf"\g<1>{lastmod}\g<2>{lastmod}\g<3>", html, count=1)
    html = re.sub(
        r'(<p class="eyebrow">[^<]*?updated )[A-Z][a-z]{2} \d{1,2}, \d{4}',
        rf"\g<1>{_fmt(lastmod)}", html, count=1)

    def repl_updated(match: re.Match) -> str:
        open_tag, body, close = match.group(1), match.group(2), match.group(3)
        if "data-feed-updated" in open_tag:
            return match.group(0)
        if re.fullmatch(r"Updated \d{4}-\d{2}-\d{2}", body.strip()):
            return f"{open_tag}Updated {lastmod}{close}"
        return match.group(0)

    html = re.sub(r'(<p class="updated"[^>]*>)(.*?)(</p>)', repl_updated, html, count=1, flags=re.S)

    needs_visible = path.startswith("/guides/") or path.startswith("/plans/")
    has_fresh = 'class="fresh"' in html
    has_iso = re.search(r'<p class="updated"(?![^>]*data-feed-updated)[^>]*>Updated \d{4}-\d{2}-\d{2}</p>', html)
    if needs_visible and not has_fresh and not has_iso:
        line = f'<p class="fresh">Updated <time datetime="{lastmod}">{lastmod}</time></p>\n'
        html = html.replace('<main class="wrap">\n', '<main class="wrap">\n' + line, 1)
    elif not needs_visible and not has_fresh and not has_iso and "data-feed-updated" not in html:
        line = f'<p class="updated">Updated {lastmod}</p>\n'
        html = html.replace('<main class="wrap">\n', '<main class="wrap">\n' + line, 1)
    return html


def publish(out: pathlib.Path, paths: list[str]) -> dict[str, str]:
    """Patch each page's dates and write sitemap.xml. Returns path -> lastmod."""
    assert_full_history()
    previous = load_ledger()
    # A same-day rebuild must see the ledger from the previous run even when
    # this checkout's committed copy is older. NYN_FRESHNESS_LEDGER is set by
    # nothing in the repo; the Actions cache restores the file in place.
    dates: dict[str, str] = {}
    pages = {}
    for path in paths:
        if path in dates:
            continue
        file = html_file(out, path)
        if not file.is_file():
            raise SystemExit(f"freshness: {path} has no file at {file}")
        html = file.read_text(encoding="utf-8")
        lastmod, digest = resolve(path, html, previous, out)
        if not _DATE.fullmatch(lastmod):
            raise SystemExit(f"freshness: {path} lastmod {lastmod!r} is not YYYY-MM-DD")
        patched = patch_html(html, path, lastmod)
        if patched != html:
            file.write_text(patched, encoding="utf-8", newline="\n")
        dates[path] = lastmod
        pages[path] = {"hash": digest, "lastmod": lastmod}
    body = "".join(
        f"<url><loc>{SITE}{path}</loc><lastmod>{dates[path]}</lastmod></url>\n"
        for path in sorted(dates))
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + body + "</urlset>\n",
        encoding="utf-8", newline="\n")
    if os.environ.get("NYN_FRESHNESS_LEDGER", "1") != "0":
        save_ledger(pages)
    return dates


def _page_dates(html: str) -> list[str]:
    found = []
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") in PAGE_TYPES and item.get("dateModified"):
                found.append(str(item["dateModified"]))
    return found


def _visible_dates(html: str) -> list[str]:
    dates = [m.group(1) for m in re.finditer(
        r'<p class="fresh">Updated <time datetime="(\d{4}-\d{2}-\d{2})">\1</time></p>', html)]
    dates += [m.group(1) for m in re.finditer(
        r'<p class="updated"(?![^>]*data-feed-updated)[^>]*>Updated (\d{4}-\d{2}-\d{2})</p>', html)]
    return dates


def problems(root: pathlib.Path) -> list[str]:
    """Fail the build when lastmod is older than the inputs, or the page disagrees."""
    root = pathlib.Path(root)
    sm_path = root / "sitemap.xml"
    if not sm_path.is_file():
        return ["sitemap.xml is missing"]
    try:
        assert_full_history()
    except SystemExit as exc:
        return [str(exc)]
    text = sm_path.read_text(encoding="utf-8")
    rows = re.findall(
        r"<loc>\s*https://nynightlife\.com([^<]*?)\s*</loc>\s*<lastmod>\s*(\d{4}-\d{2}-\d{2})\s*</lastmod>",
        text)
    if not rows:
        return ["sitemap.xml has no lastmod dates to check"]
    out = []
    for loc, lastmod in rows:
        path = loc or "/"
        if not path.startswith("/"):
            path = "/" + path
        try:
            git_day = git_date(path)
        except SystemExit as exc:
            out.append(str(exc))
            continue
        if lastmod < git_day:
            out.append(f"sitemap {path} lastmod {lastmod} is older than git {git_day}")
        file = html_file(root, path)
        if not file.is_file():
            continue
        html = file.read_text(encoding="utf-8")
        modified = _page_dates(html)
        if not modified:
            out.append(f"{path} has no dateModified")
        elif any(item != lastmod for item in modified):
            out.append(f"{path} dateModified {modified} disagrees with sitemap lastmod {lastmod}")
        visible = _visible_dates(html)
        if any(item != lastmod for item in visible):
            out.append(f"{path} visible Updated {visible} disagrees with sitemap lastmod {lastmod}")
        if (path.startswith("/guides/") or path.startswith("/plans/")) and lastmod not in visible:
            out.append(f"{path} is missing a visible Updated {lastmod}")
    return out
