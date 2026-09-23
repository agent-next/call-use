# call-use-web

Marketing website for [call-use](https://github.com/agent-next/call-use) -- the open-source AI phone call runtime.

Live at [call-use.com](https://call-use.com)

## Tech Stack

- [Astro](https://astro.build/) v6 -- static site generator
- [Tailwind CSS](https://tailwindcss.com/) v4 -- styling
- [Cloudflare Workers](https://workers.cloudflare.com/) -- hosting & deployment

## Development

```sh
npm install
npm run dev
```

## Build & Deploy

```sh
npm run build          # Build to ./dist/
npm run preview        # Preview locally via Wrangler
npm run deploy         # Build + deploy to Cloudflare Workers
```

Deployment is configured via GitHub Actions (`workflow_dispatch` -- manual trigger only).

## Project Structure

```
src/
  components/    # Astro components (Nav, Hero, Features, etc.)
  layouts/       # Base HTML layout
  pages/         # Route pages (index only)
  styles/        # Global CSS + Tailwind theme
public/          # Static assets (favicon, OG image)
```

## License

Part of the [call-use](https://github.com/agent-next/call-use) project. MIT Licensed.
