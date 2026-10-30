"""Raw data pack -> data/interim/gas_hourly.parquet + validation report (JSON).

Usage (from repo root):
    python scripts/ingest.py "data/raw/Triangle HPC Data Center.xlsx"
    python scripts/ingest.py --synthetic        # no sponsor data needed
Prints only shapes and flags, never values, so the console output is safe to share.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from twhr.config import REPO_ROOT
from twhr.data.io import load_gas_figures, save_interim
from twhr.data.synthetic import make_synthetic_gas
from twhr.data.validate import validate_hourly


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", nargs="?", help="path to the sponsor data pack")
    ap.add_argument("--synthetic", action="store_true")
    a = ap.parse_args()
    if not a.synthetic and not a.xlsx:
        ap.error("give a path or --synthetic")

    df = make_synthetic_gas() if a.synthetic else load_gas_figures(a.xlsx)
    tag = "synthetic" if a.synthetic else "gas"
    out_dir = REPO_ROOT / ("data/synthetic" if a.synthetic else "data/interim")
    pq = save_interim(df, out_dir / f"{tag}_hourly.parquet")
    report = validate_hourly(df)
    (out_dir / f"{tag}_validation.json").write_text(json.dumps(report.to_dict(), indent=2))

    print(f"rows={report.n_rows}  span={report.start} -> {report.end}")
    print("flags:", *(report.flags or ["none"]), sep="\n  - ")
    print(f"wrote {Path(pq).relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
