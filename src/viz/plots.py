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


def plot_tract_assignment(tracts, hoods, output_path=None, basemap=True):
    """Verification map: census tracts colored by their assigned neighborhood.

    Black neighborhood outlines are drawn on top -- if the assignment is right,
    each colored cluster of tracts sits neatly inside its outline.
    """
    import matplotlib.patches as mpatches

    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "tracts_assigned.png"

    t = tracts.to_crs(3857)
    h = hoods.to_crs(3857)

    names = sorted(t["neighborhood"].unique())
    cmap = plt.get_cmap("tab10")
    color_for = {n: cmap(i) for i, n in enumerate(names)}

    fig, ax = plt.subplots(figsize=(12, 12))
    t.plot(ax=ax, color=t["neighborhood"].map(color_for), alpha=0.6,
           edgecolor="white", linewidth=0.6)
    h.boundary.plot(ax=ax, color="black", linewidth=2)   # outlines on top to check the tracts nest inside

    if basemap:
        try:
            import contextily as cx
            cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"(basemap skipped: {e})")

    handles = [mpatches.Patch(facecolor=color_for[n], alpha=0.7, edgecolor="white", label=n)
               for n in names]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=2, fontsize=12, frameon=True, framealpha=0.95, borderpad=0.9,
              title="Tract assigned to", title_fontsize=14)

    ax.set_title("Centroid-method diagnostic — gaps show why we apportion by area", pad=14)
    ax.axis("off")
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_store_sites(points, chosen_ids, hoods, radius_m, output_path=None, basemap=True):
    """Map of MCLP-chosen store sites with their walkshed coverage circles.

    `points` are the demand/candidate corners (meters CRS) with pid + weight;
    dot size scales with demand weight so the coverage logic is visible.
    """
    import geopandas as gpd
    import numpy as np
    import matplotlib.lines as mlines
    import matplotlib.patches as mpatches

    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "store_sites.png"

    pts = points.to_crs(3857)
    hd = hoods.to_crs(3857)
    chosen = points[points["pid"].isin(chosen_ids)]
    walksheds = gpd.GeoSeries(chosen.geometry.buffer(radius_m), crs=points.crs).to_crs(3857)
    chosen = chosen.to_crs(3857)

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.scatter(pts.geometry.x, pts.geometry.y, s=np.clip(pts["weight"] / 25, 2, 70),
               color="#4a6fa5", alpha=0.45, linewidths=0, zorder=2)
    hd.boundary.plot(ax=ax, color="black", linewidth=1.2, zorder=3)
    walksheds.plot(ax=ax, facecolor="#e4572e", alpha=0.18, edgecolor="#e4572e",
                   linewidth=1.5, zorder=4)
    ax.scatter(chosen.geometry.x, chosen.geometry.y, s=260, marker="*",
               color="#c1121f", edgecolor="white", linewidth=1, zorder=5)

    if basemap:
        try:
            import contextily as cx
            cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"(basemap skipped: {e})")

    handles = [
        mlines.Line2D([], [], color="#4a6fa5", marker="o", linestyle="", alpha=0.6,
                      markersize=8, label="Demand at corners (size = catchment)"),
        mlines.Line2D([], [], color="#c1121f", marker="*", linestyle="",
                      markersize=16, label="Chosen store site"),
        mpatches.Patch(facecolor="#e4572e", alpha=0.25, edgecolor="#e4572e",
                       label=f"{radius_m} m walkshed"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              fontsize=12, frameon=True, framealpha=0.95, borderpad=0.9)
    ax.set_title(f"Optimized store placement ({len(chosen_ids)} sites, MCLP)", pad=14)
    ax.axis("off")
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_coverage_curve(curve, output_path=None):
    """Coverage vs store count, plus what each added store contributes.

    Top: total coverage %% (the benefit curve Phase 5 prices out).
    Bottom: marginal catchment per added store -- the diminishing-returns signal
    that decides where extra stores stop paying for themselves.
    """
    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "coverage_vs_p.png"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), sharex=True,
                                   height_ratios=[3, 2])

    ax1.plot(curve["p"], curve["coverage_pct"], marker="o", color=BAR_COLOR,
             linewidth=2.5, markersize=7)
    for _, r in curve.iterrows():
        ax1.annotate(f"{r['coverage_pct']:.0f}%", (r["p"], r["coverage_pct"]),
                     textcoords="offset points", xytext=(0, 10),
                     ha="center", fontsize=10)
    ax1.set_ylabel("Catchment covered (%)")
    ax1.set_ylim(top=104)
    ax1.set_title("Coverage vs. number of stores (MCLP sweep)")

    marginal = curve.dropna(subset=["marginal_catchment"])   # undefined at the first p
    ax2.bar(marginal["p"], marginal["marginal_catchment"], color="#e4572e", alpha=0.85)
    ax2.bar_label(ax2.containers[0], labels=[f"{v:,.0f}" for v in marginal["marginal_catchment"]],
                  padding=3, fontsize=10)
    ax2.set_xlabel("Number of stores  (p)")
    ax2.set_ylabel("Catchment added\nby store #p")
    ax2.set_xticks(curve["p"])

    for ax in (ax1, ax2):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_capture_sensitivity(cap, baseline, output_path=None):
    """THE verdict chart: how many stores are viable as capture_rate varies."""
    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "sensitivity_capture.png"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), sharex=True,
                                   height_ratios=[3, 2])
    x = cap["capture_rate"] * 100

    bar = cap["stores_clearing_bar"]
    bar_label = "Pre-registered bar (contribution > 0)"
    if bar.nunique() == 1:
        # the flat line is a finding, not a bug -- note it where the eye already goes
        bar_label += f"\nflat by result: all {bar.iloc[0]} stores clear it at every rate"
    ax1.step(x, bar, where="post", linewidth=2.5, color=BAR_COLOR, label=bar_label)
    ax1.step(x, cap["stores_fully_loaded_pos"], where="post", linewidth=2.5,
             color="#e4572e", label="Fully loaded (rent + hub + capex)")
    ax1.axvline(baseline * 100, color="gray", linestyle="--", linewidth=1.5)
    ax1.annotate(f"baseline {baseline * 100:.1f}%",
                 (baseline * 100, ax1.get_ylim()[1] * 0.05),
                 rotation=90, fontsize=11, color="gray", ha="right")
    ax1.set_ylabel("Viable stores (of 10)")
    ax1.set_title("The verdict vs. the star parameter: capture rate")
    ax1.legend(loc="lower right", fontsize=12)

    ax2.plot(x, cap["median_fully_loaded"], color="#e4572e", linewidth=2.5)
    ax2.axhline(0, color="black", linewidth=1)
    ax2.axvline(baseline * 100, color="gray", linestyle="--", linewidth=1.5)
    med, xs = cap["median_fully_loaded"].tolist(), x.tolist()
    for i in range(1, len(med)):
        if med[i - 1] < 0 <= med[i]:
            frac = -med[i - 1] / (med[i] - med[i - 1])
            flip = xs[i - 1] + frac * (xs[i] - xs[i - 1])
            ax2.plot([flip], [0], "o", color="#e4572e", markersize=9, zorder=5)
            ax2.annotate(f"median store flips positive at ~{flip:.1f}%",
                         (flip + 0.07, 70), fontsize=11.5, color="#e4572e")
            break
    ax2.set_xlabel("Capture rate (% of daytime catchment transacting per day)")
    ax2.set_ylabel("Median store\nfully-loaded $/day")

    for ax in (ax1, ax2):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_automation_sensitivity(hours, baseline_hours, output_path=None):
    """The automation lever: viability vs on-site staff hours, by capture scenario."""
    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "sensitivity_automation.png"

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = {c: col for c, col in zip(sorted(hours["capture_rate"].unique(), reverse=True),
                                       [BAR_COLOR, "#e4572e"])}
    for c, grp in hours.groupby("capture_rate"):
        ax.plot(grp["staff_hours"], grp["median_fully_loaded"], linewidth=2.5,
                color=colors[c], label=f"capture = {c:.1%}")
    ax.axhline(0, color="black", linewidth=1)
    ax.axvline(baseline_hours, color="gray", linestyle="--", linewidth=1.5)
    ax.annotate("automated baseline", (baseline_hours, ax.get_ylim()[0] * 0.9),
                rotation=90, fontsize=11, color="gray", ha="right", va="bottom")
    ax.axvline(32, color="gray", linestyle=":", linewidth=1.5)
    ax.annotate("fully staffed reference", (32, ax.get_ylim()[0] * 0.9),
                rotation=90, fontsize=11, color="gray", ha="right", va="bottom")
    ax.set_xlabel("On-site staff hours per store-day")
    ax.set_ylabel("Median store fully-loaded $/day")
    ax.set_title("The automation lever: labor hours vs. viability")
    ax.legend(fontsize=12)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_hub_routes(G, routes, hub_latlon, output_path=None):
    """Map of fastest delivery routes from the SoDo hub to each neighborhood.

    `routes` is a dict {neighborhood: node list} from hub_drive_times(). The
    street grid is drawn light gray as its own context (no basemap needed);
    each route gets a color, the hub a black star.
    """
    import osmnx as ox
    import matplotlib.lines as mlines

    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "hub_routes.png"

    fig, ax = ox.plot_graph(G, show=False, close=False, figsize=(12, 12),
                            bgcolor="white", node_size=0,
                            edge_color="#d9d9d9", edge_linewidth=0.4)

    cmap = plt.get_cmap("tab10")
    handles = []
    for i, (name, route) in enumerate(routes.items()):
        edges = ox.routing.route_to_gdf(G, route)
        edges.plot(ax=ax, color=cmap(i), linewidth=3, alpha=0.85, zorder=3)
        handles.append(mlines.Line2D([], [], color=cmap(i), linewidth=3, label=name))

    hub_lat, hub_lon = hub_latlon
    ax.scatter([hub_lon], [hub_lat], s=350, marker="*", color="black", zorder=5)
    handles.append(mlines.Line2D([], [], color="black", marker="*", linestyle="",
                                 markersize=16, label="SoDo production hub"))

    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=2, fontsize=12, frameon=True, framealpha=0.95, borderpad=0.9,
              title="Fastest route to", title_fontsize=14)
    ax.set_title("Fresh-delivery routes from the SoDo hub", pad=14)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
