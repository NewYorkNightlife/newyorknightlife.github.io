# Content Template Lock + Publishing Standards (Step 6)

This document locks the default page structure for scalable NYC nightlife publishing.

## 1) Page Types

Use one of these templates for every new page:
- **Guide page** (`/guides/*`)
- **Neighborhood page** (`/neighborhoods/*`)
- **Tool page** (`/tools/*`)
- **Ranking page** (`/rankings/*`)

If a page does not clearly fit one type, default to **Guide page**.

## 2) Required Structure (all templates)

Every page must include:
1. SEO title tag (intent + NYC)
2. Meta description (120–160 chars)
3. Canonical URL
4. H1 (single)
5. Intro paragraph (clear value in first 2 sentences)
6. Main content sections with H2/H3 hierarchy
7. Internal links to at least 3 related pages
8. CTA block (plan/book/subscribe)
9. Affiliate disclosure when monetized links are present
10. Last updated date near footer/content end

## 3) SEO & On-Page Rules

- Include primary keyword in: title, H1, first paragraph, one H2.
- Keep one clear search intent per page (do not blend multiple intents).
- Use short paragraphs and scannable bullets.
- Add at least one table/list where it improves decision speed.
- Avoid thin pages; target useful depth over word-count vanity.

## 4) Internal Linking Rules

Minimum internal links per new page:
- 2 contextual links in body copy
- 1 hub link (guides/tools/neighborhoods index)
- 1 conversion-adjacent link (planner/tool/booking page)

Use descriptive anchor text (not “click here”).

## 5) Monetization Rules

When affiliate links appear:
- Include standardized disclosure language.
- Use proper rel attributes (`nofollow sponsored noopener`).
- Prefer high-intent placements (decision sections, comparison sections, final CTA).
- Do not overload above-the-fold with monetization links.

## 6) Publishing QA Checklist

Before publishing any page:
- [ ] Title/meta/canonical set
- [ ] H1 + clean heading structure
- [ ] Internal links added and tested
- [ ] External/affiliate links open correctly
- [ ] Mobile readability checked
- [ ] Page included in sitemap workflow
- [ ] Analytics events firing for key CTAs
- [ ] Spelling and factual accuracy pass complete

## 7) File Naming Convention

- Use lowercase kebab-case filenames.
- Include topic + nyc/nightlife context when helpful.
- Example: `best-thursday-night-spots-nyc.html`

## 8) Recommended Frontmatter Block (HTML comments)

At top of each new file, keep planning notes in comments during drafting:

```html
<!--
primary_intent: <one intent>
primary_keyword: <main keyword>
secondary_keywords: <k1, k2>
money_stage: discover | compare | book
last_updated: YYYY-MM-DD
-->
```

Remove or keep as internal note before production based on team preference.
