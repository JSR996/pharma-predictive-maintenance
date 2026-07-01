---
name: PharmaGuard
description: Instrument-grade predictive-maintenance dashboard for pharma manufacturing equipment.
colors:
  bg: "#EEF4FB"
  surface: "#FFFFFF"
  surface-inset: "#F1F5FB"
  border: "#DBE7F3"
  brand: "#1D4ED8"
  normal: "#16A34A"
  warning: "#B45309"
  warning-graphic: "#D97706"
  critical: "#DC2626"
  ink: "#12233B"
  subtext: "#5B7089"
  muted: "#94A3B8"
  track: "#E2E8F0"
  scrollbar-thumb: "#CBD9EA"
  chart-temperature: "#D97706"
  chart-vibration: "#DC2626"
  chart-pressure: "#1D4ED8"
  chart-rpm: "#0E7490"
typography:
  display:
    fontFamily: "'Space Grotesk', sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "normal"
  headline:
    fontFamily: "'Space Grotesk', sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "normal"
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.625rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.1em"
  mono:
    fontFamily: "'JetBrains Mono', monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
rounded:
  sm: "3px"
  md: "8px"
  lg: "12px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  equipment-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "16px"
  sensor-tile:
    backgroundColor: "{colors.surface-inset}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "6px 8px"
  status-pill:
    backgroundColor: "{colors.surface-inset}"
    textColor: "{colors.subtext}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  button-primary:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "6px 8px"
  button-ghost:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.brand}"
    rounded: "{rounded.md}"
    padding: "6px 8px"
  toast:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
---

# Design System: PharmaGuard

## 1. Overview

**Creative North Star: "The Cleanroom Readout"**

PharmaGuard is the display panel of a precision lab instrument, rendered for a bright pharma
cleanroom rather than a dark control booth. The canvas is a blue-tinted white (`#EEF4FB`) — the
light, controlled, low-noise surface of a GMP suite — and the data sits on crisp white cards that
lift off it with a soft neutral shadow. Brand blue (`#1D4ED8`) is the instrument's UI accent: it
marks what you can touch (selection, focus, the "Live" pill, the primary action) and nothing else.
Health is spoken in the clinical vocabulary every operator already knows — **green, amber, red** —
so a well-running fleet reads calmly green, and severity earns attention only when a unit actually
degrades.

Density is purposeful: a three-pane operations layout (equipment list · live charts · alert feed)
on desktop that collapses to a single readable column on a phone. The signature element is the
**RUL degradation arc** — a 220° SVG gauge that sweeps green → amber → red as remaining useful life
falls. It is an instrument readout, never a fitness ring or a percentage bar.

This system explicitly rejects the generic SaaS admin panel (templated card grids, hero-metric stat
tiles), the consumer fitness/IoT look (playful gradients, emoji, gamified rings), enterprise SCADA
clutter (gray gradients, beveled skeuomorphic gauges), and the crypto/trading terminal (neon
hyperactivity, ambient blinking). It also rejects the dark-dashboard tropes it was born from: no
neon glows, no glassmorphism.

**Key Characteristics:**
- Blue-tinted white canvas; white cards lift on a soft neutral shadow, not a glow.
- Brand blue is a UI accent only; a healthy fleet reads green, never blue.
- Status escalates green → amber → red on real severity, never for decoration.
- Monospace for every number — telemetry reads as instrument output.
- The RUL degradation arc is the signature, non-negotiable component.
- Motion is reserved for meaning (the critical pulse, action feedback), never ambient.

## 2. Colors

A calm blue-tinted-white field with one brand blue accent and a strict green→amber→red severity
escalation borrowed from clinical convention.

### Primary
- **Pharma Blue** (`#1D4ED8`): The single UI/brand accent. Selection rings, keyboard focus, the
  "Live" connection pill, the brand mark, the primary/maintenance button, info alerts, and the
  pressure chart line. It signals "interactive / on-brand", never health. Used sparingly.

### Secondary — Status (clinical green/amber/red)
- **Healthy Green** (`#16A34A`): Normal status. The healthy RUL arc, normal card wash, the "normal"
  legend dot/count, healthy anomaly score. A running fleet is green.
- **Warning Amber** (`#B45309` text, `#D97706` graphics): Degradation has begun (RUL < 50 cycles).
  The darker amber is used wherever amber is **text** (it clears WCAG AA on white); the brighter
  `#D97706` is used for **graphics** — the warning arc segment, health-meter fill, temperature chart
  line — where the 3:1 graphical threshold applies and the vivid tone reads better.
- **Critical Red** (`#DC2626`): Imminent failure (RUL < 20 cycles). Critical status, the header
  pulse, failed/anomaly badges, the critical arc segment, the vibration chart line.

