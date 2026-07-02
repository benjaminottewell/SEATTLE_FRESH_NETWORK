# Findings — Konbini-Inspired Fresh-Convenience Network, Seattle v1.0

*Full narrative of the feasibility model: method, results, verdict, and limitations.
The condensed version lives in the [README](../README.md); every number below is
reproducible via `python run_all.py`.*

---

## 1. The question

Could a dense network of konbini-inspired, **low-labor automated fresh-convenience
micro-stores** pencil out in Seattle's dense northern core — and how much automation and
what store density does it take to flip it from infeasible to feasible?

The node being tested is *not* Amazon Go (which automated checkout only, kept prep/restock
labor, and carried expensive sensor tech) and *not* a staffed store (Foxtrot — the closest
U.S. attempt at staffed small-format urban fresh convenience, though premium-positioned and
without konbini logistics — filed Chapter 7 in 2024). It is a small multi-SKU fresh store,
replenished 2–3×/day from a SoDo commissary, run on ~6 on-site labor hours/day.

## 2. Method (the chain)

| Phase | Model | Key output |
|---|---|---|
| 1 Demand | Weighted daytime catchment: `workers + 0.5×residents`, area-apportioned from census tracts | $/day demand per neighborhood |
| 2 Network | OSM drive graph, per-edge speeds, congestion factor | Hub→neighborhood drive times |
| 3 Siting | MCLP (maximal covering, fixed p) on 1,061 street-corner demand points | Store sites + coverage-vs-p curve |
| 4 Routing | VRP with capacity + fresh-window constraints (OR-Tools) | Fleet size + daily delivery cost |
| 5 Economics | Per-store P&L vs pre-registered bar + star-parameter sweeps | The verdict + tipping thresholds |

Data: ACS 2024 (residents), LEHD LODES 2023 (workplace jobs), TIGER 2024 (tract shapes),
Seattle City Clerk neighborhood boundaries, OpenStreetMap. All sources with links in
[SOURCES.md](../SOURCES.md).

## 3. Results by phase

**Demand.** The northern core holds ~283k weighted daytime catchment. Worker-weighting is
decisive: Capitol Hill ranks #1 by residents but #5 by demand once jobs dominate; the CBD
(7.4k residents, 77k jobs) ranks #1. External cross-check: our 283k study-area jobs vs the
Downtown Seattle Association's ~337k for its (larger) downtown definition.

**Drive times.** All 7 neighborhood centers are 3.9–9.8 congested minutes from the SoDo hub —
roughly 3× headroom inside the 30-minute fresh window. Within this land-contiguous core,
**logistics reach is not the binding constraint**. (Cross-water expansion, where geography
does bind, is deferred future work.)

**Siting.** Demand concentration is extreme: 5 optimally-placed stores cover 64.8% of
catchment; 10 cover 86.6%; 20 cover 99.0%. Marginal coverage collapses 16× from store #6
(+21,411 catchment) to store #20 (+1,302). The optimizer reproduces konbini "area
dominance" clustering unprompted — overlapping walksheds along the Belltown–CBD–Pioneer
Square spine beat even spacing.

**Routing.** The fresh window binds, not van capacity (loads run 9–42% of capacity while
last handoffs land at minute 26–27 of 30). A van manages ~3 stops per run → 4 vans for 10
stores → **$773/day total delivery cost ($77/store)**, fleet-dominated. Modeling note that
mattered: the freshness clock stops at the last handoff (the paid return leg doesn't age
goods) — counting the return inside the window would wrongly cost 5 vans/$946.

**Economics.** At baseline (p=10, capture 2.5%, 6h labor):

- **Pre-registered bar (contribution > 0): 10 of 10 stores clear it.** Break-even is only
  88 transactions/day — the bar, committed before results, turned out generous; we report
  it as registered.
- **Fully loaded** (adding rent, hub allocation, amortized capex): **9 of 10 stores
  positive**; the fringe store (~240 txns/day) loses ~$474/day. Median payback ≈ 0.5 years
  (secondary lens; capex-assumption-dependent).

## 4. The verdict and what flips it

**Conditionally feasible. The condition is demand (capture rate); automation is the
margin-maker at Seattle wages.**

| Threshold | Value |
|---|---|
| Median store fully-loaded break-even (automated, 6h) | **capture ≈ 1.7%** |
| Median store fully-loaded break-even (staffed, 32h) | **capture ≈ 2.6%** |
| Automation dividend (6h vs 32h @ $21.30/h) | **≈ $554/store-day ≈ 0.9pp of capture slack** |
| Below capture ≈ 1.5% | Median store negative at any staffing level; only the densest corners persist (5 of 10 at 1.5%, 1 of 10 at 1.0%) |
| Viable network size at baseline | Formally evaluated at p=10: 9 of 10 viable. Marginal-store arithmetic (revenue vs cost incl. hub share) puts the ceiling in the mid-teens — not formally optimized |

The staffed reference case sits almost exactly at break-even at baseline demand — an
independent rhyme with Foxtrot's real-world failure. Automation doesn't create demand; it
widens the demand band in which the concept survives — from "needs konbini-tier adoption"
(~2.6%) to "needs good adoption" (~1.7%).

### Stress case: what if we're wrong about everything at once?

The sweeps above vary one parameter at a time; bad worlds correlate. `src/econ/stress.py`
sets four levers **jointly adverse** (capture 1.5%, rent $12k/mo, spoilage 15%, wage $26 —
each inside its swept range) and re-runs the P&L:

