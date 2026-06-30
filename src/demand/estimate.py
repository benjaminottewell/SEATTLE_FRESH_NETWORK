''' estimate.py -- Phase 1 demand estimation. This is the first step in the pipeline and turns "people nearby" into "dollars per day" '''
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  
from src.config import load_assumptions, get_value, PROJECT_ROOT
from src.viz.plots import plot_demand_by_neighborhood

def estimate_daily_demand(catchment_population, assumptions):
    """Dollars/day a store earns: population x capture x frequency x ticket."""
    capture_rate = get_value(assumptions, "demand", "capture_rate")
    visit_frequency = get_value(assumptions, "demand", "visit_frequency")
    avg_ticket = get_value(assumptions, "demand", "avg_ticket")

    daily_demand = catchment_population * capture_rate * visit_frequency * avg_ticket
    return daily_demand


def estimate_area_demand(neighborhoods, assumptions):
    """Run the single-store model across every neighborhood in a table.

    `neighborhoods` is a pandas DataFrame (a spreadsheet-in-code) that has a
    'daytime_population' column. We loop over each row, reuse your
    estimate_daily_demand(), attach the answer as a new 'daily_demand' column,
    then sort so the highest-demand neighborhood is on top.
    """
    demands = []
    for population in neighborhoods["daytime_population"]:
        demands.append(estimate_daily_demand(population, assumptions))

    result = neighborhoods.copy()
    result["daily_demand"] = demands
    return result.sort_values("daily_demand", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    a = load_assumptions()

    # Load the neighborhood table (placeholder daytime populations for now).
    csv_path = PROJECT_ROOT / "data" / "neighborhoods.csv"
    neighborhoods = pd.read_csv(csv_path)

    ranked = estimate_area_demand(neighborhoods, a)

    print("Estimated daily demand by neighborhood (PLACEHOLDER populations):\n")
    print(ranked[["neighborhood", "daytime_population", "daily_demand"]].to_string(index=False))

    total = ranked["daily_demand"].sum()
    print(f"\nWhole study area: ${total:,.0f} per day across {len(ranked)} neighborhoods")

    fig_path = plot_demand_by_neighborhood(ranked)
    print(f"Saved chart -> {fig_path}")