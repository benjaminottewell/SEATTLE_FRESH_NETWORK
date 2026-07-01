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
  `assumptions.yaml`, each with a `source: cited|assumed` flag and a note. Never hardcode a
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
- Notebooks (`notebooks/01..05`) are the narrative; reusable logic goes in `src/`.
- Pin versions only after a clean install (lock what actually worked).

## Methodological positioning (Related Work)
Built on established location-routing methods: set-covering + multi-depot capacitated VRP
with time windows (MDCVRP-TW), per a U.S. food-desert grocery-hub study. We differ by
**application**: konbini multi-daily fresh cadence, area-dominance density, Seattle
labor/geography economics. Siting uses **MCLP** (maximal covering, fixed p) — not p-median.

## Status
- **Phase 0 — Setup:** IN PROGRESS. Folder structure, skeleton files, assumptions.yaml
  created. Next: build the Python environment and verify the geo/optimization libraries
  install on this machine.
- Phases 1–6: not started. See `SEATTLE_PLAN.md` for the full phased build.
