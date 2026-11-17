# Emitter module: design note

Planned home: `src/twhr/physics/emitters.py`. Nothing is coded yet; this is the plan to build against.

## What it's for

One question drives the whole module: **how cool can the heating flow run and still meet the load?**
If the emitters can run near the data-centre return temperature (~32.5 °C, register T2), the waste heat
can be used directly. If not, a heat pump has to lift it, and the COP then decides the economics.

## Libraries

Everything is already in `pyproject.toml`, so nothing new needs installing.

| Library | What we use | Why |
|---|---|---|
| `numpy` | arrays, `np.log`, `np.where`, `np.expm1` | One call handles all 8760 hours; `np.where` handles the invalid cases without loops |
| `scipy.optimize.brentq` | root-finding for the return temperature | Bracketed method: guaranteed to converge once the root is bracketed, no derivative needed |
| `dataclasses` (stdlib) | frozen `NominalConditions`, `Emitter` | Bundles a type's rating data so it can't be changed by accident mid-run |
| `pyyaml` via `twhr.config` | reads the `emitters:` block | Keeps numbers in `configs/base.yaml` with their source/status |
| `pytest` | hand-calculable tests | Each equation gets a check you can do on paper |

## Conventions

Same as `thermo.py`: units go in the variable names, heat is in **kW**, and cp is
`CP_WATER_KJ_PER_KG_K` (4.18, register D4). Functions are stateless: arrays in, arrays out (S5).
Note that the draft I pasted earlier in chat used W and J/kg·K, so switch it to kW.

## Variables

| Name | Meaning | Unit |
|---|---|---|
| `t_flow_c` | water temperature into the emitter | °C |
| `t_return_c` | water temperature out of the emitter | °C |
| `t_room_c` | air temperature the emitter heats (see the type table for coils) | °C |
| `m_dot_kg_s` | water mass flow through the emitter | kg/s |
| `q_nom_kw` | rated output at nominal conditions | kW |
| `n_exp` | emitter exponent | – |
| `dt_lm_k`, `dt_lm_nom_k` | log-mean excess temperature (actual, nominal) | K |
| `q_emitter_kw` | heat the emitter gives to the room | kW |
| `q_water_kw` | heat the water gives up | kW |
| `q_required_kw` | load to meet | kW |
| `t_flow_min_c` | lowest flow temperature that meets `q_required_kw` | °C |

Nominal conditions are one object: `NominalConditions(t_flow_nom_c, t_return_nom_c, t_room_nom_c)`.

## Equations, in build order

**1. Log-mean excess temperature**: `lmtd_excess(t_flow_c, t_return_c, t_room_c) -> dt_lm_k`

    dt_lm_k = (t_flow_c - t_return_c) / ln((t_flow_c - t_room_c) / (t_return_c - t_room_c))

This is only valid when `t_flow_c >= t_return_c > t_room_c`; otherwise return NaN. When flow equals
return, use the limit `t_flow_c - t_room_c` to avoid 0/0.
Check: 75/65/20 gives 10 / ln(55/45) = 49.83 K.

**2. Emitter characteristic**: `emitter_output(...) -> q_emitter_kw`

    q_emitter_kw = q_nom_kw * (dt_lm_k / dt_lm_nom_k) ** n_exp

Returns 0 when `t_flow_c <= t_room_c`. Check: at nominal conditions it returns exactly `q_nom_kw`.

**3. Water-side balance**

    q_water_kw = m_dot_kg_s * cp * (t_flow_c - t_return_c)

**4. Operating point**: `solve_return_temp(...) -> t_return_c`

Set `q_emitter_kw = q_water_kw` and solve for `t_return_c` in (`t_room_c`, `t_flow_c`]. The emitter side
rises with `t_return_c` and the water side falls, so there is exactly one root; `brentq` finds it.
Checks: at the nominal flow it recovers 65 °C, and for `n_exp = 1` it matches the closed form
`t_return = t_room + (t_flow - t_room) * exp(-UA / (m_dot * cp))`.

**5. Minimum flow temperature for a load**: `min_flow_temp_for_load(...) -> t_flow_min_c`

Once the load is fixed, both equations can be rearranged directly, so no solver is needed:

    dt_water_k   = q_required_kw / (m_dot_kg_s * cp)                 # flow-return drop
    dt_lm_req_k  = dt_lm_nom_k * (q_required_kw / q_nom_kw) ** (1 / n_exp)
    t_flow_min_c = t_room_c + dt_water_k / (1 - exp(-dt_water_k / dt_lm_req_k))

(The last line comes from substituting `t_return = t_flow - dt_water_k` into equation 1 and solving
for `t_flow - t_room`.) Check: at full load and nominal flow it gives 75 °C; and if you feed the result
back through equation 4, you get the load back.

**6. Circuit of mixed emitters**: `circuit_output(t_flow_c, t_room_c, branches) -> totals`

Each branch (one emitter type plus its own `m_dot_kg_s`) is in parallel on the same `t_flow_c`:

    q_circuit_kw      = sum(q_water_kw_i)
    t_return_mixed_c  = sum(m_dot_i * t_return_i) / sum(m_dot_i)

Mixing assumption: adiabatic, constant cp, no pipe losses or bypass. The flow split is given as an
input, not solved hydraulically.

## Emitter types

All values are placeholders until checked. Typical exponents are **to verify**, not citations.

| Type | What `t_room_c` means | Nominal conditions | `n_exp` (typical, verify) | Where to check |
|---|---|---|---|---|
| Radiator | room air | 75/65/20 under EN 442; older units may be BS 3528 (ΔT60) | ~1.3 | BS EN 442-2, installed models' datasheets |
| Fan coil | room/return air | manufacturer rating, at a stated fan speed | ~1.0 | BS EN 1397, manufacturer heating curves |
| AHU heating coil | **air-on** temperature (after heat recovery) | coil schedule | ~1.0, rough | AHU coil selection printouts |
| Underfloor (optional) | room air | design flow/return from M&E drawings | ~1.0–1.1 | BS EN 1264-2 |

## Later extensions (not in v1, just noting)

- **AHU coils → ε-NTU crossflow heat-exchanger model.** The characteristic equation is a fit for natural
  convection and is only a rough approximation for coils. This matters if AHUs carry a big share of the load.
- **Variable flow / TRVs → valve characteristic.** v1 assumes constant flow (matches the "CT" circuits, D9).
- **Hydraulic flow split → pressure-drop network (Δp = k·V̇²).** v1 takes the split between branches as given.
- **Pipe heat losses → `UA_pipe * (t_mean_c - t_ambient_c)`** between the plant room and the emitters.
- **FCU fan speed → `q_nom_kw` scaled per speed step**, using manufacturer data.
- Transients and thermal mass stay out of scope (S3).

## Tests to write alongside each step

The hand checks listed under each equation, plus: output falls monotonically as `t_flow_c` drops; zero
output when `t_flow_c <= t_room_c`; the solved return satisfies both equations to 1e-6; and the
circuit's total heat equals `sum(m_dot) * cp * (t_flow - t_return_mixed)`.
