# Workflows — NYNightlife

This folder contains automation assets for live nightly publishing.

## Included
- `n8n/nyc-tonight-production.json` — importable n8n workflow
- `n8n/SETUP.md` — credential + setup instructions
- `n8n/tonight-feed.schema.json` — output schema contract

## What this workflow does
1. Runs on schedule (ET)
2. Pulls weather + headlines + event candidate sources
3. Applies triple-source verification gate for featured events
4. Runs AI readability/consistency QA pass
5. Publishes `/data/tonight-feed.json` to this repo via GitHub API

## Non-negotiables
- No fabricated events
- Featured events require 3 independent confirmations
- If verification fails, keep previous valid feed