| | Baseline | **Stress** |
|---|---|---|
| Pre-registered bar (contribution > 0) | 10 / 10 | **10 / 10** |
| Fully-loaded positive stores | 9 / 10 | **3 / 10** |
| Network fully-loaded total | +$6,211/day | **−$3,486/day** |

Read: the *variable* economics survive even joint pessimism (every store still covers
product, delivery, and labor), but the **fixed-cost stack — rent, hub allocation, capex —
kills the network**: only the three densest corners (~620–690 txns/day even at 1.5%
capture) stay positive, and only barely (+$32 to +$166/day). A cherry-picked 3-store
network is the surviving skeleton — with the caveat that hub opex is still allocated
across 10 stores here; at p=3 the hub share triples and would sink those too unless the
commissary shrinks with the network.

**So the verdict is genuinely conditional, and this is the boundary:** under joint
pessimism the 10-store concept fails. Feasibility lives or dies on the baseline
assumptions being roughly right — chiefly capture — which is exactly why they are
sourced, derived, and swept rather than asserted.

## 5. Honest limitations

- **Baseline optimism.** Top-store volumes (1,100+ txns/day) are busiest-konbini territory;
  the thresholds, not the point estimates, are the finding.
- **Rent is flat** ($8k/mo — now derived from Seattle CBD asking rents of ~$46/sqft on a
  ~1,200–1,600 sqft footprint) while the model deliberately picks the best corners downtown;
  a per-store rent *surface* (prime corners cost more) remains the refinement.
- **Capture rate is derived, not measured** (cited volumes ÷ our computed walkshed
  populations). It is the star sensitivity for exactly this reason.
- **Uniform dasymetric split** of tract population across street corners; LODES is
  block-level and would sharpen this.
- **Delivery share held constant** across economic sweeps (defensible: the fleet is
  window-bound, so cost is ~independent of demand volume) and split equally across stores.
- **Assumed operational numbers**: hub opex, vehicle costs, product margin, spoilage,
  visit frequency, capex — all flagged in the table below and swept where starred.
- **No notebooks**: the narrative lives in documented `src/` scripts + `run_all.py`
  (a deliberate deviation from the original plan; notebooks remain future work).

## 6. Assumption table

Generated from [`assumptions.yaml`](../assumptions.yaml) — see the file for per-parameter
notes and derivations, and [SOURCES.md](../SOURCES.md) for citations.

| Parameter | Value | Swept range | Source | Star |
|---|---|---|---|---|
| `study_area.neighborhoods` | Downtown/CBD, Belltown, South Lake Union, Capitol Hill, First Hill, Pioneer Square, Chinatown-International District |  | assumed |  |
| `study_area.production_hub` | SoDo industrial district |  | assumed |  |
| `study_area.production_hub_coords` | 47.5789, -122.3345 |  | assumed |  |
| `demand.capture_rate` | 0.025 | 0.01–0.05 | derived | ⭐ |
| `demand.visit_frequency` | 1.0 |  | assumed |  |
| `demand.avg_ticket` | 7.8 | 5.0–10.0 | cited |  |
| `demand.worker_weight` | 1.0 |  | assumed |  |
| `demand.resident_weight` | 0.5 | 0.2–0.8 | assumed | ⭐ |
| `network.fresh_delivery_window_min` | 30 |  | assumed |  |
| `network.congestion_factor` | 1.4 | 1.2–1.8 | assumed | ⭐ |
| `facility_location.num_nodes_p` | 10 | 5–20 | assumed | ⭐ |
| `facility_location.coverage_radius_m` | 400 |  | assumed |  |
| `routing.deliveries_per_day` | 3 | 1–4 | cited | ⭐ |
| `routing.vehicle_capacity_units` | 200 |  | assumed |  |
| `routing.transactions_per_unit` | 10 |  | assumed |  |
| `routing.service_minutes_per_stop` | 5 |  | assumed |  |
| `routing.vehicle_fixed_cost_per_day` | 150 |  | assumed |  |
| `routing.driver_cost_per_hour` | 30 |  | derived |  |
| `economics.node_rent_per_month` | 8000 |  | derived |  |
| `economics.labor_wage_per_hour` | 21.3 | 19.0–26.0 | cited | ⭐ |
| `economics.staff_hours_per_day` | 6 | 2–32 | assumed | ⭐ |
| `economics.automation_capex_per_store` | 150000 | 50000–400000 | assumed | ⭐ |
| `economics.capex_amortization_years` | 7 |  | assumed |  |
| `economics.product_cost_ratio` | 0.65 |  | assumed |  |
| `economics.spoilage_rate` | 0.08 | 0.03–0.15 | assumed | ⭐ |
| `economics.hub_opex_per_day` | 5000 |  | assumed |  |

**Pre-registered feasibility bar** (committed before results): primary — contribution
margin per node > 0 (revenue − product incl. spoilage − delivery share − direct labor);
secondary — payback < 5 years.

## 7. Future work

Cross-water expansion (Ballard/Eastside — where Seattle's geography actually bites);
per-store rent surfaces; block-level dasymetric demand; distance-weighted gravity demand;
network-distance walksheds; joint location-routing (LRP) instead of the fixed-hub
decomposition; stochastic demand + discrete-event simulation; time-of-day demand;
consumer demand sensing as a richer input layer; notebook narrative.

**Format generalization.** The pipeline is a general feasibility engine for
hub-replenished walk-up node networks; the konbini micro-store is one parameter file.
A single-product automated kiosk (premium drink machines and similar vending-first
formats) is the natural second case: swap capex, labor (restock folds into the delivery
stop), walkshed radius, ticket, and cadence in `assumptions.yaml` and re-run. Model
prediction worth testing: at kiosk scale the binding constraint flips from the fresh
window to machine capacity.
