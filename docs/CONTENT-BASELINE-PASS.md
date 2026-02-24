# Content Baseline Pass (Phase B Prep)

Goal: eliminate "empty skeleton" feel by ensuring every page has a minimum useful baseline.

## Baseline requirements (every page)
- Clear intro with who this page is for
- Practical decision guidance (price, vibe, timing, alternatives)
- At least 3 internal links
- One action CTA (planner / weekend / booking path)
- Last-updated stamp

## Tiering model

### Tier 1 (money pages)
Deep content first (priority set in money-page modules):
- tonight
- weekend
- top rankings
- best experiences
- stay-near-nightlife
- core planner tools

### Tier 2 (all other pages)
Minimum viable depth pass so no page feels empty.

## Workflow
1. Run thin-page audit script:
   - `bash scripts/audit-thin-pages.sh .`
2. Fill Tier 2 pages to baseline standards.
3. Upgrade Tier 1 pages to deep standards.
4. Re-run audit and track reductions.

## KPI targets
- 0 critical thin pages on money-page set
- >80% pages above baseline threshold
- reduced bounce on hub-to-detail traffic
