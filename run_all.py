"""run_all.py -- reproduce the entire feasibility model, end to end.

Runs every phase in dependency order. First run on a fresh clone pulls external
data (needs CENSUS_API_KEY in .env -- see .env.example); later runs use the
data/raw/ caches and take a few minutes, mostly MILP/VRP solver time.

    python run_all.py
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PIPELINE = [
    ("Phase 1  demand data (census pulls + tract apportionment)", "src/geo/assign.py"),
    ("Phase 1  demand estimates + chart",                         "src/demand/estimate.py"),
    ("Phase 2  road network + hub drive-times",                   "src/geo/network.py"),
    ("Phase 3  store siting (MCLP) + site map",                   "src/optimize/mclp.py"),
    ("Phase 3  coverage-vs-p sweep",                              "src/optimize/sweep_p.py"),
    ("Phase 4  delivery routing (VRPTW) + cadence cost",          "src/optimize/routing.py"),
    ("Phase 5  per-store economics vs the pre-registered bar",    "src/econ/economics.py"),
    ("Phase 5  sensitivity sweeps (the verdict charts)",          "src/econ/sensitivity.py"),
    ("Phase 5  stress case (joint pessimism)",                    "src/econ/stress.py"),
]

if __name__ == "__main__":
    t0 = time.time()
    for label, script in PIPELINE:
        print(f"\n{'=' * 72}\n{label}\n{'=' * 72}")
        result = subprocess.run([sys.executable, "-u", str(ROOT / script)])
        if result.returncode != 0:
            sys.exit(f"\nFAILED at {script} (exit {result.returncode})")
    print(f"\n{'=' * 72}\nPipeline complete in {(time.time() - t0) / 60:.1f} min. "
          f"Figures -> outputs/figures/, tables -> outputs/tables/")
