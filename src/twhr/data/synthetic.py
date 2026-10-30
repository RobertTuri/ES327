"""Synthetic stand-in for the sponsor gas data.

Use this for tests, CI, demos, and any AI-assisted debugging, so real JLR data never
needs to leave approved storage. Shape and column names match `load_gas_figures`.
The numbers are invented and must never appear in the report as results.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def make_synthetic_gas(start: str = "2025-03-01", periods: int = 8760, seed: int = 0,
                       ua_kw_per_k: float = 40.0, t_base_c: float = 16.0,
                       base_load_kw: float = 60.0, boiler_eff: float = 0.85,
                       noise_frac: float = 0.10) -> pd.DataFrame:
    """Hourly gas kWh from a toy degree-hour model plus noise, with UK-ish temperatures."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=periods, freq="h")
    doy = idx.dayofyear.to_numpy()
    hod = idx.hour.to_numpy()
    t_out = (10.5 - 6.5 * np.cos(2 * np.pi * (doy - 20) / 365)
             + 3.0 * np.sin(2 * np.pi * (hod - 9) / 24)
             + rng.normal(0, 1.5, periods))
    occupied = (idx.dayofweek < 5) & (hod >= 6) & (hod < 19)
    heat_kw = ua_kw_per_k * np.clip(t_base_c - t_out, 0, None) * np.where(occupied, 1.0, 0.4)
    gas = (heat_kw + base_load_kw) / boiler_eff
    gas *= 1 + rng.normal(0, noise_frac, periods)
    return pd.DataFrame({"gas_kwh": np.clip(gas, 0, None).round(1), "t_out_c": t_out.round(1)},
                        index=pd.Index(idx, name="timestamp"))


def write_synthetic_xlsx(path, **kwargs) -> None:
    """Write synthetic data in the same sheet layout as the data pack (for loader tests)."""
    df = make_synthetic_gas(**kwargs).reset_index()
    df.columns = ["Timestamp", "Gas kWh", "Outside Temp"]
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame([["SYNTHETIC data pack"], ["Hot water system gas usage figures"]]).to_excel(
            xw, sheet_name="Gas Figures", header=False, index=False)
        df.to_excel(xw, sheet_name="Gas Figures", startrow=3, index=False)
