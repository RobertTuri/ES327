"""Data-quality checks for an hourly time series. Returns a report; never alters the data.

Cleaning decisions (drop, interpolate, cap) are yours to make and record in
docs/data_register.md — this module only tells you what is there.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd


@dataclass
class ValidationReport:
    n_rows: int
    start: str
    end: str
    duplicate_timestamps: int
    missing_hours: int
    nan_counts: dict[str, int]
    negative_counts: dict[str, int]
    non_hourly_steps: int
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def ok(self) -> bool:
        return not self.flags


def validate_hourly(df: pd.DataFrame, nonneg_cols: tuple[str, ...] = ("gas_kwh",),
                    t_range: tuple[float, float] = (-25.0, 45.0)) -> ValidationReport:
    idx = df.index
    dupes = int(idx.duplicated().sum())
    expected = pd.date_range(idx.min().floor("h"), idx.max().ceil("h"), freq="h")
    missing = int(len(expected.difference(idx.unique())))
    steps = idx.to_series().diff().dropna()
    non_hourly = int((steps != pd.Timedelta(hours=1)).sum())
    nans = {c: int(df[c].isna().sum()) for c in df.columns}
    negs = {c: int((df[c] < 0).sum()) for c in nonneg_cols if c in df}

    flags: list[str] = []
    if dupes:
        flags.append(f"{dupes} duplicate timestamps (check autumn DST change)")
    if missing:
        flags.append(f"{missing} missing hours (check spring DST change / logger gaps)")
    if any(nans.values()):
        flags.append(f"NaNs present: {nans}")
    if any(negs.values()):
        flags.append(f"negative values: {negs}")
    if "t_out_c" in df:
        lo, hi = t_range
        n_out = int(((df["t_out_c"] < lo) | (df["t_out_c"] > hi)).sum())
        if n_out:
            flags.append(f"{n_out} outside temps outside {t_range} degC")
    return ValidationReport(len(df), str(idx.min()), str(idx.max()), dupes, missing,
                            nans, negs, non_hourly, flags)
