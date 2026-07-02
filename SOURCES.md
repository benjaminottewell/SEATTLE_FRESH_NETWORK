# Sources & References

Every external dataset and published benchmark this project relies on, with links.
This file backs the `source: cited|derived` flags in [`assumptions.yaml`](assumptions.yaml)
and the data-pipeline modules in [`src/`](src/). Last reviewed: **2026-07-01** (all URLs
verified resolving on this date).

---

## 1. Data sources (pipeline inputs)

### Resident population — U.S. Census ACS 5-year
- **Used for:** residents per census tract (a component of the demand catchment).
- **Dataset:** American Community Survey 5-year, **2024 vintage** (2020–2024), variable
  `B01003_001E` (total population).
- **Access:** Census Data API — `https://api.census.gov/data/2024/acs/acs5`
- **Docs:** https://www.census.gov/data/developers/data-sets/acs-5year.html
- **Code:** [`src/demand/census.py`](src/demand/census.py) → `fetch_tract_population()`
- **Note:** 5-year (not 1-year) is required for tract-level geography. Survey data, so it
  carries published margins of error.

### Worker / daytime population — LEHD LODES
- **Used for:** jobs counted at their *workplace* (the daytime-population driver, weighted
  most heavily in the catchment).
- **Dataset:** LEHD Origin-Destination Employment Statistics, **LODES8**, Washington
  Workplace Area Characteristics (`WAC`), **2023**, segment `S000`, job type `JT00`,
  total jobs `C000`.
- **Access:** https://lehd.ces.census.gov/data/lodes/LODES8/wa/wac/ (file
  `wa_wac_S000_JT00_2023.csv.gz`)
- **Docs / tool:** https://lehd.ces.census.gov/data/ · OnTheMap: https://onthemap.ces.census.gov/
- **Code:** [`src/demand/census.py`](src/demand/census.py) → `fetch_tract_workers()`
- **Note:** Built from administrative unemployment-insurance wage records (~95% of U.S.
  jobs). Counts *jobs*, not people (a 2-job holder counts twice); worksite is
  employer-reported; small privacy noise is added.

### Census tract boundaries — TIGER/Line
- **Used for:** tract polygons, to place population on the map and apportion it to
  neighborhoods.
- **Dataset:** TIGER/Line shapefiles, **2024**, Washington tracts (`tl_2024_53_tract`).
- **Access:** https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_53_tract.zip
- **Docs:** https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- **Code:** [`src/geo/boundaries.py`](src/geo/boundaries.py) → `fetch_tract_boundaries()`

### Seattle neighborhood boundaries — City Clerk "Neighborhood Map Atlas"
- **Used for:** the 7 study-area neighborhood polygons.
- **Dataset:** Seattle City Clerk Neighborhood Map Atlas, accessed via the widely-used
  `seattleio` mirror of the city's open GIS data.
- **Access (used):** https://raw.githubusercontent.com/seattleio/seattle-boundaries-data/master/data/neighborhoods.geojson
- **Original source:** https://data-seattlecitygis.opendata.arcgis.com/datasets/city-clerk-neighborhoods
- **Code:** [`src/geo/neighborhoods.py`](src/geo/neighborhoods.py) → `fetch_study_neighborhoods()`
- **Note:** The dataset's fine `name` values are reconciled to my study-area names in the
  `STUDY_AREA` map (Capitol Hill = the "Broadway" core).

---

## 2. Assumption benchmarks (parameter grounding)

### `capture_rate` = 0.025 (range 0.01–0.05) ⭐ — flag: **derived**
Fraction of the daytime catchment that transacts per day, which is the model's most uncertain input.
That is why the swept range is deliberately wide. No published number exists for this exact
format, so it is **derived** from cited transaction volumes and my own computed densities
(not flagged `cited` — that would overclaim).

**Cited numerators (store transaction volumes):**
- **U.S. convenience average (NACS 2023):** 1,491 transactions/day *including fuel pump*
  (45,312/month) — in-store-only volume is lower.
  https://www.cspdailynews.com/company-news/us-convenience-store-sales-reach-new-highs ·
  https://www.convenience.org/stay-current/news/2024/april/4/1-us-c-store-sales-hit-860-billion_research
- **Japanese 7-Eleven (the ceiling analog):** ~¥664k/day sales ⇒ ~950 customers/day at the
  ~¥700 (~$4–5) konbini basket. https://www.statista.com/topics/8484/convenience-stores-in-japan/

**Computed denominator (people per 400m walkshed, from my apportioned data —
reproducible from `src/geo/assign.py` + neighborhood polygon areas):**

| Neighborhood | Catchment ÷ area ⇒ per 400m walkshed |
|---|---|
| Downtown/CBD | ~46,000 |
| First Hill / SLU / Belltown | ~25,000 |
| Pioneer Square | ~11,000 |
| Chinatown-ID / Capitol Hill | ~5,000–6,000 |

**Derivation:** a 550–950 txn/day store against those walksheds implies daily capture of
~1.2% (CBD, dense) up to ~5% (lighter districts / konbini-like penetration). Range
**[0.01, 0.05]**, midpoint **0.025**. Interpreted as network penetration of *covered*
catchment — Phase 3 siting counts only demand within store coverage radii.

> ⚠️ An earlier draft anchored on **Amazon Go** (~550 txns/day). That figure is a 2018–19
> hype-era analyst estimate, and the concept is now being wound down, so it is used only as
> illustrative context (below), **not** a load-bearing anchor.

