# Findings — Konbini-Inspired Fresh-Convenience Network, Seattle v1.0

*The full narrative of the feasibility model: method, results, verdict, and limitations.
The condensed version lives in the [README](../README.md); every number below is
reproducible via `python run_all.py`.*

---

## 1. The question

Could a dense network of konbini-inspired, **low-labor automated fresh-convenience
micro-stores** make money in Seattle's dense northern core? And how much automation and
how many stores would it take to flip the answer from no to yes?

It matters to be precise about the type of store being tested, because the two famous American
attempts were different concepts. It is *not* Amazon Go, which automated checkout only,
kept the restocking and food-prep labor, and paid for expensive sensor technology. It is
*not* a staffed store either: Foxtrot, the closest U.S. attempt at small-format urban
fresh convenience (premium-positioned, and without konbini-style logistics), filed
Chapter 7 bankruptcy in 2024. The store tested here is a small shop selling a rotating
range of short-shelf-life fresh food, restocked 2 to 3 times a day from a SoDo
commissary (a central kitchen and warehouse), and run on about 6 paid on-site labor
hours per day.

## 2. Method (the chain)

The model is a chain of five phases. Each phase's output is the next phase's input, so
the final economics inherit every upstream decision.

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

**Demand.** I measure demand pressure as a weighted daytime population: each worker
counts as 1 and each resident as 0.5, because this format lives on daytime foot traffic
and residents are partly elsewhere during the day. By that measure the northern core
holds about 328,000 weighted catchment, with jobs contributing 283,000 of it. The worker
weighting turned out to be decisive: Capitol Hill has the most residents of the seven
neighborhoods but ranks only #5 in demand, while Downtown/CBD, with just 7,400 residents
but 77,000 jobs, ranks #1. As an external sanity check, my 283k study-area jobs sit
plausibly against the Downtown Seattle Association's ~337k count for its larger downtown
definition.

**Drive times.** I built a drivable street map from OpenStreetMap, estimated speeds from
road types, and then slowed everything by 40% to approximate downtown traffic. Even with
that penalty, every neighborhood center is only 3.9 to 9.8 minutes from the SoDo hub,
against a 30-minute freshness deadline. **Reach is not the binding constraint** anywhere
in this land-connected core; a van gets everywhere with roughly 3× time to spare.
(Cross-water expansion, where geography does start to bind, is deferred to future work.)

**Siting.** Store placement uses MCLP, a classic coverage optimizer: given a budget of p
stores, pick the street corners that put the most weighted population within a 5-minute
walk (400 m) of at least one store. Demand turns out to be extremely concentrated: 5
well-placed stores already cover 64.8% of the catchment, 10 cover 86.6%, and 20 cover
99.0%. Each added store buys less than the one before it. Store #6 adds 21,411 catchment
while store #20 adds only 1,302, a 16× collapse. Without being told to, the optimizer
reproduced the konbini "area dominance" playbook: clusters of overlapping walksheds
along the Belltown, Downtown, Pioneer Square spine beat spreading stores out evenly.

**Routing.** A vehicle-routing solver (OR-Tools) plans refrigerated van runs from the
SoDo hub to the stores under two limits: van capacity and the 30-minute freshness
window. Vans leave far from full (9 to 42% of
capacity) but their last handoffs land at minute 26 or 27 of the 30, so a van can only
reach about 3 stores per run. Ten stores therefore need 4 vans, and the whole delivery
operation costs **$773 per day, or $77 per store**, most of it fixed fleet cost rather
than driver time. One modeling decision mattered a lot here: the freshness clock stops
at the last handoff, because the drive back to the hub is paid time but does not age any
food. Counting the return leg inside the window would have wrongly demanded a 5th van
and $946 per day unnecessarily.

**Economics.** Every store gets a daily profit-and-loss test at two levels, at baseline
settings (10 stores, 2.5% capture, 6 staffed hours):

- **Contribution, the pre-registered feasibility bar: 10 of 10 stores clear it.**
  Contribution asks whether a day of operating pays for itself: revenue minus product
  cost (including spoilage), the store's delivery share, and on-site labor. Break-even
  turns out to be only 88 transactions per day. The bar, committed in
  `assumptions.yaml` before any results existed, proved generous; I report it as
  registered rather than move it after the fact.
- **Fully loaded, the operator's view: 9 of 10 stores are positive.** This adds the
  fixed bills: rent, the store's share of commissary operating cost, and store equipment
  paid off over 7 years. The one failing store is the fringe store (~240 transactions
  per day), which loses about $474 per day. Median payback on store capex is roughly
  half a year (a secondary lens, since it depends directly on the capex guess).

## 4. The verdict and what flips it

**Conditionally feasible. The condition is demand (the capture rate), and automation is
what makes the margins work at Seattle wages.**

