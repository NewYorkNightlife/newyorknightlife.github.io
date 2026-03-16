# Neighborhood Page Template (LOCKED v2 — Williamsburg Final)

This is now the **100% canonical template** for all neighborhood pages.
Reference implementation quality is the finalized Williamsburg page.

## Canonical Reference Page
- Live: `https://nynightlife.com/neighborhoods/williamsburg-nightlife.html`

---

## 1) Required Structure (Exact Order)

1. **Premium global header/nav**
   - Same as homepage (no custom/local nav variants).

2. **Hero banner (town-specific)**
   - Full-width hero image relevant to that exact neighborhood.
   - Eyebrow + clear H1 + 1 short intro paragraph.
   - Two CTA buttons:
     - Build plan tool
     - Weekend signals page
   - Three chips:
     - best-for
     - route style
     - key risk

3. **How to Win [Town] in 4 Moves (left) + Quick Snapshot (right)**
   - 2-column panel block.

4. **Image block #2 (town-specific)**
   - Full-width in-content image.

5. **Budget Lanes section**
   - 3 cards: Value / Standard / Premium.

6. **Common Mistakes + Execution Checklist**
   - 2-column panel block.

7. **Editorial card (history + identity focused)**
   - Heading: short and readable (avoid overly long titles).
   - Includes:
     - lead paragraph
     - subheads
     - short paragraphs
     - bullet callouts
   - **Must include one inline image within the editorial card**
     - text wraps around image on desktop
     - image stacks on mobile

8. **Image block #3 (town-specific)**
   - Additional image section with short caption/context line.

9. **Top spots section (20–40 listings)**
   - 3 cards/columns:
     - bars/cocktail anchors
     - dining-led nightlife
     - music/rooftops/culture
   - Each listing must include:
     - clickable venue link
     - 🗺️ map-jump icon with `data-place`

10. **Interactive map section**
    - Leaflet + OpenStreetMap
    - fixed marker coordinates (preferred) for reliability
    - 🗺️ icon click jumps to map and focuses marker popup

11. **Use These Next**
    - Tonight Hub
    - Venue Compare
    - Weekly Brief Archive

---

## 2) Image Rules (Strict)

- Use **real, neighborhood-relevant** imagery only.
- Image must be clearly tied to the exact town page (landmark/street/venue context from that neighborhood).
- **No hallucinated/made-up visuals.**
- If generated (e.g., Nano Banana), output must still be realistic and faithful to that actual neighborhood.
- No generic NYC image unless it is clearly tied to that neighborhood.
- Minimum per page: **3 images total**
  1) hero banner image
  2) in-content image
  3) one more image (editorial inline or dedicated section)
- The 3 images must be **visually distinct** (different subject/angle/context), not near-duplicate shots.
- Alt text must be neighborhood-specific and descriptive.

---

## 3) Editorial Writing Standard (500–1000 words)

Editorial must be primarily:
- neighborhood history
- cultural identity
- what differentiates it from other NYC zones
- how nightlife evolved there

And only secondarily:
- practical strategy/execution

Tone:
- insider, direct, polished
- no fluff
- no fabricated claims

Formatting standard:
- short paragraphs
- subheads every 1–3 paragraphs
- at least one bullet list for scanability
- avoid giant uninterrupted text blocks

---

## 4) Spacing & Readability Standard (Use This Exactly)

Apply the tightened + breathable pattern from Williamsburg final:
- namespaced page classes (avoid global CSS collisions)
- compact section rhythm
- increased card/panel inner padding
- comfortable line-height for body text
- editorial card has extra internal breathing room
- avoid text hugging card edges

### CSS Behavior Requirements
- Namespaced classes per page (example pattern: `wb-*`, `les-*`, etc.)
- Do **not** rely on generic `.hero` / `.section` alone
- Ensure mobile media rules preserve readability and spacing

---

## 5) Map Standard

- Use Leaflet + OSM tiles.
- Prefer **fixed lat/lon marker set** over runtime geocoding.
- Keep marker popup names human-readable.
- Keep map-jump icon behavior consistent across all pages.

---

## 6) SEO/Schema Requirements

Each page must include:
- unique title + meta description
- canonical URL
- OG/Twitter tags
- schema `WebPage` object with neighborhood-specific name/description

---

## 7) Implementation Workflow (For Every New Town)

1. Copy finalized Williamsburg structure.
2. Rename page namespace classes for that town.
3. Replace all town-specific copy and metadata.
4. Replace all 3 images with neighborhood-true images.
5. Write 500–1000 word history/identity editorial (with inline image in card).
6. Populate 20–40 spot links + 🗺️ icons.
7. Add fixed marker coordinates for all listed spots.
8. QA:
   - desktop spacing
   - mobile spacing
   - map marker visibility
   - map-jump behavior
   - link correctness

---

## 8) Default Rollout Queue
- Meatpacking
- East Village
- Midtown
- remaining neighborhoods in `neighborhoods/`

This template is locked unless explicitly changed by Father Dan.
