import pandas as pd

from twhr.data.io import load_gas_figures
from twhr.data.synthetic import make_synthetic_gas, write_synthetic_xlsx
from twhr.data.validate import validate_hourly


def test_loader_matches_data_pack_layout(tmp_path):
    p = tmp_path / "pack.xlsx"
    write_synthetic_xlsx(p, periods=200)
    df = load_gas_figures(p)
    assert list(df.columns) == ["gas_kwh", "t_out_c"]
    assert len(df) == 200 and df.index.is_monotonic_increasing


def test_clean_series_passes():
    assert validate_hourly(make_synthetic_gas(periods=500)).ok


def test_detects_gap_duplicate_negative():
    df = make_synthetic_gas(periods=100)
    df = pd.concat([df.drop(df.index[10]), df.iloc[[20]]]).sort_index()
    df.iloc[30, 0] = -5
    r = validate_hourly(df)
    assert r.missing_hours == 1 and r.duplicate_timestamps == 1
    assert r.negative_counts["gas_kwh"] == 1 and not r.ok
