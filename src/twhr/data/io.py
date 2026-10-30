"""Readers for the sponsor data pack.

Layout of 'Gas Figures' (checked 30 Oct 2026): two title rows, a blank row, header on
Excel row 4 with columns Timestamp | Gas kWh | Outside Temp, hourly rows below, trailing
blank rows. Values are never printed or logged here; only shapes and validation flags.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

GAS_SHEET = "Gas Figures"
GAS_HEADER_ROW = 3  # zero-based -> Excel row 4
GAS_COLUMNS = {"Timestamp": "timestamp", "Gas kWh": "gas_kwh", "Outside Temp": "t_out_c"}


def load_gas_figures(path: str | Path) -> pd.DataFrame:
    """Hourly gas use and outside temperature, indexed by timestamp (naive local time)."""
    df = pd.read_excel(path, sheet_name=GAS_SHEET, header=GAS_HEADER_ROW,
                       usecols=list(GAS_COLUMNS), engine="openpyxl")
    missing = set(GAS_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Gas sheet missing expected columns: {sorted(missing)}")
    df = df.rename(columns=GAS_COLUMNS).dropna(how="all")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["gas_kwh"] = pd.to_numeric(df["gas_kwh"], errors="coerce").astype("float64")
    df["t_out_c"] = pd.to_numeric(df["t_out_c"], errors="coerce").astype("float64")
    return df.set_index("timestamp").sort_index()


def save_interim(df: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)
    return path
