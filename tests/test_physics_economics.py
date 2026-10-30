import math

import numpy as np
import pytest

from twhr.baseline.model import cv_rmse, nmbe
from twhr.economics.metrics import breakeven_capex, discounted_payback, npv, simple_payback
from twhr.physics.thermo import (
    cop_carnot_heating,
    cop_heating,
    fabric_vent_loss_kw,
    water_heat_flow_kw,
)


def test_loss_is_zero_when_warm_outside():
    assert fabric_vent_loss_kw(10, 21, np.array([25, 11]))[0] == 0
    assert fabric_vent_loss_kw(10, 21, 11) == pytest.approx(100)


def test_carnot_cop_hand_calc():
    # 70 degC sink, 30 degC source: 343.15 / 40
    assert cop_carnot_heating(70, 30) == pytest.approx(343.15 / 40)
    assert cop_heating(70, 30, 0.5, approach_k=0) == pytest.approx(0.5 * 343.15 / 40)
    with pytest.raises(ValueError):
        cop_carnot_heating(20, 30)


def test_water_heat_flow():
    assert water_heat_flow_kw(10, 70, 60) == pytest.approx(418)


def test_economics_hand_calcs():
    assert npv(0.0, [-100, 50, 50]) == pytest.approx(0)
    assert simple_payback(100, 25) == 4
    assert math.isinf(simple_payback(100, 0))
    assert discounted_payback(0.0, [-100, 40, 40, 40]) == pytest.approx(2.5)
    capex = breakeven_capex(0.07, 20, 10_000)
    assert npv(0.07, [-capex] + [10_000] * 20) == pytest.approx(0, abs=1e-6)


def test_calibration_metrics():
    m = np.array([10.0, 20, 30])
    assert cv_rmse(m, m) == 0 and nmbe(m, m) == 0
