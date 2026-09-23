# call-use Social Media Assets Specifications

---

## GitHub Organization Avatar

**Size:** 500x500px (renders at various sizes down to 20x20)

**Design:**
- Use `logo-icon.svg` as the source
- The icon is already designed as a square with rounded corners
- The indigo-to-violet gradient background ensures it stands out at small sizes
- The white phone handset + signal waves remain readable at 20px

**Export:** PNG at 500x500 from `assets/logo-icon.svg`

---

## GitHub Repository Social Preview

**Size:** 1280x640px

**Design:** Based on `assets/og-image.svg` with the following layout:

| Element | Position | Style |
|---------|----------|-------|
| Background | Full bleed | Slate 900 to Slate 800 gradient (`#0F172A` -> `#1E293B`) with subtle grid overlay |
| Top accent bar | Top edge, full width | 4px height, primary gradient |
| Logo icon | Left-center area (80px from left, vertically centered) | 140x140px, gradient background |
| Wordmark | Right of icon | 72px JetBrains Mono Bold; "call" in Indigo 400, "-" in Slate 500, "use" in Slate 100 |
| Tagline | Below wordmark | 28px Inter Regular, Slate 400: "The browser-use for phones" |
| Description | Lower-left | 28px Inter, Slate 500: "Open-source outbound call-control runtime for AI agents." |
| Install hint | Below description | Code block style: `$ pip install call-use` |
| URL | Bottom-left | 20px JetBrains Mono, Slate 600: "call-use.com" |
| Org name | Bottom-right | 20px JetBrains Mono, Slate 600: "agent-next" |

**File:** `assets/og-image.svg` (export to PNG at 1280x640)

---

## Twitter/X

### Avatar

**Size:** 400x400px (displayed as circle, 200x200 in timeline)

**Design:**
- Use `logo-icon.svg`
- Ensure the phone handset + waves are fully visible within the circular crop
- The rounded-square background works well within Twitter's circular mask since the icon content sits centered

**Export:** PNG at 400x400 from `assets/logo-icon.svg`

### Header Image

**Size:** 1500x500px

**Design:**

| Element | Position | Style |
|---------|----------|-------|
| Background | Full bleed | Slate 900 (`#0F172A`) with hero pattern overlay (`hero-pattern.svg`) |
| Logo + wordmark | Center, slightly left | `logo-dark.svg` at appropriate scale |
| Tagline | Below logo | 24px Inter, Slate 400: "The browser-use for phones" |
| URL | Bottom-right | 18px JetBrains Mono, Slate 600: "call-use.com" |

**Note:** Keep key content in the center 60% of the image -- Twitter crops edges on mobile.

---

## Open Graph Image

**Size:** 1200x630px (standard OG image dimensions)

**Design:** Same as GitHub social preview. Use `assets/og-image.svg`.

**Meta tags for website:**
```html
<meta property="og:image" content="https://call-use.com/og-image.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="call-use: The browser-use for phones" />
<meta property="og:title" content="call-use" />
<meta property="og:description" content="Open-source outbound call-control runtime for AI agents" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="https://call-use.com/og-image.png" />
```

---

## Favicon Set

All derived from `assets/favicon.svg`.

| Size | Format | Usage |
|------|--------|-------|
| SVG | SVG | Modern browsers (`<link rel="icon" type="image/svg+xml">`) |
| 16x16 | PNG | Classic favicon |
| 32x32 | PNG | High-DPI classic favicon |
| 180x180 | PNG | Apple touch icon |
| 192x192 | PNG | Android Chrome |
| 512x512 | PNG | PWA icon, manifest |

**HTML implementation:**
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
<link rel="manifest" href="/site.webmanifest" />
<meta name="theme-color" content="#6366F1" />
```

**Manifest file (`site.webmanifest`):**
```json
{
  "name": "call-use",
  "short_name": "call-use",
  "icons": [
    { "src": "/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png" }
  ],
  "theme_color": "#6366F1",
  "background_color": "#0F172A",
  "display": "standalone"
}
```

---

## Platform Handle Strategy

Claim these handles/names consistently:

| Platform | Handle / Name | Status |
|----------|---------------|--------|
| GitHub org | `agent-next` | Active |
| GitHub repo | `agent-next/call-use` | To create |
| Twitter/X | `@calluse` or `@call_use` | Claim |
| PyPI | `call-use` | Register |
| npm | `call-use` | Register (if JS SDK planned) |
| Discord | call-use | Create server |
| Domain | `call-use.com` | Registered |
| Domain | `docs.call-use.com` | Subdomain |

---

## Asset Export Checklist

When preparing assets for deployment:

- [ ] Export all SVGs to PNG at required sizes using a tool like `cairosvg`, Inkscape CLI, or Figma
- [ ] Optimize PNGs with `oxipng` or `pngquant`
- [ ] Validate OG image renders correctly with https://www.opengraph.xyz/
- [ ] Validate favicon set with https://realfavicongenerator.net/
- [ ] Test GitHub social preview by temporarily setting it on a test repo
- [ ] Verify Twitter card with https://cards-dev.twitter.com/validator
