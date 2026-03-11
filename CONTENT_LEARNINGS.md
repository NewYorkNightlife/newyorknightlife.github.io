# CONTENT_LEARNINGS.md - NYNightlife Execution Playbook

Purpose: Persistent guidance from live content work so quality improves every batch.

## What consistently works

1. **Objective-first page design**
   - Start every page by defining user objective (social, date, music-first, premium).
   - Readers convert better when they can self-segment fast.

2. **Budget lanes increase usefulness**
   - Include Lean / Balanced / Premium lanes on most planning pages.
   - Ranges should be practical and framed as planning bands, not guarantees.

3. **Route logic beats generic venue lists**
   - One core zone + one fallback zone is a strong default.
   - Late-night cross-town pivots usually reduce outcomes unless upside is obvious.

4. **Timing windows improve trust**
   - Provide practical windows (early, peak, late) and what changes in each.
   - This makes pages feel operational vs. generic.

5. **Always include a conversion path**
   - Link to Night Planner, Venue Compare, and cost tools.
   - Internal links should move users from content -> decision -> action.

## Quality checklist before publish

- Remove all scaffold remnants ("Content to be expanded", "Next Build Step", etc.)
- Ensure one clear H1 and strong meta description
- Add concrete sections: strategy, budget, timing, checklist, next steps
- Include internal links to at least 2-3 adjacent decision pages/tools
- Add "Last updated" timestamp
- Quick live check after deploy (title or unique line present)

## Style rules for NYNightlife voice

- Insider, direct, no fluff
- Strategic and actionable, not bloggy
- Focus on outcome quality, spend efficiency, and route discipline
- No fabricated claims or fake-specific venue assertions

## Batch workflow for placeholder replacement

1. Select 10 pages in one theme cluster (e.g., categories, neighborhoods)
2. Replace with production copy using reusable structure + custom section per page
3. QA scan for placeholders and metadata
4. Commit, push, and verify live endpoints
5. Report links clearly to Father Dan

## Locked Build Rules (effective now)

These are mandatory defaults unless Father Dan overrides them explicitly.

1. **Existing pages only unless asked**
   - Do not create new pages during placeholder-replacement sprints.

2. **Games must be real interactives**
   - Game pages must include working UI + scoring/decision logic.
   - Descriptive-only game pages are not acceptable.

3. **One game at a time**
   - Build, test, ship, and confirm one game before starting the next.

4. **Triple-check before publish**
   - Verify no scaffold text remains.
   - Verify JS logic is present in deployed HTML.
   - Verify core user flow works: answer/select -> result -> reset.

5. **Live validation required**
   - After push, confirm on production URL with cache-busting query (`?v=` timestamp).

6. **Quality threshold**
   - Keep pages useful even before advanced polish: clear objective, strong output, and next-step actions.

## Future upgrades to apply

- Add structured data where appropriate (Article/FAQ for deep guides, ItemList for rankings)
- Standardize reusable CTA components for affiliate/lead capture
- Add neighborhood-specific transport notes for late-night reliability
- Build stronger cross-link loops between borough, category, and tool pages
