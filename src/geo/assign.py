"""assign.py -- spatial join: tag each census tract with the study neighborhood it sits in.

Method: a tract is assigned to the neighborhood that contains its CENTROID (center
point). This makes it a clean one-tract -> one-neighborhood mapping. Tracts whose
centroid falls outside all 7 study neighborhoods are dropped (they're not in scope).

This is a deliberate simplification: a tract straddling a boundary is assigned whole
to whichever neighborhood holds its center. Areal apportionment (splitting a tract's
people across neighborhoods by overlap area) is the more precise future refinement.
"""

import sys
from pathlib import Path

import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT
from src.geo.boundaries import fetch_tract_boundaries
from src.geo.neighborhoods import fetch_study_neighborhoods
from src.demand.census import fetch_tract_population, fetch_tract_workers

WORKING_CRS = 32610   # UTM zone 10N (meters) -- accurate geometry for the Seattle area


def assign_tracts_to_neighborhoods():
    """Return the tracts that fall in our 7 neighborhoods, tagged + carrying population.

    Columns: geoid, neighborhood, population, worker_jobs, geometry.
    """
    tracts = fetch_tract_boundaries().to_crs(WORKING_CRS)
    hoods = fetch_study_neighborhoods().to_crs(WORKING_CRS)

    residents = fetch_tract_population()[["geoid", "population"]]
    workers = fetch_tract_workers()[["geoid", "worker_jobs"]]
    tracts = tracts.merge(residents, on="geoid", how="left").merge(workers, on="geoid", how="left")
    tracts["worker_jobs"] = tracts["worker_jobs"].fillna(0).astype(int)

    # Use the centroid so each tract lands in exactly one neighborhood.
    centroids = tracts.copy()
    centroids["geometry"] = tracts.geometry.centroid
    tagged = gpd.sjoin(centroids, hoods[["neighborhood", "geometry"]],
                       how="inner", predicate="within")

    # Re-attach the full tract polygons (the join used centroids), keep needed columns.
    result = tracts[["geoid", "geometry"]].merge(
        tagged[["geoid", "neighborhood", "population", "worker_jobs"]],
        on="geoid", how="inner")
    return gpd.GeoDataFrame(result, geometry="geometry", crs=tracts.crs)


def tract_neighborhood_pieces():
    """Cut tracts along neighborhood lines; each piece carries its area share of people.

    Returns a GeoDataFrame (WORKING_CRS): geoid, neighborhood, residents, workers,
    geometry -- one row per (tract x neighborhood) overlap. This is the finest
    demand surface we have; both the neighborhood totals and the Phase-3 siting
    inputs are built from it.
    """
    tracts = fetch_tract_boundaries().to_crs(WORKING_CRS)
    hoods = fetch_study_neighborhoods().to_crs(WORKING_CRS)

    residents = fetch_tract_population()[["geoid", "population"]]
    workers = fetch_tract_workers()[["geoid", "worker_jobs"]]
    tracts = tracts.merge(residents, on="geoid", how="left").merge(workers, on="geoid", how="left")
    tracts[["population", "worker_jobs"]] = tracts[["population", "worker_jobs"]].fillna(0)
    tracts["tract_area"] = tracts.geometry.area

    pieces = gpd.overlay(tracts, hoods[["neighborhood", "geometry"]], how="intersection")
    pieces["frac"] = pieces.geometry.area / pieces["tract_area"]   # share of tract in this piece
    pieces["residents"] = pieces["population"] * pieces["frac"]
    pieces["workers"] = pieces["worker_jobs"] * pieces["frac"]
    return pieces[["geoid", "neighborhood", "residents", "workers", "geometry"]]


def apportion_to_neighborhoods():
    """Sum the tract pieces up to per-neighborhood totals.

    Returns a DataFrame: neighborhood, residents, worker_jobs.
    """
    pieces = tract_neighborhood_pieces()
    out = (pieces.groupby("neighborhood")
                 .agg(residents=("residents", "sum"), worker_jobs=("workers", "sum"))
                 .round().astype(int).reset_index())
    return out.sort_values("worker_jobs", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    tagged = assign_tracts_to_neighborhoods()
    print(f"Tracts assigned to the study area: {len(tagged)} of 495 King County tracts")
    print("\nTracts per neighborhood:")
    print(tagged.groupby("neighborhood").size().sort_values(ascending=False).to_string())
    print("\nStudy-area totals (preview of step 4):")
    print(f"  residents  : {tagged['population'].sum():,}")
    print(f"  worker jobs: {tagged['worker_jobs'].sum():,}")

    # Verification map: tracts colored by their assigned neighborhood, with outlines.
    from src.viz.plots import plot_tract_assignment
    hoods = fetch_study_neighborhoods()
    out = plot_tract_assignment(tagged, hoods)
    print(f"Saved verification map -> {out.name}")

    # The accurate per-neighborhood numbers, via areal apportionment.
    print("\n--- Areal apportionment (splits straddling tracts by area share) ---")
    apportioned = apportion_to_neighborhoods()
    print(apportioned.to_string(index=False))
    print(f"\nApportioned totals -> residents {apportioned['residents'].sum():,}, "
          f"workers {apportioned['worker_jobs'].sum():,}")
    print(f"(centroid method gave  residents {tagged['population'].sum():,}, "
          f"workers {tagged['worker_jobs'].sum():,})")

    # Save the real per-neighborhood numbers as the canonical study-area data table.
    apportioned["source"] = "apportioned: ACS2024 residents + LODES2023 workers"
    apportioned.to_csv(PROJECT_ROOT / "data" / "neighborhoods.csv", index=False)
    print("\nWrote real per-neighborhood data -> data/neighborhoods.csv")
