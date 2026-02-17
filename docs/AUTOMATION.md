# Content Automation & Update Strategy

## Overview
This platform is designed for **minimal manual effort** with **maximum autonomous operation**. Once established, it requires ~2-4 hours/week maintenance.

## Content Update Workflow

### Weekly Updates (2-3 hours)

#### 1. Events Update (30 minutes)
**File:** `guides/events-this-weekend.html`

**Process:**
1. Check Eventbrite, GetYourGuide, Viator for new NYC events
2. Update "What's Happening This Weekend" section with 3-5 new events
3. Add links to booking partners
4. Update date at top of page
5. Commit with message: "Update: Weekly events (Feb 16)"

**Example Commit:**
```
git add guides/events-this-weekend.html
git commit -m "Update: Weekly events — Major club nights this weekend"
git push origin main
```

#### 2. Blog Post (1-1.5 hours)
**Goal:** One new blog post every 1-2 weeks

**Topics:**
- Venue spotlights
- Neighborhood deep-dives
- Seasonal nightlife changes
- Event reviews
- Insider tips from promoters

**Process:**
1. Research topic (30 min)
2. Write post (600-1000 words)
3. Add affiliate links naturally
4. Create HTML file in `/blog/` folder
5. Add link to `blog/index.html`
6. Commit and push

**Example Blog Post:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Inside Rooftop Season: Best NYC Rooftops in Summer | NYC Nightlife Blog</title>
  <link rel="stylesheet" href="/css/main.css">
</head>
<body>
<!-- Header -->
<main>
  <div class="container">
    <article>
      <h1>Inside Rooftop Season: NYC's Best Summer Rooftop Venues</h1>
      <p class="blog-meta">Updated June 2026 | 8 min read</p>
      <p>Rooftop season is here. Here's what you need to know...</p>
      <!-- Content -->
    </article>
  </div>
