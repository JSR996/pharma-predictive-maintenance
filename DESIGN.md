---
name: PharmaGuard
description: Instrument-grade predictive-maintenance dashboard for pharma manufacturing equipment.
colors:
  bg: "#0A0E1A"
  surface: "#111827"
  surface2: "#1F2937"
  border: "#374151"
  teal: "#00D4AA"
  critical: "#EF4444"
  warning: "#F59E0B"
  text: "#F9FAFB"
  subtext: "#9CA3AF"
  muted: "#6B7280"
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
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "16px"
  sensor-tile:
    backgroundColor: "{colors.surface2}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "6px 8px"
  status-pill:
    backgroundColor: "{colors.surface2}"
    textColor: "{colors.subtext}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
---

# Design System: PharmaGuard

## 1. Overview

**Creative North Star: "The Calibrated Instrument"**

PharmaGuard is the screen on a precision lab instrument, not a SaaS dashboard. It reads as
deep, controlled, and low-noise — the visual equivalent of a pharma cleanroom under steady
operation. The surface is a near-black navy (`#0A0E1A`) that recedes, letting illuminated data
be the only thing that draws the eye. Teal (`#00D4AA`) is the single resting accent; it signals
"healthy / live" and nothing else. The system is quiet by default and only raises its voice —
through amber, red, and a slow critical pulse — when a unit actually degrades. If everything were
glowing, nothing would read as urgent; the restraint is the point.

Density is purposeful: a three-column operations layout (equipment list · live charts · alert
feed) that a maintenance engineer can sweep in one glance and trust on a closer look. The
signature element is the **RUL degradation arc** — a 220° SVG gauge that sweeps teal → amber → red
as remaining useful life falls. It is an instrument readout, never a fitness ring or a percentage
bar.

This system explicitly rejects the generic SaaS admin panel (templated card grids, rounded blue
buttons, hero-metric tiles), the consumer fitness/IoT look (playful gradients, emoji, gamified
rings), enterprise SCADA clutter (gray gradients, beveled skeuomorphic gauges), and the crypto/
trading terminal (neon-on-black hyperactivity, blinking everything).

**Key Characteristics:**
- Near-black navy canvas; data is the only light source.
- One resting accent (teal); color escalates only with real severity.
- Monospace for all numbers — telemetry reads as instrument output.
- The RUL degradation arc is the signature, non-negotiable component.
- Motion is reserved for meaning (the critical pulse), never ambient.

## 2. Colors

A near-monochrome navy field with a single teal accent and a strict two-step severity escalation.

### Primary
- **Live Teal** (`#00D4AA`): The single resting accent. Healthy/normal status, the "Live"
  connection pill, active RUL arcs, selection rings, brand mark. Used sparingly — it means "all is
  well and the stream is alive."

### Secondary
- **Warning Amber** (`#F59E0B`): Degradation has begun (RUL < 50 cycles). Warning status, mid-range
  anomaly scores, the warning arc segment. Never decorative.
- **Critical Red** (`#EF4444`): Imminent failure (RUL < 20 cycles). Critical status, the header
  pulse, anomaly badges, the critical arc segment.

### Neutral
- **Cleanroom Navy** (`#0A0E1A`): The page background. Deep, controlled, recessive.
- **Panel Surface** (`#111827`): Cards, the alert feed, chart containers — one step up from the
  canvas.
- **Inset Surface** (`#1F2937`): Sensor tiles, pills, the gauge track — nested insets within a
  surface.
- **Hairline Border** (`#374151`): 1px borders and dividers only.
- **Primary Text** (`#F9FAFB`): Headings, equipment names, primary values.
- **Subtext** (`#9CA3AF`): Secondary labels, alert messages, axis ticks — the lightest "muted" tone
  that still clears AA on the dark surfaces.
- **Deep Muted** (`#6B7280`): Reserved for **large/non-essential** glyphs only (decorative icons at
  ≥18px). Forbidden for small body or label text — it fails AA on the navy field.

### Named Rules
**The One Accent Rule.** Teal is the only resting color. If a screen under normal operation shows
amber or red, that's a signal, not styling. Status must escalate teal → amber → red and never skip
or decorate.

**The Lit-Data Rule.** Color belongs to data, not chrome. Borders, backgrounds, and structure stay
neutral navy; saturation is spent only on values, statuses, and the RUL arc.

## 3. Typography

**Display Font:** Space Grotesk (with sans-serif fallback) — weights 400–700
**Body Font:** Inter (with sans-serif fallback) — weights 300–600
**Label/Mono Font:** JetBrains Mono (with monospace fallback) — weights 400–500

**Character:** A geometric-grotesk display (Space Grotesk) paired with a neutral humanist body
(Inter) and a true monospace for telemetry. The contrast is structural — grotesk headings,
humanist prose, mono numbers — so the three roles never blur.

### Hierarchy
- **Display** (Space Grotesk, 700, ~1.125rem, lh 1.1): Selected-equipment name, KPI counts,
  PharmaGuard wordmark.
- **Headline** (Space Grotesk, 600, ~1rem, lh 1.2): Card equipment names, panel titles
  ("Alert Feed").
- **Body** (Inter, 400, 0.875rem, lh 1.5): Alert messages, descriptive copy, empty states.
- **Label** (Inter, 500, 0.625rem, tracking 0.1em, UPPERCASE): Sensor labels, section eyebrows,
  status text. Tracked and uppercase to read as instrument legends.
- **Mono** (JetBrains Mono, 400–500, 0.75rem): Every number that is telemetry — equipment IDs,
  sensor values, anomaly %, timestamps, cycle counts.

