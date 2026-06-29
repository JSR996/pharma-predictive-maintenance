---
target: EquipmentCard maintenance button + failed badge
total_score: 29
p0_count: 0
p1_count: 1
timestamp: 2026-06-29T18-18-44Z
slug: frontend-src-components-equipmentcard-jsx
---
… scoped to the new "Perform Maintenance" button + "Failed — needs maintenance" badge in EquipmentCard.jsx, judged against PRODUCT.md ("calm by default, loud only when it matters"; "instrument, not ornament").

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Busy spinner is good; no explicit success confirmation — relies on the next WS tick (≤1.5s) |
| 2 | Match System / Real World | 4 | "Perform Maintenance" / "Failed — needs maintenance" — exact engineer voice |
| 3 | User Control and Freedom | 2 | Reset has no confirm and no undo; an accidental click discards the live run |
| 4 | Consistency and Standards | 4 | Reuses STATUS_CONFIG, tokens, lucide icons; button patterns consistent |
| 5 | Error Prevention | 2 | State-resetting button always visible, adjacent to the click-to-select card |
| 6 | Recognition Rather Than Recall | 4 | Labeled button + wrench icon; no memory load |
| 7 | Flexibility and Efficiency | 3 | One-click action; no shortcut/bulk, acceptable at this scope |
| 8 | Aesthetic and Minimalist Design | 2 | An always-on CTA on every healthy card adds noise, undercutting calm-by-default |
| 9 | Error Recovery | 2 | A failed replace POST is only console.error'd — user sees the spinner stop, nothing else |
| 10 | Help and Documentation | 3 | Self-explanatory labels; little needed |
| **Total** | | **29/40** | **Good — solid, two principle-level fixes** |

## Anti-Patterns Verdict

**LLM assessment:** Not AI slop. The failed-state treatment is genuinely good — solid teal button + critical badge only at the peak (failure) moment is correct emphasis logic, and the copy is terse and on-brand. The one real tell-adjacent problem is the opposite of slop: the button is *too present*. Five identical teal CTAs stacked down the equipment column read as "generic dashboard with an action on every row," which is exactly the anti-reference PRODUCT.md calls out.

**Deterministic scan:** `detect.mjs` on EquipmentCard.jsx → `[]` (clean). The design hook on the last write also reported no deterministic issues. No side-stripe borders, gradient text, or glass.

**Visual overlays:** Not available — the Playwright MCP requires real Chrome, which isn't installed, so no in-browser overlay was injected. Evidence here is source review + the CLI detector + the passing e2e run (button renders, click → POST 200).

## Overall Impression
The failed/critical path is excellent; the healthy path is where it slips. The signature move of this dashboard is calm uniformity broken only by severity — but the maintenance button is on by default, so every healthy card now ends in a call-to-action. The single biggest opportunity: make the action quiet (or absent) until a unit actually needs servicing, so the teal button becomes another signal of "act here" rather than ambient chrome.

## What's Working
- **Peak-moment treatment.** Solid `bg-teal` button + "Failed — needs maintenance" badge only when `failed` is a textbook calm→loud escalation. Strong.
- **Honest busy state.** `disabled` + "Servicing…" + spinning wrench gives immediate feedback and blocks double-submit.
- **System fidelity.** Reuses STATUS_CONFIG and design tokens; the div+role="button" conversion preserves keyboard selection. No new visual vocabulary invented.

## Priority Issues

- **[P1] Always-on CTA breaks "calm by default" (Heuristic 8).**
  - Why it matters: With 5 units, a healthy fleet shows 5 teal buttons competing for the eye when nothing needs action — the exact "action on every row" reflex the brand rejects. Severity should *earn* the button's presence.
  - Fix: Show the button only when `status !== 'normal'` (warning/critical/failed), or keep it but reveal on card hover/focus for healthy units (still keyboard-reachable). Reserve the solid teal for `failed`, outline for warning/critical.
  - Suggested command: `/impeccable layout`

- **[P2] Reset has no confirmation and no undo (Heuristics 3 & 5).**
  - Why it matters: One click silently discards that unit's current engine run and ~90s of chart history. The button sits inside the click-to-select card, so misclicks are plausible. For a healthy unit there's no reason to expect a destructive reset.
  - Fix: Require confirmation when the unit is *not* failed (a healthy unit rarely needs servicing), or add an inline "Undo"/"Confirm" affordance. If the button is gated to non-normal status (P1 fix), this risk mostly evaporates.
  - Suggested command: `/impeccable harden`

- **[P2] Silent failure on the replace request (Heuristic 9).**
  - Why it matters: `handleMaintenance` only `console.error`s. If the POST fails, the spinner stops and the user is left thinking it worked. Violates the "the numbers are real — show that" trust principle.
  - Fix: Surface a brief inline error state on the card (e.g. a one-shot "Retry" / "Failed to service" line), and a transient success confirmation so the action has a visible end.
  - Suggested command: `/impeccable harden`

- **[P3] Spinner has no reduced-motion alternative (Heuristic 1).**
  - Why it matters: PRODUCT.md explicitly requires a `prefers-reduced-motion` path for animations; `animate-spin` has none.
  - Fix: Swap the spin for a static icon / opacity pulse under `@media (prefers-reduced-motion: reduce)`.
  - Suggested command: `/impeccable animate`

## Persona Red Flags

**Sam (accessibility):** The div→role="button" + onKeyDown(Enter/Space) keeps selection keyboard-reachable, and the nested real `<button>` is fine — good. But `animate-spin` ignores reduced-motion. Failed state is conveyed by icon + text (not color alone) — passes.

**Riley (stress tester):** Double-submit is guarded by `busy`. But a failed network call vanishes silently, and rapidly clicking a healthy unit's button wipes its history with no guard — both reproducible.

**Alex (power user):** Fine at this scope; no "service all" bulk action, but that's not expected for 5 units.

## Minor Observations
- After a successful service, the card's RUL jumps on the next tick with no momentary "done" cue — a 1s success flash would close the loop (peak-end).
- The outline button on a healthy card and the solid button on a failed card are good, but warning/critical currently get the same outline as normal — consider a mid-tier emphasis.

## Questions to Consider
- Should a healthy unit even *offer* maintenance, or is servicing only meaningful once a unit is degrading/failed?
- What does the operator need to see the instant they click — a confirmation, or just trust the gauge to move?
- Is reset (discard the run) the right mental model, or should "maintenance" imply a logged event rather than a silent wipe?
