# Weekly Blog Workflow (Friday 2:00 PM ET)

## Objective
Publish one source-backed NYC Weekend Brief every Friday at **2:00 PM America/New_York** that is event-first, reader-friendly, and fully rule-compliant.

## Pacing
This workflow is intentionally unhurried. Verification beats speed. Research venue
calendars in small batches rather than large parallel bursts, and never re-probe the
same host repeatedly in quick succession — venue and ticketing sites will rate-limit a
burst of requests and return 403s even for perfectly good links. Allow a couple of
hours end to end.

## Weekly runbook
1. Collect weekly NYC signals from trusted sources.
2. Verify material claims (2+ sources when possible; 3 for sensitive/commercial claims).
   A venue's own listing page plus its embedded JSON-LD structured data is strong
   corroboration.
3. Draft the brief with event-first focus:
   - >=80% week-specific NYC happenings
   - <=20% generic planning commentary
   - >=12 confirmed weekly event signals (name + venue + borough + direct link)
4. Build sections in required order (see `BLOG_HARD_RULES.md`).
5. Add weather block (current + 7-day, numeric °F/°C).
6. Add at least 2 relevant images with captions. Prefer local files in `assets/images/`.
7. Ensure all required NYNightlife internal links are present.
8. Ensure reader-facing quality:
   - no internal/template wording
   - no robotic numbered "signal/context" copy
   - no repetitive boilerplate blocks
9. Validate links:
   - all external links 200–399
   - no search-result links in Live Event Signals
10. Run QA:
   - `scripts/weekly-blog-check.sh .`
   - fix all warnings/errors; wait 5+ minutes between re-runs
11. Update archive/index. Weekly briefs are `noindex` and stay OUT of `sitemap.xml`.
12. Commit + push only after QA passes.

## Reading the QA output
The link checker is deliberately slow (paced, jittered, round-robin across hosts) and
takes roughly two minutes. It reports two distinct failure classes:

- **BAD** — 404/410/5xx/connection error. A genuinely broken link. Fails the gate; fix it.
- **BLOCKED** — 403/429 after a slow retry. Bot protection, not evidence of a broken
  link. Does not fail the gate, but each one must still be confirmed by hand in a
  browser before publishing.

The brief's own canonical URL is excluded from checking, because a new post has not been
deployed yet and would always 404 against itself.

## Non-negotiables
- No fabricated events or unverified specifics.
- No publish when hard rules fail.
- Keep copy human, specific, and week-grounded.

## Quick QA checklist
- [ ] 2,000–3,000 words (this includes shared header/footer chrome)
- [ ] Weather section with °F/°C + 7-day range (literal ° characters, not entities)
- [ ] 12+ direct event links
- [ ] 2+ relevant images with captions
- [ ] Required internal links included
- [ ] No template/instructional text in article
- [ ] All external links validated; BLOCKED ones confirmed by hand
- [ ] Checker exits 0
