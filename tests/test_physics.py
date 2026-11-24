# Verifying emitters for now

import numpy as np
import pytest

from waste_heat_model.config import load_config, values
from waste_heat_model.physics.emitters import (
    CP_AIR_KJ_PER_KG_K,
    Emitter,
    EmitterType,
    NominalConditions,
    emitter_output_kw,
    load_emitters,
)
from waste_heat_model.physics.thermo import CP_WATER_KJ_PER_KG_K


# TBD: bring out of legacy/ from the folders and test imports work
"""
from waste_heat_model.physics.thermo import (
    cop_carnot_heating,
    cop_heating,
    fabric_vent_loss_kw,
    water_heat_flow_kw,
)
"""


# --- Emitters from config ---------------------------------------------------------------------

# What base.yaml should give right now. Adding or removing a type means changing this on purpose.
CONFIGURED_TYPES = {
    EmitterType.RADIATOR,
    EmitterType.FAN_COIL,
    EmitterType.UNDERFLOOR,
    EmitterType.AHU_COIL,
}
SCENARIOS = [None, "conservative", "central", "optimistic"]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_configured_emitter_loads(scenario):
    emitters = load_emitters(load_config(scenario))
    assert set(emitters) == CONFIGURED_TYPES
    assert all(isinstance(e, Emitter) for e in emitters.values())


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_rated_output_at_rating_point(scenario):
    # Hand check: at its own rating point, every emitter must give back q_nom_kw
    # (times the fan-speed factor, which is 1.0 for everything except a slowed fan coil).
    # For the AHU this holds because eps is derived from that same rating point.
    for e in load_emitters(load_config(scenario)).values():
        n = e.nominal
        q_kw = emitter_output_kw(e, n.t_flow_nom_c, n.t_return_nom_c, n.t_room_nom_c)
        assert q_kw == pytest.approx(e.fan_speed_factor * e.q_nom_kw)


# --- Worked examples (same numbers as the hand calcs in chat / the design note) -------------


def _central():
    return load_emitters(load_config("central"))


def test_worked_example_radiator_at_45_35():
    # 200 kW radiators rated 75/65/20, run at 45/35 with the room at 20:
    #   dT_lm     = 10 / ln(25/15) = 19.58 K   (rating point: 10 / ln(55/45) = 49.83 K)
    #   Q         = 200 * (19.58 / 49.83)^1.3 = 59.4 kW  -> under 30 % of rated
    rad = _central()[EmitterType.RADIATOR]
    assert emitter_output_kw(rad, 45, 35, 20) == pytest.approx(59.4, abs=0.1)


def test_worked_example_ahu_effectiveness_from_rating_point():
    # 150 kW coil, 5 kg/s of air, rated with 70 degC water and 10 degC air-on:
    #   eps = 150 / (5 * 1.005 * (70 - 10)) = 150 / 301.5 = 0.4975
    ahu = _central()[EmitterType.AHU_COIL]
    assert ahu.effectiveness == pytest.approx(0.4975, abs=1e-4)


def test_worked_example_ahu_at_45_flow():
    # The model is linear in (T_flow - T_air_on), so at 45 degC flow, 10 degC air-on:
    #   Q = 150 * (45 - 10) / (70 - 10) = 87.5 kW
    ahu = _central()[EmitterType.AHU_COIL]
    assert emitter_output_kw(ahu, 45, None, 10) == pytest.approx(87.5)


def test_code_constants_match_register():
    # The YAML is the register; the code constants must never drift away from it.
    v = values(load_config())
    assert v["properties.cp_water_kj_per_kg_k"] == CP_WATER_KJ_PER_KG_K
    assert v["properties.cp_air_kj_per_kg_k"] == CP_AIR_KJ_PER_KG_K

