# Email Capture Integration

## What was added

All `.email-form` forms now submit through a shared JavaScript pipeline in `js/main.js`.

Submission payload:
- `email`
- `source` (pathname)
- `page_url`
- `captured_at` (ISO timestamp)

If no endpoint is configured or provider fails, leads are still saved in local storage under:
- `nynightlife_email_leads`

## Configure provider endpoint

Use one of these methods (priority order):

1. Per-form endpoint:
```html
<form class="email-form" data-endpoint="https://YOUR_ENDPOINT">
```

2. Page-level endpoint:
```html
<meta name="nyn-email-endpoint" content="https://YOUR_ENDPOINT">
```

3. Global endpoint:
```html
<script>window.NYN_EMAIL_ENDPOINT = "https://YOUR_ENDPOINT";</script>
```

## Recommended providers

- ConvertKit Forms/API
- MailerLite API
- Formspree endpoint forwarding into your ESP

## Notes

- Button states now reflect submit lifecycle (`Saving…`, success messages, reset state).
- Events are emitted via `trackEvent()` for later analytics wiring.
- Keep endpoint server-side validation enabled to prevent abuse/spam.
