# CLAUDE.md — Standing context for Claude Code

## What this project is
A logistics/operations **feasibility model**: could a Japanese-konbini-**inspired** fresh-
convenience network work in Seattle? We model the full chain — demand → store siting →
delivery routing → unit economics — for one bounded geography and produce a feasibility
verdict with sensitivity analysis.

**The node being tested:** a konbini-inspired **fresh-convenience micro-store** — small,
multi-SKU, short-shelf-life fresh goods, replenished by multi-daily delivery. It is
**low-labor by design**; the *degree of automation* is the model's central lever, expressed
in Phase-5 economics as **store labor hours (down) vs. automation capex (up)** — feasible
only if labor saved > capex/tech added. NOT a single-product vending kiosk (too narrow for
the fresh-delivery logistics), and NOT assumed to be a fully-staffed store (that model just
failed — see Foxtrot). Amazon Go is a **cautionary reference**: it automated *checkout* only,
kept restocking/prep labor, and used expensive cashierless tech — its shutdown is one failed
design point, not proof the concept can't work. Konbini = the inspiration + logistics
blueprint; automation = Seattle's answer to its labor wall; the model finds the tipping
conditions. An honest "infeasible unless X" is a valid result.

**v1.0 scope:** the dense northern core (Downtown, Belltown, South Lake Union, Capitol
Hill, First Hill, Pioneer Square, Chinatown-International District), with a fixed
production hub in **SoDo**. Land-contiguous, so routing is tractable. Cross-water
expansion (Ballard, Eastside) is documented future work, not built.

## The prime directive: this is a MODELING project
- **Assumption transparency is the rigor.** Every operational/cost parameter lives in
  `assumptions.yaml`, each with a `source: cited|derived|assumed` flag and a note
  (`derived` = computed from cited inputs plus stated assumptions). Never hardcode a
  tunable number in `src/` — read it from `assumptions.yaml`.
- **Always do sensitivity analysis.** The valuable output is "feasible if X < threshold,"
  not a bare yes/no. Parameters flagged `star: true` are the ones we sweep.
- **Frame around operational/structural features**, never cultural superiority.
- **Report honestly.** "Infeasible under current Seattle wages unless density exceeds Y" is
  a strong result, not a failure.

## Working with the user
The user is **new to a lot of this** and wants to learn by doing. Explain what you're doing
and why, in plain language. Prefer small, reviewable steps over large autonomous dumps.
Lean toward cutting scope when something gets heavy — a finished small thing beats a
half-built big one.

## Repo conventions
- Cache every external pull (Census, OSM) to `data/raw/`. Never commit large raw data
  (see `.gitignore`).
- `run_all.py` + documented `src/` scripts are the narrative (no notebooks).
- Pin versions only after a clean install (lock what actually worked).

## Methodological positioning (Related Work)
Built on established location-routing methods: set-covering + multi-depot capacitated VRP
with time windows (MDCVRP-TW), per a U.S. food-desert grocery-hub study. We differ by
**application**: konbini multi-daily fresh cadence, area-dominance density, Seattle
labor/geography economics. Siting uses **MCLP** (maximal covering, fixed p) — not p-median.

## Status
- **Phases 0–5: core chain COMPLETE** — demand (real ACS/LODES data) → siting (MCLP,
  p-sweep) → routing (VRPTW, window-bound fleet) → economics (per-store P&L vs the
  pre-registered bar + capture/automation sensitivity sweeps).
- Headline: pre-registered contribution bar clears everywhere in the swept range;
  fully-loaded viability is conditional — median store positive above ~1.7% capture
  (baseline 2.5% ⇒ 9/10 stores viable); automation (6h vs 32h staffing) is worth
  ~$550/store-day ≈ ~0.9pp of capture-rate slack.
- **Phase 6 (polish & ship) remains:** README verdict + figures, findings.md,
  reproducibility check, docstrings cleanup. Some assumptions still
  `assumed` (rent, capex, visit_frequency, resident_weight) — candidates for
  grounding or explicit limitations. See `SEATTLE_PLAN.md`.
