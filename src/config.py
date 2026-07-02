"""
config.py -- the single doorway between assumptions.yaml and our code.

Every tunable number in this project lives in assumptions.yaml, NOT in code.
This module reads that file and hands the numbers to whatever code asks for
them. Import it anywhere:

    from src.config import load_assumptions, get_value
    a = load_assumptions()
    rate = get_value(a, "demand", "capture_rate")   # -> 0.02
"""

from pathlib import Path
import os
import yaml

# Resolve paths from the repo root so imports work from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSUMPTIONS_PATH = PROJECT_ROOT / "assumptions.yaml"


def load_assumptions(path=ASSUMPTIONS_PATH):
    """Read assumptions.yaml into a nested dict mirroring the file's structure."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_value(assumptions, *keys):
    """Dig down through the given keys and return that parameter's 'value' field.

    Each parameter in the YAML looks like:
        capture_rate:
          value: 0.02
          range: [0.005, 0.05]
          source: assumed
    So get_value(a, "demand", "capture_rate") walks to that block and returns 0.02
    """
    node = assumptions
    for key in keys:
        node = node[key]
    return node["value"]


def get_range(assumptions, *keys):
    """Like get_value, but returns the parameter's swept 'range' field [lo, hi]."""
    node = assumptions
    for key in keys:
        node = node[key]
    return node["range"]


def get_census_key():
    """Return the Census API key, or None if it isn't configured.

    Checks the CENSUS_API_KEY environment variable first, then a local .env
    file in the project root. The .env file is git-ignored so the key never
    enters version control.
    """
    key = os.environ.get("CENSUS_API_KEY")
    if key:
        return key.strip()

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("CENSUS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


if __name__ == "__main__":
    a = load_assumptions()
    print("Loaded assumptions.yaml OK. A few values:")
    print("  capture_rate     =", get_value(a, "demand", "capture_rate"))
    print("  avg_ticket       =", get_value(a, "demand", "avg_ticket"))
    print("  num_nodes_p      =", get_value(a, "facility_location", "num_nodes_p"))
    print("  labor_wage/hour  =", get_value(a, "economics", "labor_wage_per_hour"))
    print("  census key       =", "FOUND" if get_census_key() else "not set up yet")