### Named Rules
**The Numbers-Are-Mono Rule.** Any value the model produces or the stream reports is set in
JetBrains Mono. Prose is Inter, headings are Space Grotesk, data is mono — no exceptions. It makes
telemetry read as instrument output and keeps digits from reflowing as they tick.

## 4. Elevation

Flat by default. Depth comes from **tonal layering**, not shadows: navy canvas → `#111827` panel →
`#1F2937` inset, each step one tone lighter. The only "shadows" in the system are colored
**glows** — `drop-shadow` / `box-shadow` in the status color — used to make active data feel lit,
never to fake physical lift. Tooltips get a single soft `shadow-xl` because they float above the
plane.

### Shadow Vocabulary
- **Status glow** (`drop-shadow(0 0 4px <statusColor>88)` on the RUL arc; `0 0 8px` on the health
  bar): A halo in the active color so live values read as illuminated. The blur is small and the
  color is the data's own.
- **Tooltip lift** (`shadow-xl`): The one true shadow — chart tooltips float above the plane.

### Named Rules
**The Tonal-Layering Rule.** Surfaces are distinguished by tone, not by shadow. Going one level
deeper means going one step lighter (`#0A0E1A` → `#111827` → `#1F2937`), never adding a drop
shadow. Glows are for data, shadows are for true overlays only.

## 5. Components

### Buttons
- **Shape:** Rounded (12px / `rounded-xl` on cards-as-buttons; pills are fully rounded).
- **Primary affordance:** Equipment cards are the primary interactive surface — full `<button>`
  elements with a status-tinted border and a faint status background wash.
- **Hover / Focus:** `hover:border-teal/40`; focus shows a `ring-2 ring-teal/40`. Selected state
  is a stronger `ring-teal/60` + `border-teal/50`. Transitions are 200ms.
- **No standalone primary button** in the current UI — there are no rounded blue CTAs, by design.

### Status Pills
- **Style:** Fully rounded (`rounded-full`), `#1F2937` or status-tinted background, 1px status
  border, mono or label type. The "Live"/"Reconnecting" connection pill and the header "Critical"
  count pill.
- **State:** The critical count pill carries the `pulse-critical` animation (slow opacity breathe).

### Cards / Containers
- **Corner Style:** 12px (`rounded-xl`).
- **Background:** `#111827` panels; sensor tiles inside use `#1F2937`.
- **Shadow Strategy:** None — tonal layering only (see Elevation). Status cards add a faint colored
  background wash (`bg-<status>/5`) and a colored border at low opacity.
- **Border:** 1px hairline `#374151`, or a status color at 20–40% opacity.
- **Internal Padding:** 16px (`p-4`).

### Charts
- **Style:** Recharts line charts on `#111827`, dashed `#1F2937` gridlines, no vertical grid,
  1.5px lines, no dots, animation disabled (the live stream is the motion). One sensor per chart in
  a 2-up grid.
- **Line colors:** Drawn from the palette — amber for temperature, red for vibration, teal/cyan for
  pressure and RPM. **Never purple/violet.**
- **Tooltip:** `#111827` card, 1px border, mono label, value colored to its line.

### RUL Gauge (Signature Component)
The defining element. A 220° SVG arc (160° → 20°, clockwise) with a `#1F2937` track and an active
arc whose length encodes RUL/cap and whose color steps teal (healthy) → amber (`<32%`) → red
(`<12%`). The remaining-cycle count sits in the center in Space Grotesk; a tracked "CYCLES" legend
sits below. The active arc carries a status-colored glow. **Never** replace it with a percentage
bar or a fitness-style progress ring — even if asked to "simplify."

## 6. Do's and Don'ts

### Do:
- **Do** keep the canvas `#0A0E1A` and let illuminated data be the only light source.
- **Do** set every telemetry value in JetBrains Mono (IDs, sensor readings, %, timestamps, cycles).
- **Do** reserve teal for resting/healthy state and escalate teal → amber → red only on real
  severity.
- **Do** convey depth by tonal layering (`#0A0E1A` → `#111827` → `#1F2937`), and use colored glows,
  not drop shadows, to make active data feel lit.
- **Do** keep the RUL degradation arc as the signature readout, color-stepped and glowing.
- **Do** hold body and label text to `#9CA3AF` or lighter so it clears AA on the dark surfaces, and
  pair every status color with an icon or label (never color alone).
- **Do** gate the critical pulse and spinners behind `prefers-reduced-motion`.

### Don't:
- **Don't** ship the **generic SaaS dashboard** — no templated card grids, no rounded blue primary
  buttons, no hero-metric stat tiles repeated in a row.
- **Don't** drift toward the **consumer fitness/IoT app** — no playful gradients, no emoji, no
  gamified rings. The RUL gauge is an instrument, not a fitness ring.
- **Don't** look like **enterprise SCADA / industrial HMI clutter** — no gray gradients, no beveled
  skeuomorphic gauges, no 1990s bevels.
- **Don't** become a **crypto/trading terminal** — no neon-on-black hyperactivity, no blinking
  everything, no ambient motion. Motion is for meaning (the critical pulse) only.
- **Don't** use `#6B7280` (deep muted) for small body or label text on the navy field — it fails
  WCAG AA. Use `#9CA3AF` or lighter.
- **Don't** use purple/violet (`#A78BFA`) anywhere — it is off-palette. Chart and accent colors
  come from teal / amber / red / cyan only.
- **Don't** add `background-clip: text` gradients, glassmorphism as decoration, or `border-left`
  accent stripes.
