"""System interfaces: the contract between subsystems (your SE architecture in code).

Inputs/outputs are fixed here so baseline, recovery options, ML surrogate and the
scenario runner can be developed and verified independently. The implementations are
yours: each stub raises NotImplementedError until you decide the method (log it in
docs/decisions/).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd


@dataclass
class DemandResult:
    """Hourly host-building heat demand (kW), indexed like the input weather."""
    heat_demand_kw: pd.Series


@dataclass
class OptionResult:
    """Hourly flows for one waste-heat option. All kW, same index as demand."""
    heat_supplied_kw: pd.Series      # to LTHW from recovered heat
    residual_gas_kw: pd.Series       # boiler top-up, as gas input
    elec_kw: pd.Series               # heat pumps, pumps, fans
    rejected_heat_kw: pd.Series      # DC heat not used (dry coolers etc.)
    capex_gbp: float


class DemandModel(Protocol):
    def fit(self, weather: pd.DataFrame, gas_kwh: pd.Series) -> DemandModel: ...
    def predict(self, weather: pd.DataFrame) -> DemandResult: ...


class RecoveryOption(Protocol):
    name: str
    def simulate(self, demand: DemandResult, weather: pd.DataFrame,
                 params: dict) -> OptionResult: ...
