# Verifying emitters for now

import numpy as np
import pytest

from waste_heat_model.physics.emitters import (
    Emitter,
    EmitterType,
    NominalConditions,
    emitter_output_kw,
)


# TBD: bring out of legacy/ from the folders and test imports work
"""
from waste_heat_model.physics.thermo import (
    cop_carnot_heating,
    cop_heating,
    fabric_vent_loss_kw,
    water_heat_flow_kw,
)
"""
