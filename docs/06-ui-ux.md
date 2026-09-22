# UI / UX System

Design language: Apple-inspired, dark, minimal, soft, purple accent.

## Principles

1. **Calm surface** — near-black background, low-contrast cards, no visual noise.
2. **Content first** — typography does the hierarchy, not boxes and lines.
3. **One accent** — purple is the only saturated color; statuses are pastel.
4. **Motion is subtle** — micro-transitions only (150–250ms). No bounces.
5. **Information density** — clean tables, generous row height, muted metadata.
6. **Consistency** — same statuses, same badges, same input, same spacing everywhere.

## Palette

Background
- `--bg`        #0a0a0b  page
- `--bg-elev`   #131316  raised surfaces
- `--bg-card`   rgba(255,255,255,0.03)  glass card
- ambient radial purple glows on the page top-left and top-right

Borders
- `--border`        rgba(255,255,255,0.07)
- `--border-strong` rgba(255,255,255,0.12)

Text
- `--text`      #f5f5f7  primary
- `--text-dim`  #8e8e93  secondary
- `--text-mute` #6e6e73  tertiary

Accent
- `--accent`   #a855f7
- `--accent-2` #7c3aed
- `--accent-glow` rgba(168,85,247,0.28)

Statuses (pastel fg on 10–12% alpha bg)
- success  #86efac / emerald
- warning  #fcd34d / amber
- danger   #fca5a5 / red
- info     #93c5fd / blue
- neutral  #d4d4d8 / white
- accent   #d8b4fe / purple

## Typography

Font stack: `-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Inter, system-ui, sans-serif`

Scale
- Page title         text-3xl font-semibold  (30px)
- Section title      text-lg font-semibold   (18px)
- Card label         text-xs uppercase tracking-widest text-dim
- Body               text-sm                 (14px)
- Metadata           text-xs                 (12px)
- Metric number      text-2xl/3xl font-semibold

Rules
- No `font-bold`. Maximum weight is `font-semibold`.
- Uppercase only for section labels and small metadata.
- Letter-spacing -0.01em globally for a soft feel.
- Money and IDs use `font-mono`.

## Spacing

- Base unit: 4px
- Card padding: 20–24px (p-5 / p-6)
- Section gap: 16px (gap-4) / 24px (mb-6)
- Page padding: 28px (p-7)
- Input height: ~40px (.7rem vertical padding)

## Radii

- Buttons & pills: 999px (fully rounded)
- Inputs: 12px
- Cards: 16px
- Large glass panels: 18–20px

## Components

### Card
- `.glass` — background + border + backdrop blur
- 16px radius
- Hover variant `.glass-hover` lifts border and background slightly (no shadow)

### Button
Three variants, all pill-shaped, 14px font:
- `.btn-primary` — purple gradient, glow shadow, subtle lift on hover
- `.btn-ghost` — transparent with border, lightens on hover
- `.btn-danger` — pastel red on 12% alpha

Rules
- Icons precede labels, never sit alone without a title attribute
- Compact variants use `!py-1 !px-3 text-xs` inside tables
- Never two primary buttons side by side

### Input
- 12px radius, 3% white background, subtle border
- Focus: 3px purple ring at 12% alpha + accent border
- Labels: uppercase, 11px, tracking-wide, dim color
- Select uses custom chevron SVG

### StatusBadge
Pill: pastel text on 10–12% alpha bg, 1.5px glowing dot before text.
Domains: order, delivery, driver, task, assignment, route, org, channel.
All lowercase humanized labels (`in_transit` → `in transit`).

### Skeleton
- Shimmer gradient sweeping 200% width over 1.4s
- Used for: table rows, card grids, page headers
- Never show a spinner; always show a skeleton of the actual content shape

### Toaster
- Top-right stack, 320px wide
- 12px radius, pastel bg, colored left icon dot
- Click to dismiss. Auto-dismiss at 4s.
- Only for errors (auto) and explicit user actions (success/info)

### TopProgressBar
- 2px purple gradient bar at the very top of the viewport
- Fires on route change and while React Query is fetching or mutating
- Fades out over 200ms at 100%

### Table
- No vertical lines, subtle row separators
- Header: 11px uppercase dim
- Rows: 14px, ~48px height, hover tint 1.5% white
- Right-align numeric and money columns
- Row click navigates to detail (whole row is a pointer target)

### Map
- Carto/OSM dark tiles
- Colored circular markers with glow
- Used on dispatch (drivers + pending deliveries) and public tracking
- No scroll zoom (prevents accidental zoom while scrolling)

## Layouts

Admin / Dispatcher / Warehouse
- Left sidebar 240px, brand + live dot on top, nav links, user footer with sign out
- Main content max-w-6xl, p-7

Driver
- Top nav (mobile-first)
- Wide cards, big tap targets
- Actions are full-width pills

Marketing / Auth / Public tracking
- Centered card on dark ambient background
- Same glass aesthetics

## Motion

- Transitions: 150–250ms ease
- Hover: translateY(-1px) + brightness only on primary buttons
- Progress bar: 250ms width transition
- Toasts: 200ms fade + slide-down on entry
- No parallax. No scale. No rotation.

## Accessibility

- Focus visible: purple ring on inputs and buttons
- Minimum contrast: body text #f5f5f7 on #0a0a0b = 17:1
- Dim text #8e8e93 on #0a0a0b = 7.6:1 (AA for normal text)
- Tap targets ≥ 36px
- Color is never the only signal — status pills include a text label
- All form inputs have labels (uppercase text)
- All buttons are real buttons, all navigation is real links

## Empty states

- Large, centered, minimal
- One-line description + one primary CTA
- Example: “No orders yet.” → “Create your first order”

## Loading

- Skeleton of the actual layout shape (rows, cards, charts)
- No spinners, ever
- Top progress bar on top of that for extra reassurance

## Anti-patterns (avoid)

- Bold text everywhere
- Multiple accent colors
- Drop shadows heavier than the purple button glow
- Pure black (#000) or pure white (#fff)
- Full-width tables without alignment to a container
- Icons without labels in navigation
- Modal dialogs for simple confirmations (use inline actions)