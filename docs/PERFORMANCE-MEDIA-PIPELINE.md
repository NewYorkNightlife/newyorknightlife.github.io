# Performance + Media Pipeline Standards (Step 7)

This standard prevents oversized images and layout regressions as content scales.

## 1) Image Size Standards

Use these target dimensions by placement:

- **Hero background (desktop):** 1920x1080 (or 2560x1440 source)
- **Hero background (mobile crop):** 1080x1350
- **Card/thumbnail image:** 1200x675
- **Blog feature image:** 1600x900
- **Open Graph/Twitter image:** 1200x630

Avoid portrait-only images for full-width desktop backgrounds.

## 2) File Format Standards

- Prefer **WebP** for most content images.
- Use JPG only when needed for compatibility/source constraints.
- Keep PNG for transparency/UI graphics only.

## 3) File Size Budgets

Per image target caps:
- Hero background: <= 500 KB
- Feature images: <= 300 KB
- Thumbnails/cards: <= 180 KB
- Icons/UI assets: <= 80 KB

Page-level target:
- Keep total page transfer practical for mobile (avoid multi-MB pages).

## 4) Naming Convention

Use lowercase kebab-case names and include context:
- `nyc-nightlife-skyline-hero.webp`
- `lower-east-side-cocktail-bars-1200x675.webp`

Avoid generic names like `image1.jpg`.

## 5) CSS Background Rules

For cinematic backgrounds:
- `background-size: cover`
- `background-position: center top` for skyline/tall-subject compositions

If mobile framing differs, use a mobile-specific override in media queries.

## 6) Loading Rules

- Add `loading="lazy"` for non-critical images.
- Keep hero-critical assets optimized because they load immediately.
- Avoid auto-playing heavy media in first viewport.

## 7) QA Checklist (before merge)

- [ ] Correct dimensions for placement
- [ ] File size within budget
- [ ] Proper format (WebP/JPG/PNG)
- [ ] Mobile + desktop visual framing checked
- [ ] No CLS/layout jump introduced
- [ ] Lighthouse/performance spot check completed

## 8) Optional Local Conversion Commands

If tools are installed, typical conversions:

```bash
# JPG -> WebP (quality 82)
cwebp input.jpg -q 82 -o output.webp

# Resize with ImageMagick
magick input.jpg -resize 1920x1080^ -gravity center -extent 1920x1080 output.jpg
```

Use quality settings that balance visual fidelity and speed.