### Market context — have U.S. konbini-style ventures worked?
Directly relevant to the feasibility question, and honest to surface: the closest U.S.
attempts have struggled **commercially** — mostly on cost/economics, not obviously on demand.
- **Amazon Go** (cashierless grab-and-go): down to ~17 stores by late 2024 (NYC closures
  cited high lease costs); Amazon announced it is closing **all** Amazon Go + Amazon Fresh
  stores by ~early 2026, refocusing "Just Walk Out" on ~360 third-party sites.
  https://www.fastcompany.com/91483585/amazon-go-closing ·
  https://techcrunch.com/2024/10/04/amazon-closes-more-of-its-cashierless-convenience-stores/
- **Foxtrot** (upscale urban convenience + café hybrid — arguably the closest U.S. konbini
  analog): abruptly closed all 35 stores and filed Chapter 7 in 2024; a few Chicago
  locations later reopened under new ownership. Closure framed around shoppers
  "recalculating the value of convenience" (price vs. time saved).
  https://en.wikipedia.org/wiki/Foxtrot_(convenience_store) ·
  https://www.mintel.com/insights/market-news/foxtrot-doms-market-sudden-closure-the-broader-impact/

**Why this strengthens the project:** these are real-world tests of exactly what I model,
and they broke on the **unit economics** (lease + labor/tech costs, price sensitivity) — the
very constraint Phase 5 quantifies. It confirms the feasibility answer is genuinely uncertain
and likely *conditional*, not an obvious yes. Excellent README "why this question is live"
material.

### `avg_ticket` = $7.80 (range $5–$10)
- **U.S. convenience average in-store basket, 2023 = $7.80** (up 3.7% year-over-year), per
  NACS State of the Industry data. Of $859.8B total 2023 industry sales, $327.6B were
  in-store.
  https://www.cspdailynews.com/company-news/us-convenience-store-sales-reach-new-highs ·
  https://www.convenience.org/stay-current/news/2024/april/4/1-us-c-store-sales-hit-860-billion_research

### `labor_wage_per_hour` = $21.30 ⭐
- **Seattle minimum wage effective 2026-01-01: $21.30/hour** (up from $20.76 in 2025),
  applying to all employer sizes; indexed annually to CPI-W (2.61% for the period ending
  Aug 2025). Source: City of Seattle Office of Labor Standards.
  https://www.seattle.gov/laborstandards/ordinances/minimum-wage ·
  https://www.seattle.gov/documents/Departments/LaborStandards/Memo_2026_Seattle_MW_Increase.pdf

---

### `node_rent_per_month` = $8,000 — flag: **derived**
- **Seattle CBD retail asking rents average $46.38/sqft/yr** across 105 active listings
  (citywide average ~$30; NNN is the dominant lease type, so tenants add
  taxes/insurance/CAM of roughly $10–15/sqft).
  https://www.commercialcafe.com/retail/us/wa/seattle/ ·
  https://www.loopnet.com/search/retail-space/downtown-seattle-seattle-wa/for-lease/
- Derivation: ~1,200–1,600 sqft micro-format × ~$56–61/sqft gross ⇒ **~$6–9k/month**;
  the model's $8k sits mid-band.

### `driver_cost_per_hour` = $30 — flag: **derived**
- Seattle delivery-driver market base ~$22–25/hr per aggregated listings
  (Indeed / ZipRecruiter / Glassdoor, 2025–26), plus ~20–30% employer burden ⇒
  ~$27–32/hr fully loaded; $30 mid-band.
  https://www.indeed.com/career/delivery-driver/salaries/Seattle--WA ·
  https://www.ziprecruiter.com/Salaries/Local-Delivery-Driver-Salary-in-Seattle,WA

### `vehicle_fixed_cost_per_day` = $150 — assumed (conservative), anchored
- Refrigerated cargo-van leases start ~**$1,999/month (~$66/day)** as of 2026; larger
  reefer box trucks from ~$1,200/month (Ryder). All-in with commercial insurance +
  maintenance ≈ $90–120/day; the model's $150 deliberately holds a buffer (fuel,
  utilization slack). https://refrigeratedrentalvans.com/pricing/ ·
  https://www.ryder.com/en-us/fleet-leasing/trucks/refrigerated-box-trucks

### `spoilage_rate` = 0.08 (range 0.03–0.15) ⭐ — plausibility-checked
No clean published percentage exists, but konbini waste reporting gives absolutes:
roughly **¥20,000–50,000 of discarded food per store per day** against ~¥664,000/day
typical sales ⇒ waste ≈ **3–7.5% of sales value**. My 8%-of-COGS assumption equals
5.2% of revenue — mid-band. Flag stays `assumed` (the check is order-of-magnitude,
not a measurement); the 3–15% sweep spans the plausible space.
https://planetforward.org/story/reinventing-convenience-konbini/ ·
https://zenbird.media/where-does-japans-food-waste-come-from/

## 3. Validation / cross-checks

### Downtown employment (external sanity check)
- **Downtown Seattle Association** State of Downtown: ~**337,000 jobs** in downtown Seattle.
  My model's 7-neighborhood total is ~283,000 worker jobs — consistent given differing
  boundary definitions.
  https://www.kuow.org/stories/seattle-has-lost-its-mojo-downtown-seattle-association-report-claims-taxes-are-driving-out-jobs

---

## 4. Methodological / prior work
- Location-routing template (set-covering + multi-depot capacitated VRP with time windows,
  MDCVRP-TW) adapted from a U.S. food-desert grocery-hub study. Full citation to be added
  in the README "Related Work" section (see [`SEATTLE_PLAN.md`](SEATTLE_PLAN.md) §3a).

---

*Accessed dates: data pulls and benchmark lookups performed 2026-06. Cached raw pulls live
in `data/raw/` (git-ignored); re-running the `src/` modules regenerates them.*
