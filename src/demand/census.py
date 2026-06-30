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

# King County, WA, in Census FIPS codes (the government's ID numbers for places).
STATE_FIPS = "53"
COUNTY_FIPS = "033"
ACS_YEAR = "2023"
CACHE_DIR = PROJECT_ROOT / "data" / "raw"


def fetch_tract_population(year=ACS_YEAR, use_cache=True):
    """Return a DataFrame of population per census tract in King County.

    Columns: geoid, name, population, tract.
    The raw pull is cached to data/raw/ so we only ever hit the API once.
    """
    cache_path = CACHE_DIR / f"acs{year}_king_tract_population.csv"

    # If we already pulled this once, just read the saved file -- no API call.
    if use_cache and cache_path.exists():
        print(f"Loading cached Census data <- {cache_path.name}")
        return pd.read_csv(cache_path, dtype={"geoid": str, "tract": str})

    key = get_census_key()
    if not key:
        raise RuntimeError("No Census API key found. Set CENSUS_API_KEY in your .env file.")

    print(f"Fetching ACS {year} tract population from the Census API ...")
    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": "NAME,B01003_001E",                       # B01003_001E = total population
        "for": "tract:*",                                # every tract...
        "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",  # ...in King County
        "key": key,
    }
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()                              # blow up loudly if the request failed
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


if __name__ == "__main__":
    tracts = fetch_tract_population()
    print(f"\nKing County tracts : {len(tracts)}")
    print(f"Total population    : {tracts['population'].sum():,}")
    print("\nLargest 5 tracts by population:")
    print(tracts.sort_values("population", ascending=False).head().to_string(index=False))
