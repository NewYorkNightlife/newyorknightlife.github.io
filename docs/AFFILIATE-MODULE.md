# Affiliate Module + Disclosure Standard (Step 5)

## What this step adds

A reusable affiliate recommendation block is now injected on monetizable page types:
- guides
- tools
- things-to-do
- visit
- rankings
- categories
- tonight
- weekend

## Standardized disclosure

Each block includes this disclosure text:

> Affiliate disclosure: We may earn a commission if you book through these links, at no extra cost to you.

## Link standards

Affiliate links are rendered with:
- `target="_blank"`
- `rel="nofollow sponsored noopener"`

## Tracking

Clicks emit:
- `affiliate_link_click`

Payload:
- `from`
- `to`
- `label`

## Offer logic

- General pages: Eventbrite / Viator / GetYourGuide
- Visit + things-to-do pages: Booking.com / Viator / GetYourGuide

## Tracking parameters (UTM)

Affiliate module links now include UTM parameters for attribution:
- `utm_source=nynightlife`
- `utm_medium=affiliate_module`
- `utm_campaign=<section>` (guides/tools/visit/things_to_do/rankings/categories/tonight/weekend)
- `utm_content=<partner>`

This gives immediate monetization structure while we refine partner-specific deep links later.
