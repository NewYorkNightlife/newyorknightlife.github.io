# Conversion CTA Module (Sprint 2 Step 4)

Adds a reusable high-intent CTA block on commercial sections:
- guides
- rankings
- categories
- tonight
- weekend
- visit
- things-to-do

## CTA destinations
- `/tools/nyc-night-planner.html`
- `/tools/venue-compare-nyc.html`
- `/weekend/nyc-nightlife-this-weekend.html`

## Tracking
Each CTA click emits:
- `conversion_cta_click`

Event params:
- `from`
- `to`
- `cta`

## Why
This creates a consistent conversion path from discovery pages into planning/booking behavior.