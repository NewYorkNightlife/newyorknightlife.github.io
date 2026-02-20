# NYNightlife — Website Skeleton Blueprint V1

Date: 2026-02-20
Status: Approved direction draft (build-first, content-light initially)

## Objective
Build a scalable NYC nightlife site architecture that:
1) captures SEO demand across borough + neighborhood + intent pages,
2) creates repeat usage via tools/maps/games/weekly updates,
3) avoids future structural rebuild.

## Product Thesis
NYNightlife should function like an **NYC nightlife operating system**:
- Discover by area, vibe, budget, and night
- Decide quickly with comparison tools
- Plan an actual night out with practical utilities
- Return weekly for fresh picks, event updates, and games

## Benchmark Patterns Observed
From review of major city discovery platforms (Time Out, Eventbrite city nightlife listings, local event aggregators, venue-list ecosystems):
- Strong category hubs (bars/clubs/events/music)
- Strong neighborhood segmentation
- Frequent “tonight/this weekend” refresh loops
- List + utility combo outperforms article-only structures
- Newsletter and recurring series support return traffic

## Final IA (Top-Level)
- Home
- Visitor Start Here (NEW)
- Boroughs
- Neighborhoods
- Categories
- Tonight / This Weekend
- Things To Do (Attractions + tours) (NEW)
- Plan Your Trip (transport + hotel + itineraries) (NEW)
- Tools
- Games
- Blog / Editorial
- Rankings
- Deals / Guest Lists (future monetization lane)
- About / Contact / Legal

## Skeleton Build Targets (Phase 1 Structure)

### A) Borough Hubs (5 pages)
- /boroughs/manhattan-nightlife.html
- /boroughs/brooklyn-nightlife.html
- /boroughs/queens-nightlife.html
- /boroughs/bronx-nightlife.html
- /boroughs/staten-island-nightlife.html

### B) Neighborhood Hubs (30 pages initial)
Prioritize high-intent nightlife zones first.

Manhattan (12):
- lower-east-side-nightlife
- east-village-nightlife
- west-village-nightlife
- soho-nightlife
- meatpacking-nightlife
- chelsea-nightlife
- hells-kitchen-nightlife
- midtown-nightlife
- upper-west-side-nightlife
- upper-east-side-nightlife
- harlem-nightlife
- financial-district-nightlife

Brooklyn (10):
- williamsburg-nightlife
- bushwick-nightlife
- greenpoint-nightlife
- dumbo-nightlife
- downtown-brooklyn-nightlife
- park-slope-nightlife
- bed-stuy-nightlife
- crown-heights-nightlife
- cobble-hill-nightlife
- red-hook-nightlife

Queens (6):
- astoria-nightlife
- long-island-city-nightlife
- flushing-nightlife
- jackson-heights-nightlife
- forest-hills-nightlife
- ridgewood-nightlife

Bronx (1):
- bronx-nightlife-guide

Staten Island (1):
- staten-island-nightlife-guide

### C) Category Hubs (12 pages)
- /categories/best-nyc-clubs.html
- /categories/best-nyc-bars.html
- /categories/rooftop-bars-nyc.html
- /categories/speakeasies-nyc.html
- /categories/live-music-nyc-nightlife.html
- /categories/latin-nightlife-nyc.html
- /categories/hip-hop-nightlife-nyc.html
- /categories/edm-nightlife-nyc.html
- /categories/lgbtq-nightlife-nyc.html
- /categories/comedy-nightlife-nyc.html
- /categories/after-hours-nyc.html
- /categories/date-night-nyc-nightlife.html

### D) Time-Intent Hubs (8 pages)
- /tonight/things-to-do-in-nyc-tonight.html
- /tonight/friday-night-nyc.html
- /tonight/saturday-night-nyc.html
- /weekend/nyc-nightlife-this-weekend.html
- /weekend/nyc-rooftop-weekend-guide.html
- /seasonal/summer-nightlife-nyc.html
- /seasonal/winter-nightlife-nyc.html
- /seasonal/new-years-eve-nyc-nightlife.html

### E) Utility Tools (10 pages)
- /tools/nyc-night-planner.html
- /tools/nyc-nightlife-map.html
- /tools/venue-compare-nyc.html
- /tools/cover-charge-calculator-nyc.html
- /tools/dress-code-checker-nyc.html
- /tools/subway-safe-route-night.html
- /tools/group-night-out-planner.html
- /tools/birthday-night-planner-nyc.html
- /tools/budget-planner.html (existing)
- /tools/night-out-spinner.html (existing)

### F) Games & Engagement (10 pages)
- /games/guess-the-neighborhood.html
- /games/would-you-get-in-door-game.html
- /games/build-your-perfect-nyc-night.html
- /games/nightlife-tier-list.html
- /games/bar-or-club-quiz.html
- /games/nyc-nightlife-trivia.html
- /games/dj-or-genre-match.html
- /games/first-date-night-game.html
- /games/group-vibe-decider.html
- /games/secret-spot-hunt.html

