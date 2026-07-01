"""census.py -- pull real population data from the U.S. Census ACS API.

We fetch tract-level numbers for King County (where Seattle sits) and cache the
result to data/raw/ so reruns don't keep hitting the API -- a repo convention,
and good manners toward a free public service.
"""

import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT, get_census_key

# King County, WA (state + county FIPS).
STATE_FIPS = "53"
COUNTY_FIPS = "033"
ACS_YEAR = "2024"   # latest available ACS 5-year vintage (covers 2020-2024)
LODES_YEAR = "2023"  # latest available LODES workplace-jobs year for WA
CACHE_DIR = PROJECT_ROOT / "data" / "raw"


def fetch_tract_population(year=ACS_YEAR, use_cache=True):
    """Return a DataFrame of population per census tract in King County.

    Columns: geoid, name, population, tract.
    The raw pull is cached to data/raw/ so we only ever hit the API once.
    """
    cache_path = CACHE_DIR / f"acs{year}_king_tract_population.csv"

    if use_cache and cache_path.exists():
        print(f"Loading cached Census data <- {cache_path.name}")
        return pd.read_csv(cache_path, dtype={"geoid": str, "tract": str})

    key = get_census_key()
    if not key:
        raise RuntimeError("No Census API key found. Set CENSUS_API_KEY in your .env file.")

    print(f"Fetching ACS {year} tract population from the Census API ...")
    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": "NAME,B01003_001E",   # B01003_001E = total population
        "for": "tract:*",
        "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",
        "key": key,
    }
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    rows = resp.json()

    # The API returns a list of lists: rows[0] is the header, the rest are data.
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.rename(columns={"NAME": "name", "B01003_001E": "population"})
    df["population"] = df["population"].astype(int)
    df["geoid"] = df["state"] + df["county"] + df["tract"]   # 11-digit unique tract ID
    df = df[["geoid", "name", "population", "tract"]]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache_path, index=False)
    print(f"Saved {len(df)} tracts -> data/raw/{cache_path.name}")
    return df


def fetch_tract_workers(year=LODES_YEAR, use_cache=True):
    """Return a DataFrame of total WORKER JOBS per census tract in King County.

    Source: LEHD LODES Workplace Area Characteristics -- jobs counted at their
    WORK location, i.e. the daytime/worker-population proxy. We download the
    statewide file, keep only King County blocks, and sum jobs up to the tract.
    Columns: geoid, worker_jobs.
    """
    cache_path = CACHE_DIR / f"lodes{year}_king_tract_workers.csv"

    if use_cache and cache_path.exists():
        print(f"Loading cached LODES data <- {cache_path.name}")
        return pd.read_csv(cache_path, dtype={"geoid": str})

    url = (f"https://lehd.ces.census.gov/data/lodes/LODES8/wa/wac/"
           f"wa_wac_S000_JT00_{year}.csv.gz")
    print(f"Fetching LODES {year} workplace jobs ...")
    # w_geocode is a 15-digit block id -- read as text so leading zeros survive.
    df = pd.read_csv(url, dtype={"w_geocode": str}, usecols=["w_geocode", "C000"])

    # Keep only King County: blocks whose id starts with state 53 + county 033.
    king = df[df["w_geocode"].str.startswith("53033")].copy()

    # First 11 digits of a block id ARE its tract id -> group and sum the jobs.
    king["geoid"] = king["w_geocode"].str[:11]
    workers = (king.groupby("geoid", as_index=False)["C000"].sum()
                   .rename(columns={"C000": "worker_jobs"}))

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    workers.to_csv(cache_path, index=False)
    print(f"Saved {len(workers)} tracts -> data/raw/{cache_path.name}")
    return workers


if __name__ == "__main__":
    residents = fetch_tract_population()
    workers = fetch_tract_workers()

    merged = residents.merge(workers, on="geoid", how="left")
    merged["worker_jobs"] = merged["worker_jobs"].fillna(0).astype(int)

    print(f"\nKing County totals:")
    print(f"  residents  (ACS {ACS_YEAR})    : {residents['population'].sum():>10,}")
    print(f"  worker jobs (LODES {LODES_YEAR}): {workers['worker_jobs'].sum():>10,}")

    cols = ["name", "population", "worker_jobs"]
    print("\nTop 5 tracts by RESIDENTS:")
    print(merged.sort_values("population", ascending=False).head()[cols].to_string(index=False))
    print("\nTop 5 tracts by WORKERS (the daytime core):")
    print(merged.sort_values("worker_jobs", ascending=False).head()[cols].to_string(index=False))
