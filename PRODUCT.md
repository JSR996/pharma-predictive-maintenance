# Product

## Register

product

## Users

The on-screen fiction is a **plant maintenance / reliability engineer** in pharma manufacturing,
watching the health of five pieces of process equipment (tablet compression, capsule filling, fluid
bed dryer, blister packaging, HVAC air handler) and acting on predicted remaining-useful-life (RUL)
and anomaly alerts before a unit fails.

The real audience is a **portfolio reviewer** — a hiring manager, engineer, or recruiter evaluating
full-stack + ML craft. So the dashboard must read as a credible, in-use operations tool *and* be
visibly more considered than a tutorial project. Two viewing contexts: a quick glance that should
land "this person ships polished, real-time systems," and a closer look that holds up to scrutiny
(honest model metrics, real CMAPSS data driving live predictions, no faked numbers).

## Product Purpose

PharmaGuard turns a trained ML model (RUL regression + anomaly detection on the NASA CMAPSS dataset)
into a live monitoring surface: streamed sensor telemetry over WebSocket, real-time charts, a
signature RUL degradation-arc gauge per unit, and a severity-sorted alert feed. Success is a viewer
trusting that the predictions are real and the interface is production-grade — calm under normal
conditions, unmistakably legible the moment a unit degrades.

## Brand Personality

**Calm authority. Clinical precision. Instrument-grade.**

Quiet and trustworthy, like a well-designed piece of lab equipment — nothing flashes for attention
under normal operation, and everything is exact and legible. The pharma cleanroom is the mood: deep,
controlled, low-noise. When a unit degrades, urgency earns its way to the foreground through
hierarchy and restrained motion, not decoration. Voice in copy is terse and technical (engineer
talking to engineer), never marketing-cheerful.

## Anti-references

- **Generic SaaS dashboard** — no templated Bootstrap/Material card-grid admin panel, no rounded
  blue primary buttons, no identical stat-tile rows. The hero-metric template is banned.
- **Consumer fitness / IoT app** — no playful gradients, emoji, friendly rounded everything, or
  gamified progress rings. The RUL gauge is an instrument, not a fitness ring.
- **Enterprise SCADA / industrial HMI clutter** — no gray gradients, beveled skeuomorphic gauges,
  1990s bevels, or dense unreadable mimic diagrams.
- **Crypto / trading terminal** — no neon-on-black hyperactivity, no blinking everything, no ticker
  overload. Motion is reserved for meaning (a critical pulse), not ambient noise.

## Design Principles

1. **Calm by default, loud only when it matters.** Normal operation is quiet and uniform; severity
   is what breaks the rhythm. If everything demands attention, nothing does.
2. **The numbers are real — show that.** Honest model metrics (RMSE ~17.5, R² ~0.82), real data
   replay, and live predictions are a feature. Never dress up or fake a value; credibility is the
   product.
3. **Instrument, not ornament.** The RUL degradation arc is the signature element and reads as a
   precision gauge. Every visual choice should feel measured, not decorative.
4. **Glanceable hierarchy.** Status of all five units must be readable in one sweep; detail rewards a
   closer look without being required for the headline.
5. **Production-grade or not shipped.** Responsive, fast, bug-free, on-brand. The polish *is* the
   portfolio argument.

## Accessibility & Inclusion

Best-effort, with a practical floor: aim for WCAG AA contrast on body and status text against the
white/blue-tinted surfaces, keyboard-reachable interactive elements, and a `prefers-reduced-motion`
alternative for the critical pulse and any stream animations. No formal audit target, but legibility
is non-negotiable given the "instrument-grade" promise — the muted-gray-on-tinted-white trap is the
one to watch (light gray "for elegance" on a near-white page is the biggest readability killer).