| Threshold | Value |
|---|---|
| Median store fully-loaded break-even (automated, 6h) | **capture ≈ 1.7%** |
| Median store fully-loaded break-even (staffed, 32h) | **capture ≈ 2.6%** |
| Automation dividend (6h vs 32h at $21.30/h) | **≈ $554 per store-day ≈ 0.9 percentage points of capture** |
| Below capture ≈ 1.5% | The median store is negative at any staffing level; only the densest corners persist (5 of 10 at 1.5%, 1 of 10 at 1.0%) |
| Viable network size at baseline | Formally evaluated at p=10: 9 of 10 viable. Rough marginal-store arithmetic (revenue vs cost including hub share) puts the ceiling in the mid-teens; not formally optimized |

Two readings of that table. First, the staffed version of this store sits almost exactly
at break-even at baseline demand. Second, automation does not create demand; it widens the band of
demand in which the concept survives, from "needs Japanese konbini-tier adoption" (~2.6% of the
walkshed buying daily) down to "needs good adoption" (~1.7%).

### Stress case: what if I'm wrong about everything at once?

The sweeps above vary one parameter at a time, but bad worlds come correlated.
`src/econ/stress.py` sets four levers adverse at the same time (capture 1.5%, rent
$12k/month, spoilage 15%, wage $26/hour, each still inside its swept range) and re-runs
the P&L:

| | Baseline | **Stress** |
|---|---|---|
| Pre-registered bar (contribution > 0) | 10 / 10 | **10 / 10** |
| Fully-loaded positive stores | 9 / 10 | **3 / 10** |
| Network fully-loaded total | +$6,211/day | **−$3,486/day** |

The reading: even under joint pessimism every store still covers its variable costs
(product, delivery, labor), but the **fixed-cost stack of rent, hub share, and capex
kills the network**. Only the three densest corners stay positive (620 to 690
transactions per day even at 1.5% capture), and only barely (+$32 to +$166 per day). A
cherry-picked 3-store network is the surviving skeleton but with one important caveat: the
hub's operating cost is still split across 10 stores in this table. Run only 3 stores
and each store's hub share triples, which would sink even those three.

**So the verdict is genuinely conditional, and this is the main boundary.** Under joint
pessimism the 10-store concept fails. Feasibility lives or dies on the baseline
assumptions being roughly right, chiefly capture, which is exactly why every assumption
is sourced, derived, and swept rather than asserted.

## 5. Honest limitations

- **The baseline is optimistic.** The busiest stores are projected at 1,100+
  transactions per day, which is territory only the busiest konbini reach. The
  thresholds, not the point estimates, are the finding.
- **Rent is flat** at $8k/month (derived from Seattle CBD asking rents of ~$46/sqft on a
  1,200 to 1,600 sqft footprint) even though the model deliberately picks the best
  corners downtown. A per-store rent surface, where prime corners cost more, is the
  natural refinement.
- **The capture rate is derived, not measured**: published store transaction volumes
  divided by my computed walkshed populations. That is exactly why it is the star
  sensitivity.
- **Theft and external shrink are not modeled.** The spoilage rate covers waste from
  unsold fresh goods, not loss from theft. A store staffed for only a few hours a day in
  downtown Seattle carries real shrink risk, and solving exactly this problem is part of
  what made Amazon Go's technology so expensive. The low-staffing economics should be
  read as a best case on this front.
- **Demand is steady-state from day one.** Each store is priced at its settled capture
  rate, with no ramp-up period, no marketing spend, and no habit-building phase. A real
  launch would lose money for months while capture climbs toward its resting level, so
  the model understates early cash needs even where the daily P&L clears the bar.
- **Population is spread evenly across street corners** within each tract piece. The
  jobs data exists at block level and would sharpen this.
- **The delivery share is held constant** across the economic sweeps (defensible: the
  fleet is sized by the time window, so its cost barely moves with demand volume) and
  split equally across stores.
- **Several operating numbers are assumed**: hub opex, vehicle costs, product margin,
  spoilage, visit frequency, capex. All are flagged in the table below and swept where
  starred.

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

**Pre-registered feasibility bar** (committed before results): primary, contribution
margin per store > 0 (revenue minus product including spoilage, delivery share, and
direct labor); secondary, payback under 5 years.

## 7. Future work

- **Cross-water expansion** (Ballard, the Eastside): the geography that actually
  stresses the delivery window.
- **A per-store rent surface** instead of one flat rent.
- **Block-level demand** instead of spreading tract populations evenly across corners.
- **Distance-decayed (gravity) demand**: people next to a store should count for more
  than people at the walkshed edge.
- **Walksheds along the street network** instead of straight-line circles.
- **Joint location-routing (LRP)**: optimize siting and routing together instead of the
  fixed-hub shortcut.
- **Demand uncertainty**: stochastic demand and discrete-event simulation instead of
  steady daily averages, plus time-of-day patterns.
- **Consumer demand sensing** as a richer input layer.

**Format generalization.** The pipeline is really a general feasibility engine for any
"many small nodes, restocked from one hub, serving walk-up demand" concept; the konbini
micro-store is just one parameter file. A single-product automated kiosk (drink/food
machines and similar vending-first formats) is the natural second case: swap capex,
labor (restocking folds into the delivery stop), walkshed radius, ticket size, and
delivery cadence in `assumptions.yaml` and re-run. One model prediction worth testing:
at kiosk scale the binding constraint flips from the freshness window to the machine
capacity.