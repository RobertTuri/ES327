# MATLAB / Simulink

Python owns data ingest, cleaning and the assumptions register; MATLAB/Simulink reads the
same processed files, so both sides use one source of truth.

- **Exchange format**: Parquet (`parquetread` in MATLAB R2019a+) or CSV from `data/interim/`.
  Read assumptions with `readstruct`/a YAML toolbox, or export a flat CSV from `twhr.config`.
- **Layout**: put functions in `matlab/+twhr/` (package folder), models in `matlab/models/`,
  run scripts in `matlab/scripts/`. Run `matlab/startup.m` to add paths.
- **Simulink in git**: save models as `.slx`, enable *Source Control* in the MATLAB project, and use
  *Compare* (Simulink diff) for reviews. Generated folders (`slprj/`, `*.slxc`) are gitignored.
- **Verification**: when a component exists in both languages (e.g. COP), compare outputs on the
  synthetic dataset and record agreement in `docs/decisions/`.