</main>
<!-- Footer -->
</body>
</html>
```

#### 3. Email Newsletter (30 min)
**Via:** Email service (MailerLite, ConvertKit)

**Content:**
- Top blog post of the week
- Featured guide excerpt
- 3-5 event highlights
- Tool recommendation

**Process:**
1. Log into email service
2. Create new email from template
3. Add this week's content links
4. Send to subscriber list
5. Track open rate + clicks

### Monthly Reviews (1-2 hours)

#### Review Performance
- **Metrics:** Pageviews, affiliate conversions, email growth
- **Tools:** Analytics dashboard, affiliate dashboards
- **Focus:** What content is converting best?

#### Content Audit
- Check for outdated information
- Verify affiliate links still work
- Update venue/pricing info if changed
- Fix broken links

#### Expand High-Performers
- If a guide is converting well, expand it
- Add more internal links to it
- Create supporting blog content
- Promote in newsletter

### Quarterly Updates (2-3 hours)

#### Major Content Review
- Review all guides for accuracy
- Update pricing if significantly changed
- Add new neighborhoods/venues if relevant
- Refresh blog archives

#### Technical Audit
- Test all functionality (forms, links, tools)
- Check mobile experience
- Verify affiliate disclosures are clear
- Backup site

#### Strategic Planning
- Review revenue data
- Plan next quarter's content
- Identify partnership opportunities
- Update this automation plan

## Content Calendar Template

**Week 1-2:**
- [ ] Update events page
- [ ] Publish blog post #1
- [ ] Send email newsletter

**Week 3:**
- [ ] Update events page
- [ ] Publish blog post #2
- [ ] Send email newsletter

**Week 4:**
- [ ] Update events page
- [ ] Perform content audit
- [ ] Send email newsletter

**Month End:**
- [ ] Review analytics
- [ ] Plan next month
- [ ] Update strategy docs

## Blog Post Topics (Content Ideas)

### High-Value Guides (1,500+ words)
- Complete neighborhood breakdown
- Season-specific nightlife (summer rooftop guide, winter cozy bars)
- Type-specific guides (dive bars, upscale, dance clubs)
- Guest list strategy
- Dress code by venue type

### Trend Posts (800-1,200 words)
- What's hot in NYC nightlife right now
- Event reviews (after attending)
- Seasonal changes
- New venue openings
- Policy/rule changes

### Utility Posts (600-800 words)
- Budget planning
- First-time guide
- Girls night out tips
- Group night strategy
- Safety tips

### Link Bait (1,000+ words)
- "50 Best Bars in NYC"
- "The Hidden Gems Nobody Knows About"
- "Ranked: Neighborhoods by Vibe"
- Comparative guides (neighborhood vs neighborhood)

## Email Newsletter Strategy

### Segments (Future)
- **New subscribers:** Welcome sequence (3 emails)
- **Engaged:** Weekly content emails
- **Inactive:** Re-engagement campaign

### Content Types
- **70%:** Guides & tools (educational)
- **20%:** Blog & trends (engagement)
- **10%:** Promotions & partners (revenue)

### Frequency
- Weekly during high season (Fri-Sat planning)
- Bi-weekly during low season (Mon-Thurs)

## Affiliate Link Management

### Placement Rules
- **Max 3 affiliate links per 1,000 words**
- **Natural integration only** (no forced links)
- **Value-first:** Would you recommend this without commission?
- **Label all links** with affiliate disclosure

### Partner Rotation
- **Booking.com:** Every accommodation mention
- **GetYourGuide:** Bar crawl, VIP experience recommendations
- **Amazon:** Product mentions (clothing, accessories, tools)
- **Eventbrite:** Event listings

### Tracking Template
```
[Date] | [Page] | [Partner] | [Anchor Text] | [Position] | [Conversions]
2026-02-16 | best-nightlife | Booking | "hotels near clubs" | para 3 | 2
```

## Tools & Services

### For Updates
- **Git/GitHub:** Version control, branching
- **VS Code / Editor:** HTML editing
- **Browser:** Testing and verification

### For Content
- **MailerLite / ConvertKit:** Email marketing
- **Canva / Figma:** Simple images (if needed)
- **Google Docs:** Collaborative drafting

### For Analytics
- **Google Analytics** (or Plausible for privacy)
- **Affiliate Dashboards:** Partner-specific tracking
- **Simple Spreadsheet:** Manual tracking

### For Management
- **GitHub Projects:** Content calendar
- **Notion / Trello:** Editorial calendar
- **Google Sheet:** Performance tracking

## Automation Opportunities (Future)

### Semi-Automation (1-2 hours/week saved)
- **Email template:** Reusable structure
- **Blog template:** Standard HTML/CSS
- **Event scraping:** Script to pull from APIs
- **Link checking:** Automated broken link detection

### Full Automation (needs infrastructure)
- **Event API integration:** Auto-update events
- **Email scheduling:** Automated send times
- **Social posting:** Auto-share new content
- **Analytics tracking:** Dashboard alerts

## Maintenance Checklist

### Weekly
- [ ] Update events page (30 min)
- [ ] Publish blog post (90 min)
- [ ] Send email (30 min)
- [ ] Check affiliate dashboards (15 min)

### Monthly
- [ ] Review analytics (30 min)
- [ ] Content audit (30 min)
- [ ] Affiliate link verification (20 min)
- [ ] Email list health check (10 min)

### Quarterly
- [ ] Major guide review (60 min)
- [ ] Technical audit (30 min)
- [ ] Strategic planning (60 min)
- [ ] Competitor research (30 min)

### Annually
- [ ] Site redesign assessment
- [ ] Revenue model review
- [ ] New partner evaluation
- [ ] Growth planning

## Handing Off

If delegation needed:

### For another person (40-60% of work):
**Assign:**
- Blog post writing (30-45 min/week)
- Email newsletter assembly (20-30 min/week)
- Events updating (15-30 min/week)

**Keep:**
- Strategy & planning
- Affiliate management
- Analytics review
- Partner relationships

### For AI/Automation (future):
**Could automate:**
- Event pulling + formatting
- Newsletter templating
- Blog outline generation
- Link checking

**Manual always:**
- Final content review
- Affiliate optimization
- Strategy changes
- Partnership decisions

## Success Metrics

### Monthly Targets
- **Pageviews:** 1,000 → 5,000 → 10,000+
- **Email subscribers:** +100-200/month
- **Affiliate conversions:** 5-10 → 15-25 → 30-50/month
- **Blog posts:** 4-5/month

### Annual Goals (Year 1)
- 100,000+ annual pageviews
- 1,000+ email subscribers
- $200-500+ monthly revenue
- Established authority in NYC nightlife

---

**Next Steps:**
1. Set up content calendar (Google Sheet / Notion)
2. Create email template
3. Create blog post template
4. Schedule first 4 blog topics
5. Send first newsletter

For technical details, see SITE-ARCHITECTURE.md.
For revenue goals, see MONETIZATION.md.
