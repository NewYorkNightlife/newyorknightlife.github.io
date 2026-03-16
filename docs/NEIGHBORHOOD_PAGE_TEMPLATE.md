# Neighborhood Page Template (Locked)

This is the canonical template for all neighborhood pages, based on the approved SoHo implementation.

## Canonical Live Example
- `/neighborhoods/soho-nightlife.html`

## Required Page Structure (Do Not Skip)

1. **Premium Header/Nav**
   - Same global menu/nav as homepage.

2. **Hero Section (Town-Specific)**
   - Background image must be town-specific and visually accurate.
   - Eyebrow + strong H1 + strategic intro copy.
   - Two CTAs:
     - Build a plan (tool)
     - Weekend signals (weekend page)
   - 3 chips (best-for, route style, key risk).

3. **How to Win [Town] in 4 Moves**
   - Practical route logic in ordered steps.

4. **Quick Snapshot panel**
   - Energy profile
   - Best start window
   - Group sweet spot
   - Most common fail

5. **Inline Visual Section**
   - One additional town-specific image.

6. **Budget Lanes Section**
   - Value / Standard / Premium cards.

7. **Mistakes + Execution Checklist**
   - Two side-by-side panels.

8. **Editorial Section (500–1000 words)**
   - Explain the town’s nightlife identity/history/behavior.
   - Must be useful and practical, not generic filler.

9. **Top Spot Listings (20–40 links)**
   - Group into 3 columns/cards.
   - Include bars, restaurants, clubs, rooftops, and cultural/night options where relevant.
   - Every spot must have:
     - direct link (maps/search or official page)
     - map-jump icon (🗺️) with `data-place`.

10. **Interactive Map Section**
    - Leaflet + OpenStreetMap.
    - Markers generated from the listed places.
    - Clicking 🗺️ icon jumps to map and focuses marker.

11. **Use These Next**
    - Tonight Hub
    - Venue Compare
    - Weekly Archive

## Design/UX Rules
- Keep spacing compact/premium (use tightened section rhythm from SoHo page).
- Keep same visual language as site-wide style.
- Do not add random blocks not present in SoHo model unless approved.

## Content Rules
- Must be town-specific (copy, image, spots, map place names).
- No fabricated claims.
- Prefer verifiable spot names and practical planning language.
- Keep tone strategic and direct.

## Implementation Workflow
For each new neighborhood page:
1. Duplicate SoHo page structure.
2. Replace all SoHo-specific content with target town content.
3. Update title/meta/OG/canonical and schema name/description.
4. Replace hero and inline image with relevant town visuals.
5. Replace all 20–40 spot links + map `data-place` values.
6. Validate map markers and icon jump behavior.
7. QA on mobile and desktop.

## Current Queue (to execute in order unless changed)
- Lower East Side
- Williamsburg
- Meatpacking
- East Village
- Midtown
