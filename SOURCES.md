# Sources & References

Every external dataset and published benchmark this project relies on, with links.
This file backs the `source: cited` flags in [`assumptions.yaml`](assumptions.yaml) and
the data-pipeline modules in [`src/`](src/). Last reviewed: **2026-06-30**.

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
- **Note:** The dataset's fine `name` values are reconciled to our study names in the
  `STUDY_AREA` map (Capitol Hill = the "Broadway" core).

---

## 2. Assumption benchmarks (parameter grounding)

### `capture_rate` = 0.025 (range 0.01–0.05) ⭐
Fraction of the daytime catchment that transacts per day — the model's most uncertain input,
which is why the swept range is deliberately wide.

**Robust anchors (current, broad):**
- **U.S. convenience in-store traffic (NACS 2023)** — industry-standard, large sample
  (basket + volume below).
- **Busy urban cafés** (e.g., Starbucks) — ~500–600 transactions/day is typical for a
  high-traffic location; a good grab-and-go foot-traffic proxy.
- **Japanese 7-Eleven** — the ceiling: ~¥664k/day sales (~$4,200/day) ⇒ ~950 customers/day.
  https://www.statista.com/topics/8484/convenience-stores-in-japan/

**Derivation:** ~500–600 txns/day ÷ a ~15–25k dense-core walk catchment ⇒ ~2–3% daily
capture; range brackets conservative U.S. adoption (~1%) to konbini-like penetration (~5%).

> ⚠️ An earlier draft anchored on **Amazon Go** (~550 txns/day). That figure is a 2018–19
> hype-era analyst estimate, and the concept is now being wound down — so it is used only as
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

**Why this strengthens the project:** these are real-world tests of exactly what we model,
and they broke on the **unit economics** (lease + labor/tech costs, price sensitivity) — the
very constraint Phase 5 quantifies. It confirms the feasibility answer is genuinely uncertain
and likely *conditional*, not an obvious yes. Excellent README "why this question is live"
material.

### `avg_ticket` = $7.80 (range $5–$10)
- **U.S. convenience average basket, 2023 = $7.80** (also ~1,491 transactions/day incl.
  fuel-pump), per NACS State of the Industry.
  https://www.cspdailynews.com/company-news/us-convenience-store-sales-reach-new-highs ·
  https://www.convenience.org/stay-current/news/2024/april/4/1-us-c-store-sales-hit-860-billion_research

### `labor_wage_per_hour` ⭐ — TO VERIFY
- Flagged `cited` in `assumptions.yaml` but the exact current Seattle minimum wage still
  needs a confirmed official figure + link (City of Seattle Office of Labor Standards).
  **Open item.**

---

## 3. Validation / cross-checks

### Downtown employment (external sanity check)
- **Downtown Seattle Association** State of Downtown: ~**337,000 jobs** in downtown Seattle.
  Our model's 7-neighborhood total is ~283,000 worker jobs — consistent given differing
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
