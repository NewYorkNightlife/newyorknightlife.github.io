# Weekly Blog Workflow (Friday 2:00 PM ET)

## Objective
Publish one source-backed NYC Weekend Brief every Friday at **2:00 PM America/New_York**.

## Non-negotiables
- No fabricated events, listings, specials, or discounts.
- Time-sensitive/commercial claims require **3 independent sources**.
- Inline citations must be clickable hyperlinks in the sentence itself (no bracket-number citation markers like [1], [2]).
- Keep a clickable source links section at bottom for transparency.

## Weekly runbook
1. Collect candidate signals from trusted event/calendar sources.
2. Verify material claims across at least 2 independent sources when possible (3 for sensitive/commercial claims).
3. Draft the weekly brief from verified information only.
   - Uniqueness rule: target >=80% unique content week-over-week.
   - At least 12 confirmed weekly-specific NYC events/signals with venue + borough + listing/source link.
   - Event-first rule: >=80% of body must be week-specific NYC happenings; generic planning advice <=20%.
   - Avoid boilerplate paragraph reuse.
4. Enforce template sections in this exact order:
   - Title
   - Meta Description (150–160 chars)
   - NYC Weather Snapshot (current + 7-day, numeric highs/lows in both °F and °C for each day)
   - Weekend Overview
   - What Changed This Week (specific delta vs prior week: weather shift, event mix, neighborhood pressure, pricing/queue conditions)
   - Live Event Signals
   - Top Neighborhoods
   - Night Route Strategies
   - Budget + Risk Strategy
   - Plan Your NYC Night
   - Execution Checklist
   - Embedded Images + Captions (reader-facing, not internal notes)
   - Sources
   - Editorial Note
   - Final Takeaway
5. Add/confirm:
   - publish timestamp (Fri 2:00 PM ET)
   - weather block includes numeric values (°F and °C) plus daily range for 7 days
   - at least 2 embedded images with meaningful captions
   - external links use `target="_blank" rel="noopener"`
   - all external links are validated (HTTP 200–399)
   - methodology + affiliate disclosure links
   - required NYNightlife internal links:
     - https://nynightlife.com/tonight
     - https://nynightlife.com/weekend
     - https://nynightlife.com/night-planner
     - https://nynightlife.com/venue-compare
     - https://nynightlife.com/safe-late-night-transport
     - https://nynightlife.com/blog/archive
6. Add post to blog archive index.
7. Update sitemap.
8. Run `scripts/weekly-blog-check.sh .` and fix warnings.
   - Triple-check sequence before publish: (1) content specificity pass, (2) link validation pass, (3) final QA pass.
   - Word count must be 2,000–3,000.
   - Reader-facing text must not contain internal template instructions.
9. Commit + push.

## Source pool (starter)
- Eventbrite NYC nightlife events
- Time Out New York weekend listings
- NYCgo events calendar
- Resident Advisor NYC events

## QA before publish
- [ ] All links valid and clickable
- [ ] No unverified specific claims
- [ ] Timestamp format is correct (America/New_York)
- [ ] Methodology + affiliate disclosure links present
