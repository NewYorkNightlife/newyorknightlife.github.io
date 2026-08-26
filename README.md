# NYNightlife.com

**Decide your NYC night in 5 minutes.**

A fast, honest, always-current guide to New York City nightlife — real prices, real door policies,
and honest downsides. Static HTML on GitHub Pages.

![Status](https://img.shields.io/badge/status-live-green)
![License](https://img.shields.io/badge/license-private-red)

**Live site:** https://nynightlife.com

---

## What this is

NYNightlife.com is a **decision-layer utility with an editorial layer**. Most NYC nightlife coverage
is article-shaped: listicles that go stale the week they publish. This site is built around
structured, dated, verifiable facts — what a night will actually cost, whether you'll get in, and
what's genuinely worth it — with deep editorial guides alongside.

**The editorial stance is the product:**

- Every venue fact carries a visible `Last verified: YYYY-MM-DD` stamp and a source.
- We name real prices and real downsides. "Skip it: $40 cover for a dead room" is the point.
- No pay-to-play, no fake scarcity, no fabricated facts. Unverifiable means unpublished.

Full strategy lives outside this repo in `CONTENT-OPERATING-PLAN.md`. The binding editorial rules
are in [docs/EDITORIAL-TRUTH-POLICY.md](docs/EDITORIAL-TRUTH-POLICY.md).

## Site contents

*Counts verified 2026-08-26.*

| Section | Count | What it is |
|---|---:|---|
| `venues/` | 30 | **The Venue Fact Base** — cover charges, dress codes, door reality, verification stamps. The moat. |
| `neighborhoods/` | 30 | Nightlife by neighborhood, Manhattan through Queens |
| `rankings/` | 15 | Ranked "best of" pages with `ItemList` schema matching visible order |
| `tools/` | 14 | Working vanilla-JS utilities — cover calculator, dress checker, night planners, trip-cost calculator |
| `categories/` | 12 | Rooftops, speakeasies, LGBTQ+, live music, Latin, EDM, after-hours, and more |
| `games/` | 10 | Playable nightlife games (trivia, secret-spot hunt, quizzes) |
| `guides/` | 6 | Long-form pillar guides |
| **Total pages** | **262** | 196 in `sitemap.xml`; 57 archived weekly briefs are intentionally `noindex` |

Plus `tonight/` (daily automated feed), `weekend/`, `boroughs/`, `seasonal/`, `plan/`, `visit/`,
`visit-essentials/`, `things-to-do/`, `transport/`, `safety/`, `blog/`, and `methodology/`.

## How it's built

- **Static HTML5 + CSS3 + vanilla ES6 JavaScript.** No framework, no build step, no database,
  no server-side code.
- **GitHub Pages** hosting with automatic HTTPS and a global CDN. `CNAME` points at nynightlife.com.
- **Shared chrome** on every page: unified header/nav/footer, `css/chrome.css` + `css/main.css`,
  and the Nyla concierge widget (`js/concierge.js`).
- **Structured data** on every content page: `Article` + `FAQPage` JSON-LD matching visible content,
  `ItemList` on ranked pages, `LocalBusiness`/`NightClub`/`BarOrPub` on venue pages.

### The tonight feed (automated)

An n8n workflow commits `data/tonight-feed.json` to `main` on an hourly cycle, which `/tonight/`
renders client-side.

> **Do not hand-edit `data/`, the feed logic in `js/`, or `.ops-logs/`.** The automation owns those
> paths and pushes frequently. Always `git pull --rebase --autostash origin main` before pushing.

### Local development

```bash
git clone git@github.com:NewYorkNightlife/newyorknightlife.github.io.git
cd newyorknightlife.github.io
python -m http.server 8000
```

Then open http://localhost:8000. There is no build step — what's in the repo is what ships.

> **Everything committed here is published publicly**, including Markdown. `docs/` and `ops/` are
> reader-reachable. Never commit secrets, credentials, or private planning notes.

## Documentation

**Start here:**

1. [docs/EDITORIAL-TRUTH-POLICY.md](docs/EDITORIAL-TRUTH-POLICY.md) — the non-negotiable factual publishing rules
2. [docs/CONTENT-STANDARDS.md](docs/CONTENT-STANDARDS.md) — page templates + publishing QA
3. [docs/SITE-ARCHITECTURE.md](docs/SITE-ARCHITECTURE.md) — how the site is put together
4. [docs/SCHEMA-STANDARDS.md](docs/SCHEMA-STANDARDS.md) — structured-data rules
5. [docs/INTERNAL-LINKING.md](docs/INTERNAL-LINKING.md) — linking requirements

**Content and editorial:** [BLOG_HARD_RULES.md](docs/BLOG_HARD_RULES.md) ·
[WEEKLY-BLOG-WORKFLOW.md](docs/WEEKLY-BLOG-WORKFLOW.md) ·
[NEIGHBORHOOD_PAGE_TEMPLATE.md](docs/NEIGHBORHOOD_PAGE_TEMPLATE.md) ·
[CONTENT-BASELINE-PASS.md](docs/CONTENT-BASELINE-PASS.md) ·
[CHANGE_REVIEW_CHECKLIST.md](docs/CHANGE_REVIEW_CHECKLIST.md)

**Monetization:** [MONETIZATION.md](docs/MONETIZATION.md) · [AFFILIATE-OPS.md](docs/AFFILIATE-OPS.md) ·
[AFFILIATE-MODULE.md](docs/AFFILIATE-MODULE.md) ·
[AFFILIATE-APPLICATION-RUNBOOK.md](docs/AFFILIATE-APPLICATION-RUNBOOK.md) ·
[MONEY-PAGES.md](docs/MONEY-PAGES.md) · [CONVERSION-CTA.md](docs/CONVERSION-CTA.md)

**Technical:** [ANALYTICS.md](docs/ANALYTICS.md) · [AUTOMATION.md](docs/AUTOMATION.md) ·
[BREADCRUMBS.md](docs/BREADCRUMBS.md) · [EMAIL-CAPTURE.md](docs/EMAIL-CAPTURE.md) ·
[PERFORMANCE-MEDIA-PIPELINE.md](docs/PERFORMANCE-MEDIA-PIPELINE.md) ·
[TRUST-POLICY.md](docs/TRUST-POLICY.md)

## Monetization status

Honest current state, verified **2026-08-26**:

| Stream | Status |
|---|---|
| Affiliate commissions | **No programs approved yet.** Booking.com, Viator and GetYourGuide are pending submission; Eventbrite and OpenTable routes are still being confirmed. See [docs/affiliate-program-tracker.csv](docs/affiliate-program-tracker.csv). |
| Google AdSense | **Not currently serving.** Application was rejected 2026-03-20 ("low value content"); `ads.txt` is in place and re-review is pending. |
| Email list | Capture forms are live; list is in its earliest stage. |
| Sponsorships / partnerships | Future — not active. |

**Until a program is approved, outbound booking links are plain URLs with no tracking IDs.** Once
approved, links carry `rel="nofollow sponsored noopener"` plus a visible disclosure linking
[affiliate-disclosure.html](affiliate-disclosure.html), deployed per
[docs/AFFILIATE-OPS.md](docs/AFFILIATE-OPS.md).

## Privacy and analytics

This site **does** run analytics and advertising:

- **Google Analytics 4** — property `G-YWT237CDDX`
- **Google AdSense** — publisher `pub-3007723856138381` (see `ads.txt`)

Both use cookies. This is disclosed in the [privacy policy](privacy-policy.html), which is the
authoritative statement of data practices.

**What we don't do:** sell user data, run deceptive ads, or recommend venues we don't rate because
a commission is attached.

## Accessibility and performance

- Semantic HTML with skip links; WCAG AA colour contrast; keyboard navigable
- Mobile-first responsive layout (CSS Grid + Flexbox)
- Wide tables scroll inside `overflow-x:auto` wrappers rather than breaking the page
- No render-blocking frameworks; static assets served from the GitHub Pages CDN

## Legal

[Privacy Policy](privacy-policy.html) · [Terms](terms.html) ·
[Affiliate Disclosure](affiliate-disclosure.html) · [Contact](contact.html)

Private project. All rights reserved.

---

**Last updated:** 2026-08-26
