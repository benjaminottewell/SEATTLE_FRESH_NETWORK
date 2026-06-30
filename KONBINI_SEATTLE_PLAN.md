# Can Seattle Support a Japan-Style Fresh-Convenience Network? — Build Plan

A logistics and operations feasibility study: what would it take, logistically and
economically, to run a Japanese-konbini-style fresh-convenience network in the Seattle
area — and where does it become viable?

This is a **modeling project**, not a data-mining project. The deliverable is a
defensible feasibility model with transparent assumptions and sensitivity analysis, not a
fact discovered in scraped data. This document is the build spec, written to be
referenced while developing in Claude Code.

---

## 1. The Question

Japanese konbini (7-Eleven Japan, Lawson, FamilyMart) run on a fresh-food logistics
system that American convenience stores don't attempt: dense store clusters, commissaries
producing fresh meals nearby, and multiple temperature-controlled deliveries per day on
short-shelf-life items.

**This question is live.** 7-Eleven has announced plans to open roughly 1,300
konbini-style stores across North America by 2030. Industry reporting flags the logistics
of multiple daily fresh deliveries across U.S. distances, plus labor and regulatory costs,
as the central obstacles. This project is framed as an **independent decision-support
analysis** of that exact problem for one city — not a claim of novel discovery, but a
working model of whether and where the economics close.

**Core question:** Could that system work in Seattle? Specifically —
- How dense would a store network need to be to make multi-daily fresh delivery
  economical?
- Where would commissaries/distribution centers go to keep fresh-food delivery times low,
  given Seattle's water-fragmented geography?
- Does the unit economics close under U.S. (and specifically Seattle) labor and real
  estate costs?
- Under what assumptions does it flip from infeasible to feasible?

This has no guessable answer up front — which is the point.

---

## 2. Why Seattle Is a Genuinely Uncertain Test Case

These tensions are what make the model interesting rather than obvious:

- **High labor cost.** Seattle's minimum wage is among the highest in the U.S. The konbini
  model is labor-intensive (frequent restocking, fresh prep). This pressures the economics
  hard.
- **Water-fragmented geography.** Puget Sound, Lake Washington, and the ship canal break
  the road network into corridors funneled through bridges — a real routing and
  drive-time challenge for multi-daily fresh delivery.
- **Car-centric layout.** Japan's konbini rely on dense foot and transit traffic. Seattle's
  catchment behavior is different, which changes how tightly stores must cluster.
- **Lower baseline density tolerance.** Area-dominance clustering may or may not pencil out
  at U.S. densities.

---

## 3. The Konbini System Being Modeled (the real engineering)

Ground the model in the actual structural features, each of which becomes a modeling
component:

| Feature | What it means | Maps to |
|---|---|---|
| Area dominance | Tight store clustering in a zone, not thin spread | Facility location / density |
| Combined distribution centers | Commissaries batch fresh food by temperature band | Facility siting + capacity |
| Multiple daily fresh deliveries | Short-shelf-life items replenished 2-3x/day | Routing + delivery cadence |
| JIT small-batch, POS-driven | Item-level, weather-adjusted ordering | Demand forecasting |

> Treat specific operational numbers (delivery frequency, store size, SKU counts,
> commissary throughput) as **assumptions sourced from published benchmarks and cited**,
> not as known facts. Their credibility is the project's credibility.

---

## 3a. Prior Work & Positioning

The methods here are mature, and that is deliberately fine — the value is correct
application of recognized techniques to a specific, timely problem, not methodological
novelty. Position the project honestly against what exists:

- **Established methods.** Fresh-food cold-chain vehicle routing, facility location, and
  combined location-routing models are a well-developed academic field (e.g., bi-level
  facility-location-plus-routing for fresh distribution; cold-chain VRP with time windows
  accounting for perishability and traffic). Use these as validated building blocks.
- **Closest neighbor — adapt, don't reinvent.** A U.S. study modeled grocery delivery hubs
  for food deserts using neighborhood convenience stores, combining minimum-cost set
  covering with a multi-depot capacitated VRP with time windows (MDCVRP-TW), tested across
  three U.S. counties with the number of store locations as a sensitivity parameter. This
  is the methodological template. Cite it, borrow the set-covering + MDCVRP-TW structure,
  and differentiate by **application**: konbini-style multi-daily fresh cadence,
  area-dominance density, and Seattle's specific labor/geography economics — rather than
  food-desert access.
- **How to frame it.** "I built on an established location-routing framework and adapted it
  to the konbini fresh-convenience case for Seattle." In an interview, building correctly
  on prior work is a strength, not a weakness. Reserve any novelty claims for the
  application and the Seattle-specific findings.

This section should become a short "Related Work" paragraph in the README — doing the lit
review and positioning the work is itself a credibility signal.

