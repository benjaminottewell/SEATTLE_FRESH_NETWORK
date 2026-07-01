# Can Seattle Support a Japan-Style Fresh-Convenience Network?

> **Status: 🚧 in development (Phase 0 — setup).** This README is a skeleton; sections
> fill in as each phase completes.

A logistics and operations **feasibility study**: what would it take — logistically and
economically — to run a Japanese-konbini-style fresh-convenience network in Seattle, and
where does it become viable? This is a **modeling project**: the deliverable is a
defensible verdict with transparent, sourced assumptions and sensitivity analysis.

The question is live — 7-Eleven has announced plans for ~1,300 konbini-style stores across
North America by 2030, with multi-daily fresh-delivery logistics flagged as the central
obstacle. This repo is an independent decision-support analysis of that problem for one
city.

---

## 1. Hook + lead map
*(coming in Phase 6 — the optimized network map or the feasibility-tipping chart)*

## 2. The question
Could a konbini-style fresh-convenience network work in Seattle's dense northern core?

## 3. The konbini system being modeled
Four structural features: **area dominance** (tight clustering), **combined distribution
centers** (commissaries batching fresh food by temperature), **multiple daily fresh
deliveries** (2–3×/day on short-shelf-life items), and **JIT POS-driven ordering**.

## 4. Related work
Builds on established location-routing methods (set-covering + multi-depot capacitated
VRP with time windows), adapting a U.S. food-desert grocery-hub framework to the konbini
fresh-convenience case. *(expand in Phase 6)*

## 5. Approach
Demand → store siting (MCLP) → delivery routing (VRPTW) → unit economics + sensitivity.
*(expand as phases complete)*

## 6. The verdict
*(coming in Phase 5)*

## 7. What flips it
*(sensitivity results — Phase 5)*

## 8. Honest limitations
Assumption-driven. The load-bearing assumptions and their sources live in
[`assumptions.yaml`](assumptions.yaml); every external dataset and published benchmark,
with links, is recorded in [`SOURCES.md`](SOURCES.md).

## 9. Reproducing this
*(env + run instructions — finalized once the environment is locked)*

```bash
# (draft) create environment, install deps, run notebooks 01–05 in order
python -m venv .venv
# Windows:  .venv\Scripts\activate
pip install -r requirements.txt
```

---

*Full build spec: [`SEATTLE_PLAN.md`](SEATTLE_PLAN.md). Standing context for
contributors/Claude Code: [`CLAUDE.md`](CLAUDE.md).*
