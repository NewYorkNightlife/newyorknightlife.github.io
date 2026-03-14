# Weekly Blog Workflow (Friday 3:00 PM ET)

## Objective
Publish one source-backed NYC Weekend Brief every Friday at **3:00 PM America/New_York** that is event-first, reader-friendly, and fully rule-compliant.

## Weekly runbook
1. Collect weekly NYC signals from trusted sources.
2. Verify material claims (2+ sources when possible; 3 for sensitive/commercial claims).
3. Draft the brief with event-first focus:
   - >=80% week-specific NYC happenings
   - <=20% generic planning commentary
   - >=12 confirmed weekly event signals (name + venue + borough + direct link)
4. Build sections in required order (see `BLOG_HARD_RULES.md`).
5. Add weather block (current + 7-day, numeric °F/°C).
6. Add at least 2 relevant images with captions.
7. Ensure all required NYNightlife internal links are present.
8. Ensure reader-facing quality:
   - no internal/template wording
   - no robotic numbered “signal/context” copy
   - no repetitive boilerplate blocks
9. Validate links:
   - all external links 200–399
   - no search-result links in Live Event Signals
10. Run QA:
   - `scripts/weekly-blog-check.sh .`
   - fix all warnings/errors
11. Update archive/index/sitemap.
12. Commit + push only after QA passes.

## Non-negotiables
- No fabricated events or unverified specifics.
- No publish when hard rules fail.
- Keep copy human, specific, and week-grounded.

## Quick QA checklist
- [ ] 2,000–3,000 words
- [ ] Weather section with °F/°C + 7-day range
- [ ] 12+ direct event links
- [ ] 2+ relevant images with captions
- [ ] Required internal links included
- [ ] No template/instructional text in article
- [ ] All external links validated
- [ ] Checker passes clean
