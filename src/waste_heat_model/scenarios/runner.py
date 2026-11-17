"""Runs options across conservative/central/optimistic scenarios and collects KPIs
(primary energy, CO2e, CAPEX, payback, break-even). Monte Carlo extension* (Gate 1)
would sample assumption ranges here instead of three fixed scenarios.
"""

from __future__ import annotations

SCENARIOS = ("conservative", "central", "optimistic")


def run_all(options, demand_model, weather, scenarios=SCENARIOS, strict=True):
    raise NotImplementedError("Wire up once baseline and one option are verified.")
