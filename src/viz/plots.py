"""plots.py -- reusable charts for the project. Saves figures to outputs/figures/."""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # render charts straight to a file (no popup window)
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT


def plot_demand_by_neighborhood(ranked, output_path=None):
    """Horizontal bar chart of estimated daily demand per neighborhood.

    `ranked` is the DataFrame from estimate_area_demand(). We draw the bars
    smallest-to-largest so the biggest-demand neighborhood lands at the top,
    then save the image into outputs/figures/.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "outputs" / "figures" / "demand_by_neighborhood.png"

    data = ranked.sort_values("daily_demand")  

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(data["neighborhood"], data["daily_demand"], color="#4227b8")
    ax.set_xlabel("Estimated demand  ($ / day)")
    ax.set_title("Daily demand by neighborhood (placeholder populations)")
    for spine in ("top", "right"):      
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
