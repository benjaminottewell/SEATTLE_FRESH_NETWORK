"""plots.py -- reusable, readable charts & maps. Saves figures to outputs/figures/.

Every figure goes through set_plot_style() so the whole project shares one clean,
legible look (big fonts, white background, high resolution).
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")              # render straight to a file (no popup window)
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT

FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
BAR_COLOR = "#4227b8"


def set_plot_style():
    """Readable, consistent defaults applied to every figure in the project."""
    plt.rcParams.update({
        "figure.dpi": 130,
        "savefig.dpi": 200,            # crisp exported images
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
        "font.size": 13,
        "axes.titlesize": 19,
        "axes.titleweight": "bold",
        "axes.labelsize": 14,
    })


def plot_study_area(hoods, output_path=None, basemap=True):
    """Clean map of the study-area neighborhoods: numbered badges + a legend.

    `hoods` is the GeoDataFrame from fetch_study_neighborhoods(). Each neighborhood
    gets a small numbered marker on the map; a legend (dropped over the empty water)
    maps numbers to names. A light street basemap underneath gives context.
    """
    import matplotlib.patches as mpatches

    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "study_neighborhoods.png"

    # Web Mercator (EPSG:3857) so a street basemap lines up underneath.
    g = hoods.to_crs(3857).copy()
    # Number the neighborhoods north -> south so the badges read top-to-bottom.
    g["_y"] = g.geometry.representative_point().y
    g = g.sort_values("_y", ascending=False).reset_index(drop=True)
    g["num"] = g.index + 1
    colors = [plt.get_cmap("tab10")(i) for i in range(len(g))]

    fig, ax = plt.subplots(figsize=(12, 12))
    g.plot(ax=ax, color=colors, alpha=0.55, edgecolor="white", linewidth=2.5)

    # A small numbered badge sits inside each neighborhood.
    for _, row in g.iterrows():
        pt = row.geometry.representative_point()
        ax.annotate(str(row["num"]), (pt.x, pt.y), ha="center", va="center",
                    fontsize=15, fontweight="bold", zorder=5,
                    bbox=dict(boxstyle="circle,pad=0.3", fc="white", ec="black", lw=1.5))

    if basemap:
        try:
            import contextily as cx
            cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"(basemap skipped: {e})")

    # Legend mapping number -> name, placed over the empty water at lower-left.
    handles = [mpatches.Patch(facecolor=colors[i], alpha=0.7, edgecolor="white",
                              label=f"{row['num']}.  {row['neighborhood']}")
               for i, row in g.iterrows()]
    # Place the legend OUTSIDE the map (below it) so it never covers a neighborhood.
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=2, fontsize=12, frameon=True, framealpha=0.95, borderpad=0.9,
              labelspacing=0.6, columnspacing=1.5, title="Neighborhood", title_fontsize=14)

    ax.set_title("Study area — 7 northern-core neighborhoods", pad=14)
    ax.axis("off")
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_demand_by_neighborhood(ranked, output_path=None):
    """Readable horizontal bar chart of estimated daily demand per neighborhood."""
    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "demand_by_neighborhood.png"

    data = ranked.sort_values("daily_demand")   # ascending -> largest ends up on top

    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(data["neighborhood"], data["daily_demand"], color=BAR_COLOR)
    ax.bar_label(bars, labels=[f"${v:,.0f}" for v in data["daily_demand"]],
                 padding=6, fontsize=12)
    ax.set_xlabel("Estimated demand  ($ / day)")
    ax.set_title("Daily demand by neighborhood")
    ax.margins(x=0.13)                  # leave room for the value labels
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
