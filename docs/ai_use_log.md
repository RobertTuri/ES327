# AI-use log

Raw material for the AI-use appendix (PR and SLDR briefs: what tool, how, where, why).
Keep it within what you agreed with your supervisor and stated in the PFS. No JLR data in AI tools.

| Date | Tool | Where in project (file/module) | What it did | How I checked it | Changed by me? |
|------|------|--------------------------------|-------------|------------------|----------------|
| 2026-10-30 | Claude | Repo scaffold: structure, config loader, data loader/validator, synthetic data, textbook formula helpers, tests, CI | Generated initial code from my spec; model choices left as stubs | Ran tests; to review line by line | |
| 2026-11-09 | Claude | `docs/emitters_design.md` (design for planned `src/twhr/physics/emitters.py`) | My prompt (combined): spec for an emitter module (characteristic Q = Q_nom·(ΔT_lm/ΔT_lm,nom)^n with a water-side balance; radiators, AHU coils, fan coils, optional underfloor; return-temperature solve, minimum flow temperature for a load, mixed-emitter circuits; placeholder config entries; hand-calculable tests), then asked to step back to a design note first: libraries and why, equations per function, clear variable names, later extensions only mentioned. Claude wrote the design note; no code adopted yet | To do: check each equation against a heat-transfer textbook and the standards listed (BS EN 442-2, BS EN 1397, BS EN 1264-2); re-derive the closed-form minimum flow temperature by hand; confirm units match `thermo.py` (kW) | |
