# Analytics & Event Tracking

## What this adds

`js/main.js` now includes a lightweight analytics bridge that can send events to:
- Google Analytics 4 (`window.gtag`)
- Plausible (`window.plausible`)
- Custom handler (`window.NYNTrackEvent`)

Tracked events currently include:
- `page_view`
- `outbound_click`
- `email_capture_success`
- `email_capture_fallback`
- `tool_spin_wheel_complete`
- `tool_budget_calculate`
- `tool_neighborhood_quiz_complete`
- `internal_link_recommendation_click`
- `affiliate_link_click`
- `conversion_cta_click`

## Recommended GA4 custom dimensions

In GA4 Admin → Custom definitions, add event-scoped dimensions for:
- `source`
- `from`
- `to`
- `label`
- `budget`
- `vibe`
- `recommendation`

This makes internal links, affiliate clicks, and tool interactions reportable in Explorations.

## How to enable GA4

Add this in `<head>` (replace measurement id):

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

## How to enable Plausible

Add this in `<head>` (replace domain):

```html
<script defer data-domain="newyorknightlife.github.io" src="https://plausible.io/js/script.js"></script>
```

## Notes

- Event calls are safe when analytics scripts are absent.
- Keep this file updated as new events are added.
