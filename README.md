# Can Seattle Support a Japan-Style Fresh-Convenience Network?

> **Status: 🚧 in development — Phase 1 (demand) complete on real Seattle data; Phase 2
> (drive-times) next.** This README fills in as each phase completes.

## Why I built this
Right after graduating I moved out of my apartment and, three days later, was on a plane to
Japan — seventeen days across Tokyo, Kyoto, Hiroshima, and Okinawa. The thing I couldn't stop
thinking about on the flight home wasn't a temple or a view. It was the **convenience stores
and vending machines**: how something that casual could deliver quality I'd have expected from
a sit-down restaurant. Seattle is a dense city like the ones I'd just walked through — so I
wanted to actually *know*: could that model work here? This project is me answering that the
honest way, by building a model instead of guessing.

## What it is
A logistics and operations **feasibility study** of a konbini-inspired **fresh-convenience
network** in Seattle's dense core — the full chain from demand → store siting → delivery
routing → unit economics, ending in a **defensible verdict** with transparent, sourced
assumptions and sensitivity analysis.

The catch is economics. Japan's model leans on cheap, dense labor; Seattle's minimum wage is
among the highest in the U.S., and the closest American attempts have struggled — **Amazon Go
is being wound down and Foxtrot went bankrupt in 2024**, both on cost, not demand. So the node
I model is a **low-labor, largely automated fresh-convenience micro-store**, and *how automated
it has to be* is the lever the whole study turns on.

The question is live in industry too: 7-Eleven has announced ~1,300 konbini-style North
American stores by 2030, with multi-daily fresh-delivery logistics flagged as the central
obstacle. This repo is an independent decision-support analysis of that problem for one city.

---

## 1. Hook + lead map
*(coming in Phase 6 — the optimized network map or the feasibility-tipping chart)*

## 2. The question
Could a dense network of konbini-inspired, **low-labor automated fresh-convenience
micro-stores** pencil out in Seattle's core — and how much automation and store density does
it take to flip it from infeasible to feasible?

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
