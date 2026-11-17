"""Baseline (calibrated) host-building heat-demand model. Stage 3 milestone: validated 18 Dec.

Your decisions to make and justify before implementing:
  * model form (energy signature / degree-hour regression, RC network, ...)
  * calibration target and split (train/test by time, not shuffled)
  * acceptance criteria. ASHRAE Guideline 14 hourly CV(RMSE)/NMBE limits are commonly used;
    verify the current thresholds from the guideline itself before quoting them.
"""

from __future__ import annotations

import numpy as np


def cv_rmse(measured, predicted) -> float:
    m, p = np.asarray(measured, float), np.asarray(predicted, float)
    return float(np.sqrt(np.mean((m - p) ** 2)) / np.mean(m))


def nmbe(measured, predicted) -> float:
    m, p = np.asarray(measured, float), np.asarray(predicted, float)
    return float(np.sum(m - p) / (len(m) * np.mean(m)))


class BaselineDemandModel:
    def fit(self, weather, gas_kwh):
        raise NotImplementedError("Choose and record the baseline model form first.")

    def predict(self, weather):
        raise NotImplementedError
