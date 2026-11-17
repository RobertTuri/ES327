"""Waste-heat recovery options, one class per architecture you shortlist.

Examples to evaluate (from the lit review, not yet decided):
  * water-source heat pump lifting ~30-35 degC CHW return to 70 degC LTHW flow
  * lower LTHW temperature (needs emitter check) to raise COP
  * thermal storage buffer; free cooling in cold weather (JLR ask #3)
Each must satisfy the JLR priority-1 constraint: the HPC stays cooled every hour.
"""

from __future__ import annotations


class HeatPumpToLTHW:
    name = "hp_to_lthw"

    def simulate(self, demand, weather, params):
        raise NotImplementedError("Define the energy balance and control logic first.")
