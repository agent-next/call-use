# call-use Brand Guidelines

Version 1.0 | March 2026

---

## Brand Story

### Mission

Democratize phone call automation for AI agents. Every developer building an AI agent should be able to add outbound calling in minutes, not months.

### Vision

Every AI agent can communicate by phone as naturally as browsing the web. Just as browser-use made web interaction trivial for agents, call-use makes phone calls a first-class capability.

### Values

- **Open source** -- The runtime is MIT-licensed. The community builds, extends, and owns it.
- **Simplicity** -- A single `pip install` to calling capability. No telephony expertise required.
- **Reliability** -- Production-grade call control. Agents should be able to depend on the runtime in critical workflows.
- **Developer-first** -- API design, documentation, and tooling all optimize for the developer experience.

### Positioning

call-use is the **browser-use for phones**: an open-source outbound call-control runtime that gives AI agents the ability to make, manage, and respond during phone calls. It targets AI/ML developers and agent framework builders who need telephony as a tool, not a product.

---

## Logo

### Concept

The call-use logo combines a **phone handset** with **code angle brackets** (`< >`) and **signal waves**, enclosed in a rounded square. This conveys:

- Phone/call: the handset silhouette
- Code/developer: the angle brackets framing the icon
- Active communication: the signal wave arcs
- Software product: the rounded-square app-icon shape

### Primary Mark

The full logo consists of the icon (rounded square with handset + brackets + waves) alongside the "call-use" wordmark.

**Files:**
- `assets/logo.svg` -- Full logo (icon + wordmark), light background
- `assets/logo-icon.svg` -- Icon only (512x512)
- `assets/logo-wordmark.svg` -- Wordmark only

### Variants