### G) Rankings & Programmatic Lists (15 pages initial)
- /rankings/best-clubs-in-nyc.html
- /rankings/best-bars-in-nyc.html
- /rankings/best-rooftops-in-nyc.html
- /rankings/best-nightlife-by-borough.html
- /rankings/best-thursday-night-spots-nyc.html
- /rankings/best-friday-night-spots-nyc.html
- /rankings/best-saturday-night-spots-nyc.html
- /rankings/best-late-night-food-near-clubs-nyc.html
- /rankings/best-nightlife-under-50-nyc.html
- /rankings/best-vip-experiences-nyc.html
- /rankings/best-bachelorette-nightlife-nyc.html
- /rankings/best-birthday-nightlife-nyc.html
- /rankings/best-hip-hop-nights-nyc.html
- /rankings/best-latin-nights-nyc.html
- /rankings/best-edm-nights-nyc.html

### H) Blog System (24 starter posts + 1 hub)
- /blog/index.html
- 24 article placeholders across:
  - neighborhood deep dives
  - venue strategy guides
  - weekend recaps
  - trend analysis
  - practical night-planning guides

### I) Conversion + Ops Pages (8 pages)
- /newsletter/nightlife-insider.html
- /deals/guest-list.html
- /deals/bottle-service-request.html
- /partners/for-venues.html
- /partners/sponsor-with-us.html
- /about.html
- /contact.html (existing)
- legal pages (existing)

### J) Visitor Planning Layer (18 pages) (NEW)
Core for international + first-time NYC visitors who need quick-reference planning.

Visitor Hub + Trip Planning:
- /visit/first-time-nyc-nightlife-guide.html
- /visit/3-day-nyc-nightlife-itinerary.html
- /visit/5-day-nyc-nightlife-itinerary.html
- /visit/family-vs-party-zones-nyc.html
- /visit/where-to-stay-for-nightlife-nyc.html

Transport + Navigation:
- /plan/nyc-subway-for-nightlife.html
- /plan/uber-lyft-vs-subway-nyc-night.html
- /plan/airport-to-manhattan-night-arrival.html
- /plan/safe-late-night-transport-nyc.html

Attractions + Crossover Intent (day-to-night visitors):
- /things-to-do/times-square-at-night.html
- /things-to-do/statue-of-liberty-and-ellis-island-guide.html
- /things-to-do/nyc-helicopter-tours-guide.html
- /things-to-do/nyc-hop-on-hop-off-bus-guide.html
- /things-to-do/nyc-night-cruises-and-ferry-experiences.html
- /things-to-do/top-10-first-time-nyc-experiences.html

Practical Visitor Tools:
- /tools/nyc-trip-cost-calculator.html
- /tools/nyc-3-day-itinerary-builder.html
- /tools/hotel-neighborhood-matcher-nyc.html

## Total Skeleton Target (initial)
- ~111 pages (mix of existing + new placeholders)

This is large enough for topical authority and internal linking depth without overbuilding into unmanageable scope.

## Build Order (No Rebuild Strategy)
1. Foundation directories + nav + internal linking model
2. Borough hubs
3. Neighborhood hubs (Manhattan/Brooklyn/Queens first)
4. Category hubs
5. Time-intent hubs
6. Tools (map + planner + compare first)
7. Games
8. Rankings
9. Blog placeholders
10. Conversion pages

## Template System (critical)
Create reusable templates before mass page generation:
- Hub template
- Neighborhood template
- Ranking template
- Tool template
- Game template
- Blog template

Every page should include:
- hero + quick context
- structured sections
- “plan your night” module
- related links block
- email capture
- disclosure/footer

## SEO + Return Traffic Principles
- SEO: borough + neighborhood + category + intent coverage
- Retention: tools, map, weekly pages, games, recurring series
- Internal links: each page links to 6–12 related nodes
- Publishing rhythm: update tonight/weekend pages continuously

## Sprint 1 Deliverables (next execution block)
- New folders: boroughs/, neighborhoods/, categories/, tonight/, weekend/, seasonal/, rankings/, games/, newsletter/, deals/, partners/
- 12 high-priority pages scaffolded with proper navigation and placeholder sections:
  1) boroughs/manhattan-nightlife.html
  2) boroughs/brooklyn-nightlife.html
  3) boroughs/queens-nightlife.html
  4) neighborhoods/lower-east-side-nightlife.html
  5) neighborhoods/williamsburg-nightlife.html
  6) neighborhoods/astoria-nightlife.html
  7) categories/best-nyc-clubs.html
  8) categories/rooftop-bars-nyc.html
  9) tonight/things-to-do-in-nyc-tonight.html
  10) tools/nyc-nightlife-map.html
  11) tools/nyc-night-planner.html
  12) games/guess-the-neighborhood.html

Success criteria: clean IA, nav working, internal links in place, ready for content fill.