### Neutral
- **Cleanroom Page** (`#EEF4FB`): The blue-tinted page background. Bright, controlled, recessive.
- **Card Surface** (`#FFFFFF`): Cards, the alert feed, chart containers, toasts.
- **Inset Surface** (`#F1F5FB`): Sensor tiles, pills, badges, the scrollbar track — insets nested
  within a white surface.
- **Hairline Border** (`#DBE7F3`): 1px borders and dividers.
- **Gauge/Grid Track** (`#E2E8F0`): The unfilled RUL arc track and the Recharts gridlines.
- **Navy Ink** (`#12233B`): Headings, equipment names, primary values.
- **Subtext** (`#5B7089`): Secondary labels, alert messages, axis ticks — the muted tone that still
  clears AA on white.
- **Deep Muted** (`#94A3B8`): Disabled/dim glyphs and chart tick labels only. Not for body text.

### Named Rules
**The Brand-Is-Not-Status Rule.** Blue means "you can touch this", never "this is healthy". Health
is green/amber/red only. If a healthy unit ever renders blue, that's a bug — a resting fleet reads
green.

**The Clinical-Escalation Rule.** Status escalates green → amber → red and never skips a step or
decorates with it. Amber and red on screen are signals, not styling.

**The Lit-Data-Is-Dead Rule.** This is a light theme: color belongs to data via solid fills and
legible text, not glow. No `drop-shadow`/`box-shadow` in a status color to fake illumination.

## 3. Typography

**Display Font:** Space Grotesk (with sans-serif fallback) — weights 400–700
**Body Font:** Inter (with sans-serif fallback) — weights 300–600
**Label/Mono Font:** JetBrains Mono (with monospace fallback) — weights 400–500

**Character:** A geometric-grotesk display (Space Grotesk) paired with a neutral humanist body
(Inter) and a true monospace for telemetry. The contrast is structural — grotesk headings, humanist
prose, mono numbers — so the three roles never blur.

### Hierarchy
- **Display** (Space Grotesk, 700, ~1.125rem, lh 1.1): Selected-equipment name, fleet count,
  PharmaGuard wordmark.
- **Headline** (Space Grotesk, 600, ~1rem, lh 1.2): Card equipment names, panel titles.
- **Body** (Inter, 400, 0.875rem, lh 1.5): Alert messages, descriptive copy, empty states.
- **Label** (Inter, 500, 0.625rem, tracking 0.1em, UPPERCASE): Sensor labels, section eyebrows,
  status text — tracked and uppercase to read as instrument legends.
- **Mono** (JetBrains Mono, 400–500, 0.75rem): Every number that is telemetry — equipment IDs,
  sensor values, anomaly %, timestamps, cycle counts.

### Named Rules
**The Numbers-Are-Mono Rule.** Any value the model produces or the stream reports is set in
JetBrains Mono. Prose is Inter, headings are Space Grotesk, data is mono — no exceptions. It makes
telemetry read as instrument output and keeps digits from reflowing as they tick.

## 4. Elevation

Depth comes from a **soft neutral shadow** lifting white cards off the blue-tinted page, plus tonal
insets within a card. There are no colored glows — this is the deliberate break from the system's
dark-theme origin. Surfaces layer page (`#EEF4FB`) → card (`#FFFFFF`, `shadow-sm`) → inset
(`#F1F5FB`). Toasts float one step higher with a `shadow-md`.

### Shadow Vocabulary
- **Card lift** (`box-shadow: 0 1px 2px rgba(18,35,59,0.06)` — Tailwind `shadow-sm`): The resting
  elevation of every white card, feed, and chart container against the tinted page.
- **Toast lift** (`box-shadow: 0 4px 6px -1px rgba(18,35,59,0.10)` — Tailwind `shadow-md`): The one
  floating overlay — result toasts sit above the plane.

### Named Rules
**The Soft-Shadow Rule.** Cards lift on a soft neutral shadow, never a colored glow. If a shadow is
tinted to a status color, it's wrong — remove it and let the fill and border carry the meaning.

## 5. Components

### Buttons
- **Shape:** Rounded (12px `rounded-xl` on cards-as-buttons; 8px `rounded-lg` on real buttons; pills
  fully rounded).
- **Primary (maintenance / confirm):** Solid brand blue (`#1D4ED8`) with white text; used for the
  primary action on a failed unit and the armed "Confirm reset" state.
- **Ghost (maintenance, healthy/degraded):** Brand-blue text on a 1px `border-brand/30`, filling to
  `bg-brand/10` on hover. On healthy units it stays hidden until card hover/focus (calm by default).
- **Cards-as-buttons:** Equipment cards are the primary interactive surface — full keyboard-operable
  elements with a status-tinted border and faint status wash.
