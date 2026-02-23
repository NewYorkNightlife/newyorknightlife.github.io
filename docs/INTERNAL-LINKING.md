# Internal Linking Blocks (Step 4)

This step adds dynamic "Next Best Pages" blocks to increase session depth.

## What it does

On non-home pages, `js/main.js` now injects an internal links section before the footer.

It selects recommendations by section:
- `/guides/*`
- `/neighborhoods/*`
- `/tools/*`
- `/rankings/*` and `/categories/*`
- fallback set for all other pages

## Tracking

Clicks on recommendation links emit:
- `internal_link_recommendation_click`

Payload includes:
- `from` (current path)
- `to` (destination href)

## Why

- Improves page-to-page navigation
- Increases session depth and crawl paths
- Creates reusable linking logic without editing every page manually
