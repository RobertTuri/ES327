# ES327: Data-centre waste-heat reuse at the Triangle

Techno-economic model for reusing ~700 kW of HPC data-centre heat in a host building's LTHW
system. BEng Systems Engineering individual project, University of Warwick, sponsored by JLR.

> **Sponsor data never goes in git.** Put JLR files in `data/raw/` (gitignored). Tests and CI
> use synthetic data only. Check `docs/data_register.md` for permitted use.

## Layout

```
configs/            assumptions register (value, unit, source, status) + scenario overrides
data/raw|interim/   local only, gitignored
data/synthetic/     safe stand-in data
docs/               requirements traceability, decision records, data register, AI-use log
matlab/             MATLAB functions and Simulink models (read the same processed data)
scripts/            entry points (ingest, ...)
src/twhr/
  data/             loader, validation, synthetic generator
  physics/          textbook heat-transfer / heat-pump relations
  economics/        NPV, payback, break-even
  baseline/         calibrated demand model (stub) + calibration metrics
  recovery/         waste-heat options (stubs)
  scenarios/        scenario / Monte Carlo runner (stub)
  ml/               ML system (undecided; see README there)
  interfaces.py     subsystem contracts
tests/              pytest, hand-calculation checks
```

## Setup (Windows, PowerShell)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
python scripts/ingest.py --synthetic
python scripts/ingest.py "data/raw/Triangle HPC Data Center.xlsx"
```

## Working rules

- Every number in `configs/base.yaml` carries a source; `load_config(strict=True)` refuses to
  run while any `placeholder` remains, so made-up values can't reach reported results.
- Significant modelling choices get a record in `docs/decisions/`, which doubles as SLDR evidence.
- Notebooks for exploration only; anything reused moves into `src/twhr/`.
