"""Hydronic emitter models: steady state, hourly. Design notes in docs/emitters_design.md.

Units: degC, kW, kg/s, cp in kJ/(kg K), same as thermo.py.

The point of this module is to answer one question for the recovery options: how cool can
the heating flow run and still meet the building's load? Each emitter type gets its own
model, picked by a match on its type.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from waste_heat_model.physics.thermo import CP_WATER_KJ_PER_KG_K, water_heat_flow_kw

# If flow and return are closer than this, the log-mean formula turns into 0/0,
# so we fall back to its limit instead.
_EQUAL_TOL_K = 1e-9

# Specific heat of air. Textbook value, still to check against my property source.
CP_AIR_KJ_PER_KG_K = 1.005


class EmitterType(Enum):
    """The emitter kinds I expect in the Triangle. Strings match the YAML config keys."""

    RADIATOR = "radiator"
    FAN_COIL = "fan_coil"
    AHU_COIL = "ahu_coil"
    UNDERFLOOR = "underfloor"


@dataclass(frozen=True)
class NominalConditions:
    """The rating point a manufacturer quotes q_nom_kw at (e.g. 75/65/20 for radiators)."""

    t_flow_nom_c: float
    t_return_nom_c: float
    t_room_nom_c: float

    def __post_init__(self) -> None:
        # A rating point only makes sense if the water cools down towards the room.
        if not self.t_flow_nom_c > self.t_return_nom_c > self.t_room_nom_c:
            raise ValueError("Nominal conditions need t_flow > t_return > t_room.")

    @property
    def dt_lm_nom_k(self) -> float:
        """Log-mean excess temperature at the rating point, K."""
        return float(lmtd_excess(self.t_flow_nom_c, self.t_return_nom_c, self.t_room_nom_c))


@dataclass(frozen=True)
class Emitter:
    """All emitters of one type, lumped together (e.g. every radiator in the building)."""

    name: str
    kind: EmitterType
    q_nom_kw: float  # total rated output at the nominal conditions
    n_exp: float  # emitter exponent: ~1.3 radiators, ~1.0 fan coils (both to verify)
    nominal: NominalConditions
    # The next three only matter for some types, so they default to "not used".
    fan_speed_factor: float = 1.0  # fan coils: output relative to rated fan speed
    effectiveness: float | None = None  # AHU coils: fraction of the maximum heat transfer
    m_dot_air_kg_s: float | None = None  # AHU coils: air mass flow through the coil


# --- Equations ----------------------------------------------------------------------------


def lmtd_excess(t_flow_c, t_return_c, t_room_c):
    """Equation 1: dT_lm = (T_f - T_r) / ln((T_f - T_i) / (T_r - T_i)).

    The water cools along the emitter, so its excess over the room shrinks exponentially.
    The log-mean is the average that gets that right. Only valid for T_f >= T_r > T_i;
    anything else comes back as NaN rather than crashing the whole year's run.
    """
    t_f, t_r, t_i = np.broadcast_arrays(
        *(np.asarray(x, dtype=float) for x in (t_flow_c, t_return_c, t_room_c))
    )
    dt_in_k = t_f - t_i  # excess at the inlet
    dt_out_k = t_r - t_i  # excess at the outlet
    dt_lm_k = np.full(dt_in_k.shape, np.nan)

    valid = (dt_in_k > 0) & (dt_out_k > 0) & (t_f >= t_r)
    equal = valid & (np.abs(dt_in_k - dt_out_k) < _EQUAL_TOL_K)
    log_case = valid & ~equal

    dt_lm_k[log_case] = (dt_in_k[log_case] - dt_out_k[log_case]) / np.log(
        dt_in_k[log_case] / dt_out_k[log_case]
    )
    dt_lm_k[equal] = dt_in_k[equal]  # limit when flow == return
    return dt_lm_k[()]  # plain number in, plain number out


def _characteristic_kw(emitter: Emitter, t_flow_c, t_return_c, t_room_c):
    """Equation 2: Q = Q_nom * (dT_lm / dT_lm_nom)^n.

    Scales the rated output away from the rating point. Used by radiators, underfloor and
    fan coils. Zero when the flow isn't warmer than the room.
    """
    t_f = np.asarray(t_flow_c, dtype=float)
    t_i = np.asarray(t_room_c, dtype=float)
    ratio = lmtd_excess(t_f, t_return_c, t_i) / emitter.nominal.dt_lm_nom_k
    q_emitter_kw = emitter.q_nom_kw * ratio**emitter.n_exp
    return np.where(t_f <= t_i, 0.0, q_emitter_kw)[()]


def _ahu_coil_kw(emitter: Emitter, t_flow_c, t_air_on_c):
    """Q = eps * m_air * cp_air * (T_flow - T_air_on).

    The most heat the air could pick up is if it warmed all the way to the water's flow
    temperature; effectiveness says what fraction of that the coil actually manages.
    Assumes the air side has the smaller heat-capacity rate. Rough first pass, to be
    replaced by a proper eps-NTU model if AHUs turn out to carry a big share of the load.
    """
    if emitter.effectiveness is None or emitter.m_dot_air_kg_s is None:
        raise ValueError(f"{emitter.name}: AHU coil needs effectiveness and m_dot_air_kg_s")
    dt_k = np.asarray(t_flow_c, dtype=float) - np.asarray(t_air_on_c, dtype=float)
    q_kw = emitter.effectiveness * emitter.m_dot_air_kg_s * CP_AIR_KJ_PER_KG_K * dt_k
    return np.clip(q_kw, 0.0, None)[()]  # no negative heat if the water is colder than the air


def emitter_output_kw(emitter: Emitter, t_flow_c, t_return_c, t_room_c):
    """Heat output (kW) of one emitter, with the model picked by its type.

    For AHU coils, t_room_c means the air-on temperature (after heat recovery), and
    t_return_c isn't used: the return comes out of the water-side balance instead.
    """
    match emitter.kind:
        case EmitterType.RADIATOR | EmitterType.UNDERFLOOR:
            # Warm surfaces heating still air. Same equation, different n and rating point.
            # Underfloor will also need a floor-surface temperature cap later.
            return _characteristic_kw(emitter, t_flow_c, t_return_c, t_room_c)
        case EmitterType.FAN_COIL:
            # Fan-driven, so n is close to 1 and output scales with fan speed.
            return emitter.fan_speed_factor * _characteristic_kw(
                emitter, t_flow_c, t_return_c, t_room_c
            )
        case EmitterType.AHU_COIL:
            return _ahu_coil_kw(emitter, t_flow_c, t_room_c)
        case _:
            raise ValueError(f"Unknown emitter type: {emitter.kind}")


def balance_residual_kw(
    emitter: Emitter, t_flow_c, t_return_c, t_room_c, m_dot_kg_s, cp=CP_WATER_KJ_PER_KG_K
):
    """What the emitter gives out minus what the water gives up (equation 2 minus 3).

    At the real operating point these match, so this is zero. solve_return_temp_c will
    search for the return temperature that makes it zero.
    """
    q_emitter_kw = emitter_output_kw(emitter, t_flow_c, t_return_c, t_room_c)
    q_water_kw = water_heat_flow_kw(m_dot_kg_s, t_flow_c, t_return_c, cp)
    return q_emitter_kw - q_water_kw


# --- Still to do (see design note) --------------------------------------------------------


def solve_return_temp_c(emitter: Emitter, t_flow_c, m_dot_kg_s, t_room_c):
    """Equation 4: find t_return_c where balance_residual_kw is zero (scipy brentq)."""
    raise NotImplementedError


def min_flow_temp_for_load_c(emitter: Emitter, q_required_kw, m_dot_kg_s, t_room_c):
    """Equation 5: lowest flow temperature that still meets q_required_kw."""
    raise NotImplementedError


def circuit_output(t_flow_c, t_room_c, branches):
    """Equation 6: parallel branches on one flow temperature, returns mixed by mass flow."""
    raise NotImplementedError