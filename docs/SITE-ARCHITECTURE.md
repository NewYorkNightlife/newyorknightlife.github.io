# NYC Nightlife Platform — Site Architecture & Design

## Overview
This is a complete, autonomous revenue-generating NYC nightlife platform built on GitHub Pages. Static HTML/CSS/JS with no backend required.

## Directory Structure

```
newyorknightlife-site/
├── index.html                 # Homepage (hero, featured content, CTAs)
├── css/
│   └── main.css              # Master stylesheet (light theme, gold accents)
├── js/
│   ├── main.js               # Core functionality (email capture, tools, navigation)
├── guides/
│   ├── index.html            # Guides hub
│   ├── best-nightlife-experiences.html    # Pillar: Venues & experiences
│   ├── bar-crawl-guide.html   # Supporting: Bar crawl strategies
│   ├── stay-near-nightlife.html           # Pillar: Hotels/accommodation
│   └── events-this-weekend.html           # Pillar: Events & ticketing
├── tools/
│   ├── night-out-spinner.html # Interactive: Random night ideas
│   ├── budget-planner.html    # Interactive: Budget calculator
│   └── neighborhood-quiz.html # Interactive: Vibe matcher
├── blog/
│   └── index.html            # Blog hub (posts linkable)
├── privacy-policy.html        # Legal
├── terms.html                 # Legal
├── contact.html               # Business inquiries
└── docs/
    ├── SITE-ARCHITECTURE.md   # This file
    ├── MONETIZATION.md        # Revenue strategy
    └── AUTOMATION.md          # Update & content workflow
```

## Page Architecture

### Homepage (index.html)
**Goal:** Convert visitors to guides + email list + tools

**Structure:**
- Hero section with value prop
- Quick links to top 3 guides
- Featured content section
- Interactive tools preview
- Blog preview (latest 3 posts)
- Email capture CTA (prominent)
- Footer with legal + partner links

**Conversions:**
- Email capture form
- Guide links (high click-through)
- Tool links (engagement)
- Blog links (SEO + authority)

### Guides Hub (guides/index.html)
**Goal:** Hub page for guide discovery

**Structure:**
- All guides listed with descriptions
- Browse by neighborhood (Manhattan, Brooklyn, Queens)
- Featured recommendations
- Internal linking to detailed guides

### Pillar Pages (4 total)
Each pillar is 1,500-2,500 words with:
- Comprehensive content (authority signal)
- Multiple H2/H3 sections for subkeywords
- Contextual affiliate links (natural, not forced)
- Schema markup (Guide type)
- Email capture form
- Internal links to related content
- Footer with partner links

**Pillars:**
1. `best-nightlife-experiences.html` — Venues, neighborhoods, dress codes, pricing
2. `bar-crawl-guide.html` — Bar crawl strategy, neighborhoods, booking
3. `stay-near-nightlife.html` — Hotels, neighborhoods, accommodation guide
4. `events-this-weekend.html` — Events, ticketing, real-time listings

### Tools (3 interactive)
Each tool page includes:
- Functional interactive tool (JavaScript)
- Related guides/resources
- Email capture CTA
- Example outputs

**Tools:**
1. **Night Out Spinner** — Random nightlife ideas
2. **Budget Planner** — Budget-to-venue mapping
3. **Neighborhood Quiz** — Vibe-based recommendations

### Blog Hub (blog/index.html)
**Goal:** Content discovery + authority

**Structure:**
- Latest posts (blog items list)
- Category browsing
- Email subscription CTA
- Links to featured content

**Note:** Individual blog posts not yet created; structure ready for easy addition.

### Supporting Pages
- `privacy-policy.html` — Affiliate disclosure + data practices
- `terms.html` — Legal terms
- `contact.html` — Business inquiries + about us

## Design System

### Colors
- **Primary:** #1a1a2e (dark navy)
- **Secondary:** #16213e (dark blue)
- **Accent:** #0f3460 (medium blue)
- **Gold:** #d4af37 (highlight/CTAs)
- **Text:** #f4f4f4 (light, readable)
- **Muted:** #b0b0b0 (secondary text)

### Typography
- **Font Stack:** System fonts (-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, etc.)
- **Headings:** Bold, 700 weight
- **H1:** 3rem, gold color
- **H2:** 2.2rem, gold border-bottom
- **Body:** 1rem, 1.6 line-height

### Components
- **Card:** Secondary bg, border, hover effect (lift + gold border)
- **CTA Button:** Gold bg, primary text, hover state
- **Email Form:** Input + button in flex row
- **Affiliate Notice:** Gold left border, accent bg
- **Blog Item:** Secondary bg, gold left border, hover bg change

## Responsive Design
- **Mobile-first approach**
- **Breakpoint:** 768px for tablet/desktop
- **Grid:** CSS Grid with auto-fit, minmax
- **Flexible:** All components stack on mobile

## SEO Architecture

### Keywords by Cluster
**Cluster A (Experiences):**
- NYC nightlife, best bars NYC, NYC clubs, rooftop bars, bar crawls NYC, cocktail bars

**Cluster B (Accommodation):**
- Hotels near NYC nightlife, stay near clubs, hotel NYC nightlife

**Cluster C (Events):**
- NYC events, things to do tonight, club events, DJ nights NYC

### Internal Linking Strategy
- Homepage → Pillar pages (3-4 links each)
- Pillar pages → Supporting pages
- Supporting pages → Related content
- Blog previews link to guides
- Tools link to relevant guides

### Schema Markup
- Website schema (homepage)
- Guide schema (pillar pages)
- BreadcrumbList (navigation)
- FAQPage (if FAQ added)

## Mobile Experience
- Hamburger menu (future enhancement)
- Touch-friendly buttons (1rem+ padding)
- Readable on all screen sizes
- Fast loading (no images initially)

## Performance
- Static HTML/CSS/JS (no database)
- GitHub Pages hosting (fast CDN)
- Minimal JavaScript (only for tools + email)
- No tracking scripts (privacy-first)
- ~200KB total site size

## Accessibility
- Semantic HTML (header, nav, main, section, footer)
- ARIA labels where needed
- Color contrast WCAG AA
- Keyboard navigation support
- Alt text for images (if added)

## Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile (iOS Safari, Android Chrome)
- ES6 JavaScript support required

## Future Enhancements
- Blog post template for easy additions
- Image optimization pipeline
- Search functionality
- Dark/light mode toggle
- Comment system
- Affiliate link automation
- Google Analytics integration

## File Size & Performance
- Total CSS: ~6KB
- Total JS: ~6KB
- HTML average: ~5-10KB per page
- Total site: <200KB (very fast)

---
For monetization details, see MONETIZATION.md
For update strategy, see AUTOMATION.md