---

## 4. Scope Decision (read before building)

The full city-wide, multi-scenario version is large. For v1.0, build the **complete
demand -> siting -> routing -> economics chain for one bounded geography** and produce a
feasibility verdict with sensitivity analysis.

**v1.0 (build this):**
- **Study area — the dense northern core.** A contiguous cluster of high-density,
  high-daytime-population neighborhoods where a fresh-convenience network is actually
  viable: Downtown / CBD, Belltown, South Lake Union, Capitol Hill, First Hill, Pioneer
  Square, and the Chinatown-International District. This is small enough to keep MILP/VRP
  solve times sane, but the neighborhoods differ enough in density, daytime population, and
  distance-from-hub that siting and routing are *real* decisions with genuine tradeoffs —
  not a trivial single-density blob.
- **Production hub — SoDo.** Place the central production/commissary facility in the SoDo
  industrial district just south of the core. Chosen on its merits — industrial zoning,
  port proximity, and freeway access for multi-daily delivery — which also gives a clean
  spatial structure: hub to the south, demand nodes clustered to the north, real road
  distances between them.
- Demand layer -> node siting -> delivery routing -> unit economics -> feasibility verdict
- A sensitivity analysis identifying which assumptions flip the verdict

**Future work (document, don't build):**
- **Cross-water expansion** — extend north across the ship canal (Fremont, Ballard,
  Wallingford) and to the Eastside, where bridges and water crossings make routing and
  drive-time genuinely constraining. This is where Seattle's fragmented geography becomes
  the interesting variable; deferring it keeps v1.0 land-contiguous and tractable.
- Full metro coverage
- Multi-scenario comparison (e.g., commissary count, store format variants)
- Stochastic demand and discrete-event simulation of the full supply chain
- Consumer-demand sensing (the prior project) as a richer demand input layer

A complete, honest feasibility model for one area beats a sprawling half-built one.

---

## 5. Guiding Principles

- It's a modeling project: **assumption transparency is the rigor.** Every operational and
  cost parameter gets a sourced citation or an explicit "assumed" flag.
- Always run **sensitivity analysis.** The valuable output is "feasible if X < threshold,
  infeasible above it," not a single yes/no.
- Frame around transferable **structural/operational features**, not cultural superiority.
- Report honestly. "Infeasible under current Seattle labor costs unless density exceeds Y"
  is a strong, publishable result.

---

## 6. Repository Structure

```
konbini-seattle/
├── README.md                  # The deliverable - question, model, verdict, key maps
├── CLAUDE.md                  # Standing context for Claude Code (see sec 10)
├── requirements.txt
├── .gitignore
├── assumptions.yaml           # ALL operational/cost parameters, each with a source note
├── data/
│   ├── raw/                   # Census pulls, OSM extracts (cache everything)
│   ├── interim/
│   └── processed/
├── notebooks/
│   ├── 01_demand_layer.ipynb
│   ├── 02_network_drivetimes.ipynb
│   ├── 03_facility_location.ipynb
│   ├── 04_routing_cadence.ipynb
│   └── 05_economics_sensitivity.ipynb
├── src/
│   ├── demand/                # Demand estimation by area
│   ├── geo/                   # OSM road graph, drive-time / isochrone tools
│   ├── optimize/              # Facility location (MILP) + routing (VRP)
│   ├── econ/                  # Unit economics + sensitivity
│   └── viz/                   # Maps and charts
├── outputs/
│   ├── figures/
│   └── tables/
└── reports/
    └── findings.md
```

Keeping every tunable parameter in a single `assumptions.yaml` is what makes the
sensitivity analysis and the transparency claim real — reviewers can see exactly what you
assumed and change it.

---

## 7. Phased Build

Each phase ends with a committable artifact.

### Phase 0 — Setup
- Repo, env, `requirements.txt`, `.gitignore`.
- Create `assumptions.yaml` skeleton with placeholder parameters and source fields.
- Write `CLAUDE.md` (sec 10). Stub README with sec 9 outline.

### Phase 1 — Demand Layer
- Estimate per-node daily demand using a **top-down market-share structure, grounded by
  analog benchmarks**: `catchment population x capture rate x visit frequency x avg
  ticket`. Set the **capture rate** from published cafe/convenience transactions-per-day
  benchmarks (adjusted down for a smaller/automated node) so it has a source, not just a
  guess. (A distance-weighted gravity model is the more sophisticated alternative — deferred
  to future work.)
- Inputs: U.S. Census API (population, density, age mix, income), transit/walkability
  (Walk Score API or transit stop density), workplace/daytime population (matters here — the
  core is daytime-population-driven; decide deliberately between daily-average and
  time-of-day demand, daily-average is the simpler defensible default).
- **Demand is the most uncertain input, so capture rate is the star sensitivity parameter**
  — model it as a range, never a single hard number.
- Output: a demand surface — estimated daily demand per node, with an explicit range.
- Deliverable: a demand heatmap over the study area.

### Phase 2 — Network & Drive-Time Foundation
- Pull the road network for the core study area with `OSMnx`; build a routable graph in
  `NetworkX`.
- Compute drive-times from the SoDo production hub to demand nodes across the northern
  core; generate isochrones (what's reachable within the fresh-delivery time window).
- Within the contiguous core, the routing realism comes from one-ways, traffic, and real
  vs. straight-line distance (the dramatic water-crossing constraints are deferred to the
  cross-water expansion in future work).
- Deliverable: drive-time / isochrone maps from the SoDo hub.

### Phase 3 — Facility Location Optimization

> **Handling the hub chicken-and-egg (the Location-Routing Problem).** Hub location and
> delivery routing depend on each other: you can't cost the routes without a hub, and you
> can't pick the best hub without the route costs. The joint problem is the
> **Location-Routing Problem (LRP)** — exactly what the food-desert study (sec 3a) solved with
> set-covering + MDCVRP-TW. Solving it *integrated* is intractable at solo-v1.0 scope, so
> use one of these instead, and state the choice in the README:
>
> - **Decomposition (default for the generic konbini version).** Fix a hub first via a
>   **center-of-gravity** calculation (demand-weighted centroid of all nodes) or a small
>   facility-location model over a few candidate industrial sites; then solve routing given
>   that hub; optionally test a second hub and compare. Not globally optimal, but standard
>   practice — "I decomposed the LRP because the integrated form is intractable; here's the
>   tradeoff" is a strength in an interview, not a weakness.
> - **Fixed hub (when a production site already exists).** Many real-world operators
>   already run a central production/commissary facility at a known location. Framing the
>   model around a fixed, realistic production site collapses the LRP into the easy case:
>   optimize node placement and routing *from* a given hub and skip the location half
>   entirely. Simpler to build, and the most realistic framing whenever the operator's hub
>   is already a settled fact rather than an open decision.
> - **Scenario input.** Don't optimize the hub at all — test a few candidate locations and
>   report how feasibility shifts. Sidesteps the loop by making the hub a what-if.

- Candidate sets: potential node locations (high-demand commercial slots/intersections)
  and, for the decomposition path, candidate commissary sites.
- **Primary siting model: Maximal Covering Location Problem (MCLP) with a fixed number of
  nodes `p`.** Place `p` nodes to maximize daytime demand captured within an acceptable
  walk/drive radius, and sweep `p` (e.g., 5 -> 20) so network scale becomes a tunable knob
  feeding routing and economics. Apply the **area-dominance** density logic as a constraint.
- **Note the alternative considered:** set-covering ("cover all demand within radius, minimize
  node count") answers a *service-level* question; MCLP answers a *budget-constrained* one.
  Chosen MCLP because capital, not coverage, is the binding constraint in a commercial
  rollout — and because fixed-`p` makes scale sensitivities clean. (Be precise on names:
  this is maximal *covering*, not p-median — p-median minimizes total distance rather than
  maximizing captured demand.)
- Formulate as a MILP; solve with `PuLP` or OR-Tools (CP-SAT).
- Deliverable: optimized node + hub network map for the study area, with the model choice
  and hub-selection method explicitly noted.

### Phase 4 — Delivery Routing & Cadence
- Given the network from Phase 3, model multi-daily fresh delivery from commissaries to
  stores.
- Solve as a Vehicle Routing Problem with time windows (VRPTW) using OR-Tools routing.
- Capture the cadence cost: 2-3 fresh deliveries/day across temperature bands drives
  vehicle count and labor hours.
- Deliverable: route maps + total daily delivery cost/distance/vehicle requirements.

### Phase 5 — Unit Economics & Sensitivity
- **Pre-register the feasibility bar in `assumptions.yaml` BEFORE running anything.** Primary
  bar: **contribution margin per node > 0** — does a node's revenue cover its variable costs
  (product, its share of delivery cost, direct labor)? This maps directly onto what the
  siting/routing models compute (revenue vs. location-driven supply cost) and avoids
  inventing corporate-cost assumptions. Report **payback period** as a secondary lens (more
  operator-realistic, but depends on capex guesses, so not the primary gate). Choosing the
  bar after seeing results is the fastest way to destroy the study's credibility — commit
  first.
- Build the cost model from `assumptions.yaml`: node opex (rent, labor at Seattle wages),
  hub opex, delivery cost (from Phase 4), fresh spoilage/waste, revenue per node.
- Compute viability against the pre-registered bar (contribution margin; break-even
  demand/density; secondary payback).
- **Sensitivity analysis:** sweep the parameters most likely to flip the verdict — capture
  rate (the star, per Phase 1), labor cost, delivery frequency, node density, spoilage rate,
  avg ticket — and chart where feasibility tips.
- Deliverable: a feasibility verdict + sensitivity charts. Target headline: "a core node
  clears positive contribution margin above ~X daily transactions; below that, location-
  driven supply cost dominates — so the verdict is conditional on capture rates in the Y-Z
  range."

### Phase 6 — Polish & Ship
- Full README (sec 9) with the headline maps and the verdict.
- `reports/findings.md`: narrative + honest limitations + the assumption table.
- Reproducibility check: fresh clone + install + run reproduces the verdict.
- Clean notebooks (restart-and-run-all), docstrings, tidy `src/`.

---

## 8. Tech Stack

| Area | Tools |
|------|-------|
| Geospatial / networks | `OSMnx`, `NetworkX`, `GeoPandas`, `Shapely` |
| Drive-times / isochrones | `OSMnx` + `NetworkX` shortest paths (or an isochrone lib) |
| Facility location (MILP) | `PuLP` or Google `OR-Tools` (CP-SAT) |
| Vehicle routing (VRPTW) | Google `OR-Tools` routing solver |
| Demand / forecasting | `scikit-learn`, `statsmodels`, Census API (`cenpy` or `requests`) |
| Economics / sensitivity | `pandas`, `numpy`; parameters in `assumptions.yaml` (`PyYAML`) |
| Simulation (future) | `SimPy` (discrete-event), Monte Carlo |
| Viz / maps | `matplotlib`, `plotly`, `folium`/`kepler.gl`, `contextily` |

Pin versions. Cache every Census/OSM pull to disk so reruns don't depend on live APIs.

---

## 9. README Outline (the real deliverable)

1. **Hook + lead map** — open on the real 7-Eleven North America expansion (the question
   is live), then the optimized network map or the feasibility-tipping sensitivity chart.
2. **The question** — could a konbini-style fresh-convenience network work in Seattle?
3. **The konbini system** — the four structural features being modeled.
4. **Related work** — the established location-routing methods and the food-desert
   convenience-store study this builds on; how this differs (konbini cadence, Seattle
   economics).
5. **Approach** — demand -> siting -> routing -> economics, a few sentences each.
6. **The verdict** — feasible / infeasible / conditional, with the key threshold.
7. **What flips it** — sensitivity results: the parameters that decide viability.
8. **Honest limitations** — assumption-driven; list the load-bearing assumptions and their
   sources.
9. **Reproducing this** — env + run instructions; point to `assumptions.yaml`.

Reviewers will read the README and look at two or three maps. Optimize for that.

---

## 10. CLAUDE.md Contents (for Claude Code)

- One-paragraph summary + the v1.0 scope (bounded geography, full demand-economics chain).
- This is a **modeling project**: assumption transparency and sensitivity analysis are the
  rigor; every parameter lives in `assumptions.yaml` with a source note.
- Frame around operational/structural features, not cultural superiority.
- Repo conventions; cache all external pulls; never commit large raw data.
- Current phase / done / next.

---

## 11. Definition of Done (v1.0)

- [ ] Fresh clone runs and reproduces the feasibility verdict.
- [ ] Demand, network, facility location, routing, and economics each commit at least one
      figure/map.
- [ ] `assumptions.yaml` holds every tunable parameter, each with a source or "assumed"
      flag.
- [ ] Sensitivity analysis shows which assumptions flip the verdict.
- [ ] README delivers the question, the model, the verdict, and honest limitations.
- [ ] Future work (full metro, simulation, demand sensing) documented, not left as stubs.

The win is a complete, transparent, reproducible feasibility model with a defensible
verdict — not maximal coverage. Ship v1.0 before expanding.

---

## 12. Why This Project Earns Its Place

- **Resume coherence:** pairs with your manufacturing/operations capstone to tell one
  story — operations and manufacturing analytics.
- **Interview-ready skills:** facility location optimization, vehicle routing, geospatial
  network analysis, demand forecasting, cost modeling, sensitivity analysis — the exact
  toolkit supply-chain and operations roles probe.
- **Non-obvious outcome:** the feasibility verdict genuinely isn't knowable in advance,
  and the sensitivity thresholds are the kind of specific, defensible result that makes a
  portfolio piece worth discussing.
- **Timely & grounded:** ties directly to a real, in-progress industry move (7-Eleven's
  North America konbini expansion), so it reads as a relevant decision-support analysis,
  not a hypothetical.
- **Credibility through positioning:** the value is correct application of recognized
  location-routing methods to a specific problem — not novelty. Building visibly on prior
  work and stating assumptions transparently is exactly what signals maturity to
  operations and supply-chain interviewers.
