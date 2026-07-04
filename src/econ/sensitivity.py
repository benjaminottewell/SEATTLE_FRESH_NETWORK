"""sensitivity.py -- Phase 5: sweep the star parameters and find where the verdict tips.

The siting (store catchments) and routing (delivery share) are held fixed while
economic levers vary: capture_rate scales transactions linearly and staff hours
price the automation trade, so neither requires re-solving the MILP/VRP. The
delivery share is window-bound (Phase 4), hence ~independent of capture.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT, load_assumptions, get_value, get_range
from src.econ.economics import baseline_stores, delivery_cost_per_store, store_pnl


def sweep_capture(stores, a, delivery, n=41):
    """The star sweep: verdict vs capture_rate across its assumed range."""
    lo, hi = get_range(a, "demand", "capture_rate")
    rows = []
    for c in np.linspace(lo, hi, n):
        pnl = store_pnl(stores, a, delivery, capture=c)
        rows.append({
            "capture_rate": c,
            "stores_clearing_bar": int(pnl["clears_bar"].sum()),
            "stores_fully_loaded_pos": int((pnl["fully_loaded"] > 0).sum()),
            "median_fully_loaded": pnl["fully_loaded"].median(),
        })
    return pd.DataFrame(rows)


def sweep_staff_hours(stores, a, delivery, captures=(0.025, 0.015), n=31):
    """The automation lever: verdict vs on-site labor hours, at two capture scenarios."""
    lo, hi = get_range(a, "economics", "staff_hours_per_day")
    rows = []
    for c in captures:
        for h in np.linspace(lo, hi, n):
            pnl = store_pnl(stores, a, delivery, capture=c, staff_hours=h)
            rows.append({
                "capture_rate": c,
                "staff_hours": h,
                "stores_fully_loaded_pos": int((pnl["fully_loaded"] > 0).sum()),
                "median_fully_loaded": pnl["fully_loaded"].median(),
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    a = load_assumptions()
    stores = baseline_stores(a)
    delivery = delivery_cost_per_store(a)

    print("Sweeping capture_rate (the star) ...")
    cap = sweep_capture(stores, a, delivery)
    print("Sweeping staff hours (the automation lever) ...")
    hours = sweep_staff_hours(stores, a, delivery)

    cap.to_csv(PROJECT_ROOT / "outputs" / "tables" / "sensitivity_capture.csv", index=False)
    hours.to_csv(PROJECT_ROOT / "outputs" / "tables" / "sensitivity_staff_hours.csv", index=False)

    # Headline thresholds: the capture rate where the network flips.
    all_ok = cap[cap["stores_fully_loaded_pos"] == cap["stores_fully_loaded_pos"].max()]
    none_ok = cap[cap["stores_fully_loaded_pos"] == 0]
    print(f"\nAt baseline staffing ({get_value(a, 'economics', 'staff_hours_per_day')}h/day):")
    if len(none_ok):
        print(f"  below capture ~ {none_ok['capture_rate'].max():.3%}: NO store is fully-loaded viable")
    med = cap.loc[(cap['median_fully_loaded'] > 0)]
    if len(med):
        print(f"  median store turns fully-loaded positive at capture ~ "
              f"{med['capture_rate'].min():.3%}")

    from src.viz.plots import plot_capture_sensitivity, plot_automation_sensitivity
    f1 = plot_capture_sensitivity(cap, baseline=get_value(a, "demand", "capture_rate"),
                                  staff_hours=get_value(a, "economics", "staff_hours_per_day"))
    f2 = plot_automation_sensitivity(hours, baseline_hours=get_value(a, "economics", "staff_hours_per_day"))
    print(f"\nSaved charts -> {f1.name}, {f2.name}")