| Variant | File | Use case |
|---------|------|----------|
| Light background | `assets/logo-light.svg` | White or light gray backgrounds |
| Dark background | `assets/logo-dark.svg` | Dark backgrounds (#0F172A, etc.) |
| Icon only | `assets/logo-icon.svg` | Favicons, avatars, app icons |
| Wordmark only | `assets/logo-wordmark.svg` | Horizontal space-constrained contexts |

### Clear Space

Maintain a minimum clear space equal to the height of the letter "c" in the wordmark on all sides of the logo. No other graphic elements should intrude into this space.

### Minimum Size

- Full logo: minimum 120px wide
- Icon only: minimum 16px (favicon) -- the SVG is designed to remain legible at this size
- Wordmark only: minimum 80px wide

### Misuse

Do not:
- Rotate or skew the logo
- Change the logo colors outside the defined palette
- Add drop shadows, outlines, or effects
- Place the logo on busy or low-contrast backgrounds
- Alter the proportions of icon to wordmark
- Recreate the logo in a different font

---

## Color Palette

### Primary

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Indigo 500 | `#6366F1` | 99, 102, 241 | Primary brand color, "call" text, buttons, links |
| Violet 500 | `#8B5CF6` | 139, 92, 246 | Gradient end, accent highlights |

### Secondary

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Indigo 400 | `#818CF8` | 129, 140, 248 | Dark-mode primary, hover states |
| Violet 400 | `#A78BFA` | 167, 139, 250 | Dark-mode accent |

### Neutrals

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Slate 900 | `#0F172A` | 15, 23, 42 | Dark background, "use" text (light mode) |
| Slate 800 | `#1E293B` | 30, 41, 59 | Card background (dark mode), code blocks |
| Slate 700 | `#334155` | 51, 65, 85 | Borders (dark mode) |
| Slate 600 | `#475569` | 71, 85, 105 | Muted text (dark mode) |
| Slate 500 | `#64748B` | 100, 116, 139 | Muted text, secondary content |
| Slate 400 | `#94A3B8` | 148, 163, 184 | Placeholder text, hyphen in logo |
| Slate 200 | `#E2E8F0` | 226, 232, 240 | Borders (light mode) |
| Slate 100 | `#F1F5F9` | 241, 245, 249 | Light background, "use" text (dark mode) |
| Slate 50 | `#F8FAFC` | 248, 250, 252 | Page background (light mode) |

### Semantic

| Name | Hex | Usage |
|------|-----|-------|
| Success | `#10B981` | Passing tests, connected states |
| Warning | `#F59E0B` | Warnings, degraded states |
| Error | `#EF4444` | Errors, failed states, disconnected |
| Info | `#3B82F6` | Informational callouts |

### Gradients

**Primary gradient (icon background, hero accents):**
```css
background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
```

**Dark background gradient:**
```css
background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
```

### Color Usage Rules

- The primary indigo (`#6366F1`) is reserved for interactive elements and the "call" portion of the wordmark.
- Never use the primary color for large background fills -- it is an accent.
- Dark mode should use Indigo 400 / Violet 400 variants for sufficient contrast.
- Code blocks always use Slate 800 (`#1E293B`) background in both light and dark modes.
- Maintain WCAG AA contrast ratios minimum (4.5:1 for text, 3:1 for large text).

---

## Typography

### Font Stack

| Role | Font | Fallback | Weight |
|------|------|----------|--------|
| Headings | JetBrains Mono | SF Mono, Fira Code, monospace | 600 (SemiBold), 700 (Bold) |
| Body | Inter | -apple-system, system-ui, sans-serif | 400 (Regular), 500 (Medium) |
| Code | JetBrains Mono | SF Mono, Fira Code, Consolas, monospace | 400 (Regular) |

Both JetBrains Mono and Inter are available on Google Fonts (free, open source).

### Type Scale

Based on a 1.25 ratio (Major Third):

| Element | Size | Line Height | Weight | Font |
|---------|------|-------------|--------|------|
| Display | 48px / 3rem | 1.1 | 700 | JetBrains Mono |
| H1 | 36px / 2.25rem | 1.2 | 700 | JetBrains Mono |
| H2 | 28px / 1.75rem | 1.3 | 600 | JetBrains Mono |
| H3 | 22px / 1.375rem | 1.4 | 600 | JetBrains Mono |
| H4 | 18px / 1.125rem | 1.4 | 600 | JetBrains Mono |
| Body | 16px / 1rem | 1.6 | 400 | Inter |
| Body small | 14px / 0.875rem | 1.5 | 400 | Inter |
| Caption | 12px / 0.75rem | 1.4 | 500 | Inter |
| Code | 14px / 0.875rem | 1.6 | 400 | JetBrains Mono |

### Usage Rules

- Headings use a monospace font (JetBrains Mono) to reinforce the developer/code identity.
- Body text uses Inter for readability in documentation and marketing.
- All code snippets, terminal output, and API references use JetBrains Mono at 14px.
- Do not use heading fonts for body-length text; do not use body fonts for headings.

---

## Voice & Tone

### Principles

1. **Technical but accessible.** Assume the reader writes code. Don't explain what an API is. Do explain call-use-specific concepts clearly.

2. **Confident, not hype-y.** Say what the tool does. Don't say it's "revolutionary" or "game-changing." Let the capability speak.

3. **Code-first.** Lead with a code example, not a paragraph. If a concept can be shown in 5 lines of Python, show the code first, explain second.

4. **Brief and scannable.** Short paragraphs. Bullet points. Tables. Headers. Developers scan; don't make them read walls of text.

5. **Direct.** Use active voice. "call-use connects your agent to the phone network" not "your agent is connected to the phone network by call-use."

### Do

- Start docs pages with a working code example
- Use "you" and "your" to address the developer directly
- Use present tense ("call-use handles..." not "call-use will handle...")
- Provide copy-pasteable commands and snippets
- Be honest about limitations

### Don't

- Use emojis in documentation or product interfaces
- Use superlatives ("best," "fastest," "most powerful")
- Use buzzwords ("leverage," "synergy," "next-gen")
- Use hedging language ("might," "could potentially," "should hopefully")
- Assume non-technical context -- the audience writes code for a living

### Example Tone

**Good:**
```
call-use gives your AI agent the ability to make outbound phone calls.

    from call_use import CallAgent

    agent = CallAgent(phone_number="+1234567890")
    result = await agent.call(prompt="Schedule a dentist appointment for Thursday")

That's it. The agent dials, navigates the IVR, talks to a human, and returns a structured result.
```

**Bad:**
```
Introducing call-use -- the revolutionary new platform that leverages cutting-edge AI
to transform how agents interact with the telephone network! With our next-generation
runtime, you can potentially enable your agents to make phone calls in ways never
before possible!
```

---

## Code / Terminal Theme

Syntax highlighting colors that align with the brand palette, designed for dark backgrounds (`#1E293B`).

| Element | Hex | Example |
|---------|-----|---------|
| Background | `#1E293B` | -- |
| Foreground (default text) | `#E2E8F0` | general code |
| Comment | `#64748B` | `# this is a comment` |
| String | `#10B981` | `"hello world"` |
| Keyword | `#818CF8` | `import`, `from`, `async`, `await` |
| Function / method | `#A78BFA` | `agent.call()` |
| Variable / parameter | `#E2E8F0` | `result` |
| Number / constant | `#F59E0B` | `42`, `True` |
| Operator | `#94A3B8` | `=`, `+`, `==` |
| Type / class | `#6366F1` | `CallAgent` |
| Property / attribute | `#38BDF8` | `.phone_number` |
| Punctuation | `#64748B` | `()`, `{}`, `:` |
| Selection background | `#334155` | -- |
| Line highlight | `#1E293B` | -- |
| Gutter | `#475569` | line numbers |

### CSS Custom Properties

```css
:root {
  --code-bg: #1E293B;
  --code-fg: #E2E8F0;
  --code-comment: #64748B;
  --code-string: #10B981;
  --code-keyword: #818CF8;
  --code-function: #A78BFA;
  --code-variable: #E2E8F0;
  --code-number: #F59E0B;
  --code-operator: #94A3B8;
  --code-type: #6366F1;
  --code-property: #38BDF8;
  --code-punctuation: #64748B;
}
```

---

## README Badges

Use a consistent color scheme across all repository badges. Style: `flat` (shields.io).

### Badge Definitions

| Badge | Color | Example |
|-------|-------|---------|
| Version / PyPI | `#6366F1` (brand indigo) | `![PyPI](https://img.shields.io/pypi/v/call-use?color=6366F1&style=flat)` |
| Build status | `#10B981` (success green) | `![Build](https://img.shields.io/github/actions/workflow/status/agent-next/call-use/ci.yml?style=flat)` |
| Coverage | `#8B5CF6` (brand violet) | `![Coverage](https://img.shields.io/codecov/c/github/agent-next/call-use?color=8B5CF6&style=flat)` |
| License | `#94A3B8` (slate) | `![License](https://img.shields.io/github/license/agent-next/call-use?color=94A3B8&style=flat)` |
| Python version | `#3B82F6` (info blue) | `![Python](https://img.shields.io/pypi/pyversions/call-use?color=3B82F6&style=flat)` |
| Downloads | `#818CF8` (indigo 400) | `![Downloads](https://img.shields.io/pypi/dm/call-use?color=818CF8&style=flat)` |

### Badge Order in README

```markdown
[![PyPI](https://img.shields.io/pypi/v/call-use?color=6366F1&style=flat)](https://pypi.org/project/call-use/)
[![Build](https://img.shields.io/github/actions/workflow/status/agent-next/call-use/ci.yml?style=flat)](https://github.com/agent-next/call-use/actions)
[![Coverage](https://img.shields.io/codecov/c/github/agent-next/call-use?color=8B5CF6&style=flat)](https://codecov.io/gh/agent-next/call-use)
[![License](https://img.shields.io/github/license/agent-next/call-use?color=94A3B8&style=flat)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/call-use?color=3B82F6&style=flat)](https://pypi.org/project/call-use/)
```

---

## Spacing & Layout

### Spacing Scale

Based on 4px base unit:

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Icon padding, tight gaps |
| `sm` | 8px | Inline spacing, badge gaps |
| `md` | 16px | Default spacing, card padding |
| `lg` | 24px | Section spacing |
| `xl` | 32px | Major section breaks |
| `2xl` | 48px | Page section spacing |
| `3xl` | 64px | Hero spacing |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | 4px | Badges, small buttons |
| `md` | 8px | Cards, inputs, code blocks |
| `lg` | 12px | Large cards, modals |
| `xl` | 16px | Hero elements |
| `icon` | 20% | Logo icon rounded square |

---

## Application Examples

### Website Header (Light Mode)

- Background: `#F8FAFC` (Slate 50)
- Logo: `logo-light.svg`
- Navigation text: `#0F172A` (Slate 900)
- Active nav link: `#6366F1` with 2px bottom border
- CTA button: `#6366F1` background, white text, 8px radius

### Website Header (Dark Mode)

- Background: `#0F172A` (Slate 900)
- Logo: `logo-dark.svg`
- Navigation text: `#F1F5F9` (Slate 100)
- Active nav link: `#818CF8` with 2px bottom border
- CTA button: `#818CF8` background, Slate 900 text, 8px radius

### Documentation Page

- Sidebar background: `#F8FAFC`
- Active sidebar item: `#6366F1` left border, `#EEF2FF` background
- Code blocks: `#1E293B` background, syntax theme as defined above
- Inline code: `#EEF2FF` background, `#6366F1` text, 4px radius
- Links: `#6366F1`, underline on hover

### GitHub README

- Lead with the full logo SVG
- Badges row immediately below
- One-line description in regular text
- Install command in a code block
- 5-line quickstart example
- Keep above-the-fold content minimal -- link to docs for depth
