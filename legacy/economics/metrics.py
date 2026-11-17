"""Investment metrics. Conventions: year-0 CAPEX is negative, annual savings positive.

Check these conventions against the finance text you cite; payback definitions vary.
"""

from __future__ import annotations

import numpy as np


def npv(rate: float, cashflows) -> float:
    """NPV = sum_t CF_t / (1+r)^t, t starting at 0."""
    cf = np.asarray(cashflows, dtype=float)
    return float(np.sum(cf / (1 + rate) ** np.arange(len(cf))))


def simple_payback(capex: float, annual_saving: float) -> float:
    """Years to recover CAPEX from a constant undiscounted saving (inf if never)."""
    return float("inf") if annual_saving <= 0 else capex / annual_saving


def discounted_payback(rate: float, cashflows) -> float:
    """First (interpolated) year at which cumulative discounted cashflow turns non-negative."""
    cf = np.asarray(cashflows, dtype=float)
    cum = np.cumsum(cf / (1 + rate) ** np.arange(len(cf)))
    hit = np.nonzero(cum >= 0)[0]
    if len(hit) == 0:
        return float("inf")
    i = int(hit[0])
    if i == 0:
        return 0.0
    return float(i - 1 + (-cum[i - 1]) / (cum[i] - cum[i - 1]))


def annuity_factor(rate: float, years: int) -> float:
    return years if rate == 0 else (1 - (1 + rate) ** -years) / rate


def breakeven_capex(rate: float, years: int, annual_saving: float) -> float:
    """Max CAPEX at which NPV = 0 for a constant saving: saving * annuity factor."""
    return annual_saving * annuity_factor(rate, years)
