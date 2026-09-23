# call-use Brand Identity System

Brand assets, guidelines, and identity specifications for [call-use](https://call-use.com) -- the browser-use for phones.

## Contents

| File | Description |
|------|-------------|
| [`brand-guidelines.md`](brand-guidelines.md) | Complete brand guidelines: colors, typography, voice, logo specs, code theme |
| [`social-assets.md`](social-assets.md) | Social media asset specifications and export checklist |
| [`ip-checklist.md`](ip-checklist.md) | Intellectual property protection: trademarks, domains, CLA, brand policy |

## Assets

| File | Description | Preview |
|------|-------------|---------|
| [`assets/logo.svg`](assets/logo.svg) | Full logo (icon + wordmark) | For light backgrounds |
| [`assets/logo-icon.svg`](assets/logo-icon.svg) | Icon only (512x512) | Avatars, favicons, app icons |
| [`assets/logo-wordmark.svg`](assets/logo-wordmark.svg) | Wordmark only | Horizontal-constrained contexts |
| [`assets/logo-dark.svg`](assets/logo-dark.svg) | Full logo, dark variant | For dark backgrounds |
| [`assets/logo-light.svg`](assets/logo-light.svg) | Full logo, light variant | For light backgrounds |
| [`assets/favicon.svg`](assets/favicon.svg) | SVG favicon | Browser tabs |
| [`assets/og-image.svg`](assets/og-image.svg) | Open Graph image template | Link previews (1200x630) |
| [`assets/hero-pattern.svg`](assets/hero-pattern.svg) | Background pattern | Hero sections, headers |

## Quick Reference

### Colors

| Role | Hex | Swatch |
|------|-----|--------|
| Primary (Indigo 500) | `#6366F1` | ![#6366F1](https://via.placeholder.com/16/6366F1/6366F1.png) |
| Accent (Violet 500) | `#8B5CF6` | ![#8B5CF6](https://via.placeholder.com/16/8B5CF6/8B5CF6.png) |
| Dark BG (Slate 900) | `#0F172A` | ![#0F172A](https://via.placeholder.com/16/0F172A/0F172A.png) |
| Light BG (Slate 50) | `#F8FAFC` | ![#F8FAFC](https://via.placeholder.com/16/F8FAFC/F8FAFC.png) |

### Fonts

- **Headings:** JetBrains Mono (SemiBold/Bold)
- **Body:** Inter (Regular/Medium)
- **Code:** JetBrains Mono (Regular)

### Gradient

```css
background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
```

## Usage

The call-use name and logo are trademarks of agent-next. The MIT license for the call-use source code does not grant permission to use these trademarks. See [`ip-checklist.md`](ip-checklist.md) for full trademark policy.

## Exporting Raster Assets

To generate PNGs from the SVG sources:

```bash
# Using cairosvg (pip install cairosvg)
cairosvg assets/logo-icon.svg -o logo-icon-512.png -W 512 -H 512
cairosvg assets/favicon.svg -o favicon-32.png -W 32 -H 32
cairosvg assets/og-image.svg -o og-image.png -W 1200 -H 630

# Using Inkscape CLI
inkscape assets/logo-icon.svg --export-filename=logo-icon-512.png -w 512 -h 512
```
