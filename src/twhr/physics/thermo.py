"""Textbook building blocks. Each function states its equation so you can cite a source for it.

These are deliberately simple, transparent forms. Which ones you use, and how you calibrate
them, is a modelling decision for you to justify in the report (record it in docs/decisions/).
"""

from __future__ import annotations

import numpy as np

CP_WATER_KJ_PER_KG_K = 4.18  # verify against your chosen property source


def fabric_vent_loss_kw(ua_kw_per_k, t_in_c, t_out_c):
    """Steady-state loss  Q = UA * (T_in - T_out), clipped at zero (no heating demand when warm).

    UA lumps fabric (sum U*A) and ventilation (rho*cp*V*ACH/3600) conductances, in kW/K.
    """
    return np.clip(np.asarray(ua_kw_per_k) * (np.asarray(t_in_c) - np.asarray(t_out_c)), 0, None)


def degree_hours(t_out_c, t_base_c):
    """Heating degree-hours per step: max(T_base - T_out, 0)."""
    return np.clip(t_base_c - np.asarray(t_out_c), 0, None)


def heat_from_gas_kw(gas_kw, boiler_efficiency):
    """Useful heat delivered = gas input * boiler efficiency."""
    return np.asarray(gas_kw) * boiler_efficiency


def water_heat_flow_kw(m_dot_kg_s, t_hot_c, t_cold_c, cp=CP_WATER_KJ_PER_KG_K):
    """Q = m_dot * cp * dT  (kW, with cp in kJ/kg/K)."""
    return m_dot_kg_s * cp * (np.asarray(t_hot_c) - np.asarray(t_cold_c))


def cop_carnot_heating(t_sink_c, t_source_c):
    """Ideal heating COP = T_sink / (T_sink - T_source), temperatures converted to kelvin."""
    t_h = np.asarray(t_sink_c) + 273.15
    t_c = np.asarray(t_source_c) + 273.15
    if np.any(t_h <= t_c):
        raise ValueError("Sink must be hotter than source for a heat pump.")
    return t_h / (t_h - t_c)


def cop_heating(t_sink_c, t_source_c, exergetic_efficiency, approach_k=0.0):
    """Real COP approximated as  eta_ex * COP_carnot  with approach temperatures on both HXs.

    eta_ex and approach_k are assumptions to source from literature / manufacturer data.
    """
    return exergetic_efficiency * cop_carnot_heating(np.asarray(t_sink_c) + approach_k,
                                                     np.asarray(t_source_c) - approach_k)