- **Hover / Focus:** `hover:border-brand/40`; focus shows `ring-2 ring-brand/40`. Selected state is a
  stronger `ring-brand/60` + `border-brand/50`. Transitions 150–200ms.

### Inline Confirm (maintenance guard)
The maintenance action is guarded without a modal. First click **arms** the card: the button morphs
into a `[Confirm reset]` primary button plus an `✕` ghost cancel. It auto-disarms after 4s. Confirm
runs the async action (button shows "Servicing…"), and the result is surfaced as a toast — success
or, critically, failure. **Never** a blocking dialog; the guard stays inline and calm.

### Status Pills
- **Style:** Fully rounded (`rounded-full`), `#F1F5FB` or status-tinted background, 1px status
  border, mono/label type. The "Live"/"Reconnecting" pill (brand blue) and the header "Critical"
  count pill (red, carrying `pulse-critical`).

### Cards / Containers
- **Corner Style:** 12px (`rounded-xl`).
- **Background:** `#FFFFFF` cards; sensor tiles inside use `#F1F5FB`.
- **Shadow Strategy:** Soft neutral `shadow-sm` (see Elevation). Status cards add a faint status
  wash (`bg-<status>/5`) and a status border at 20–40% opacity.
- **Border:** 1px hairline `#DBE7F3`, or a status color at low opacity.
- **Internal Padding:** 16px (`p-4`).

### Toast
- **Style:** White card, 1px `#DBE7F3` border, `shadow-md`, bottom-right, stacked. Icon (green
  check / red ✕ / blue info) + message + dismiss. `role="status"` + `aria-live="polite"`; enters on
  a 220ms slide-up that reduced-motion neutralizes.

### Charts
- **Style:** Recharts line charts on white, dashed `#E2E8F0` gridlines, no vertical grid, 1.5px
  lines, no dots, animation disabled (the live stream is the motion). One sensor per chart; a 2-up
  grid on desktop that collapses to single-column on mobile.
- **Line colors:** amber `#D97706` temperature, red `#DC2626` vibration, brand blue `#1D4ED8`
  pressure, cyan `#0E7490` RPM. **Never purple/violet.**
- **Tooltip:** white card, 1px border, mono label, value colored to its line.

### RUL Gauge (Signature Component)
The defining element. A 220° SVG arc (160° → 20°, clockwise) with an `#E2E8F0` track and an active
arc whose length encodes RUL/cap and whose color steps green (healthy) → amber (`<32%`) → red
(`<12%`). The remaining-cycle count sits centered in Space Grotesk; a tracked "CYCLES" legend sits
below. **No glow.** **Never** replace it with a percentage bar or a fitness-style progress ring,
even if asked to "simplify."

## 6. Do's and Don'ts

### Do:
- **Do** keep the canvas blue-tinted white (`#EEF4FB`) and let white cards lift on a soft neutral
  `shadow-sm`.
- **Do** reserve brand blue (`#1D4ED8`) for interactive/brand chrome — selection, focus, the primary
  action, the "Live" pill — and never as a health color.
- **Do** speak health in green/amber/red; a resting fleet reads green (`#16A34A`).
- **Do** use the darker amber (`#B45309`) for amber **text** and the brighter `#D97706` only for
  amber **graphics**, so text clears WCAG AA on white.
- **Do** set every telemetry value in JetBrains Mono, and pair every status color with an icon or
  label (never color alone).
- **Do** keep the RUL degradation arc as the signature readout, color-stepped, no glow.
- **Do** guard the maintenance action with the inline confirm + result toast, and gate the critical
  pulse / spinners behind `prefers-reduced-motion`.

### Don't:
- **Don't** ship the **generic SaaS dashboard** — no templated card grids, no hero-metric stat tiles.
- **Don't** drift toward the **consumer fitness/IoT app** — no playful gradients, no emoji, no
  gamified rings. The RUL gauge is an instrument, not a fitness ring.
- **Don't** look like **enterprise SCADA / industrial HMI clutter** — no gray gradients, no beveled
  skeuomorphic gauges.
- **Don't** become a **crypto/trading terminal** — no ambient blinking; motion is for meaning only.
- **Don't** reintroduce the dark-theme tropes this restyle removed: **no neon glows** (`drop-shadow`
  / `box-shadow` in a status color), **no glassmorphism** (`backdrop-blur` cards).
- **Don't** use brand blue as a status color, or let a healthy unit render blue.
- **Don't** use purple/violet anywhere — chart and accent colors are blue / green / amber / red /
  cyan only.
- **Don't** use Deep Muted (`#94A3B8`) for body or label text — reserve it for disabled/dim glyphs
  and chart ticks.
- **Don't** add `background-clip: text` gradients or `border-left` accent stripes.
