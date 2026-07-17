# Stage 04 Electrothermal MVP Model Specification

## Purpose

This model tests the first executable link from a real DEM contact network to continuous
electric-potential, current-density, Joule-heating, and temperature fields. It is a
homogenized mesoscale smoke model. It is not a particle-resolved electrical-contact model
and its material properties are not yet calibrated to an experiment.

## Source Contract

| Input | Required evidence |
|---|---|
| Particle state | Stage 5 DEM-FEM handoff, one consistent height, 76 particles |
| Contact network | 157 rows with `source=liggghts_pair_gran_local` |
| Contact force | Positive `normal_force`, input unit `dyne`, converted to N |
| Domain | `400 x 208.698534 um` |

The preprocessor rejects inferred contacts and unexpected force units. SHA-256 hashes of
both source CSV files are stored in `data/prepared/input_manifest.json`.

## Contact-To-Property Mapping

For contact `c`, the dimensionless weight is

```text
w_c = sqrt(F_c / median(F))
```

The spatial contact field is a Gaussian kernel sum with `ell=12 um`, normalized by its
maximum on the `81 x 43` grid:

```text
g(x,y) = sum_c w_c exp(-((x-x_c)^2 + (y-y_c)^2)/(2 ell^2)) / max_grid(sum)
```

The smoke properties are

```text
sigma(x,y) = 1e3 + (1e5 - 1e3) g(x,y) S/m
k(x,y)     = 20  + (100 - 20) g(x,y) W/(m K)
```

These ranges are numerical smoke values. They demonstrate field transfer and solver
coupling but are not claims about calibrated Al-diamond contact resistance.

## Boundary-Value Problem

```text
div(sigma grad(V)) = 0
Q = sigma |grad(V)|^2
-div(k grad(T)) = Q
```

- Bottom electrode: `V=0`, `T=293.15 K`.
- Top electrode: `V=0.1 V`, `T=293.15 K`.
- Side boundaries: electric and thermal insulation.
- COMSOL physics: Electric Currents (`ConductiveMedia`), Heat Transfer, and
  `ElectromagneticHeatSource`.

## Independent Implementations

| Implementation | Discretization | Role |
|---|---|---|
| COMSOL 6.4 | 1512/3316/8390 quadratic triangular elements | Licensed main field solver and mesh study |
| Open verifier | Structured finite volume, `81 x 43` nodes | Conservation and cross-solver check |

## Smoke Acceptance Gates

1. COMSOL summary reports success and the batch log has no Java/model error block.
2. All exported field values are finite.
3. Potential extrema equal `0` and `0.1 V`.
4. Maximum temperature rise is positive.
5. COMSOL/FVM Joule power difference is at most 5%.
6. COMSOL/FVM maximum temperature-rise difference is at most 5%.
7. Potential-field normalized RMSE is at most 5%.
8. Temperature-field normalized RMSE is at most 10%.

Passing these gates proves the software and data route. Experimental calibration,
particle-resolved contact resistance, and multi-stage thermal history remain later requirements.

## Mesh Convergence Gates

The physical inputs, interpolation grid, voltage, temperature boundaries, material fields,
and solver study are frozen. Only the free-triangle size changes:

| Level | hmax (um) | hmin (um) | Elements | DOF |
|---|---:|---:|---:|---:|
| Coarse | 12.0 | 1.5 | 1512 | 6258 |
| Medium | 8.0 | 1.0 | 3316 | 13570 |
| Fine | 5.0 | 0.625 | 8390 | 34050 |

All solves and logs must be clean, element count must increase, minimum element quality must
remain at least `0.2`, and both Joule power and maximum temperature rise must differ by at most
`1%` between the medium and fine meshes. A secondary coarse/fine gate is fixed at `3%`.

The observed medium/fine differences are `0.0277%` for Joule power and `0.0187%` for maximum
temperature rise, so the original medium mesh is sufficient for these global smoke-model outputs.
This is a discretization result, not a material or contact-resistance calibration.

## Material-Aware Contact Screening

The second model layer preserves the smoke regression but replaces the common force weight
with material-aware contact laws. The source ledger is
`data/source/material_contact_parameter_sources.csv`; executable values and their
classification are frozen in `data/source/electrothermal_parameter_set.json`.

For every direct particle pair:

```text
a = (3 F R* / (4 E*))^(1/3)
Re_clean = (rho1 + rho2) / (4 a)
Rth = (1/k1 + 1/k2) / (4 a)
```

Al-Al electrical resistance is screened at clean-contact multipliers `1/10/100`. The
Al-diamond thermal resistance additionally contains `1/(h pi a^2)` with the central
screening value `h=80 MW/(m2 K)`. Diamond is treated as undoped with a conservative
room-temperature resistivity lower bound. The elastic constants remain the Stage 03 DEM
values, so Hertz radii are mechanically consistent with that run but are not measurements.

The Gaussian continuum mapping uses one raw maximum frozen from the multiplier-10 reference.
It does not renormalize each scenario. The `100-100000 S/m` electrical and `20-100 W/(m K)`
thermal bounds remain numerical regularization values, not measured effective properties.

## Contact-Screening Gates

1. Preserve all 157 direct contacts and classify every pair by material.
2. Report the fraction with `a/min(R)>0.25`; do not silently accept Hertz small-deformation validity.
3. Test bottom-to-top connectivity after removing edges below `1e-12` of maximum conductance.
4. On the frozen `81 x 43` grid and under fixed voltage, Joule power and maximum temperature
   rise must not increase as the Al-Al resistance multiplier increases.
5. Every FVM case must satisfy electrical power balance within `1e-8`.

Passing the last two gates is named `conditional_sensitivity_pass`. It does not override a
failed particle-network percolation gate and therefore is not a calibrated electrothermal pass.

## Loading-Mode Extension

The audited Liu PDF does not define an applied-current or applied-voltage boundary for the
reproduced model. The two loading modes are therefore a project mechanism extension and are
not labeled as a paper boundary condition.

The Al-Al resistance multipliers remain `1/10/100`. The fixed-voltage family uses
`V=0.1 V`. The fixed-current family uses the multiplier-10, `0.1 V` open-solver current as
the frozen target:

```text
I_target = 325.1069953718656 A/m depth
V_case = 0.1 V * I_target / I_case_at_0.1V
```

The model remains linear in voltage for each frozen property field. This makes the fixed-current
voltage calculation exact for the discretized linear electrical problem and avoids iterative
retuning. The expected limiting trends are

```text
fixed voltage: P = V^2 / R -> decreases as R increases
fixed current: P = I^2 R   -> increases as R increases
```

All six licensed runs use the accepted medium COMSOL mesh (`hmax=8 um`, `hmin=1 um`, 3316
elements). The mesh study must not be repeated. Each case must have a successful finite summary,
a clean COMSOL log, the requested voltage, and COMSOL/FVM power, current, and maximum-rise
differences no greater than the preregistered `5%` threshold. Trends, fixed element count, and
same-scenario cross-mode COMSOL hotspot positions are additional gates.

The archived six-case decision is `review`, not pass: both multiplier-1 cases have a symmetric
COMSOL/FVM power and current difference of `5.0736553%`. All other case and global trend gates
pass. This immutable result is stored in
`evidence/loading_mode_sensitivity/comparison/loading_mode_comparison.json`.

## Open-Solver Refinement Diagnostic

After the original review, a separate preregistration froze the multiplier-1 fixed-voltage
COMSOL fields and property grid. Only the structured FVM resolution changes:

| Factor | Nodes | Grid |
|---:|---:|---:|
| 1 | 3483 | `81 x 43` |
| 2 | 13685 | `161 x 85` |
| 3 | 30607 | `241 x 127` |

The factor-2/factor-3 power and maximum-rise differences must each be at most `1%`. Factor 3
must differ from COMSOL by at most `5%` in power, current, and maximum temperature rise. To avoid
using a single boundary maximum as a fragile hotspot test, COMSOL and FVM fields are bilinearly
sampled on the common `241 x 127` grid; the weighted centroid of the top 1% Joule and temperature
values must be within `24 um` (two original kernel lengths).

All eight refinement gates pass. Factor 3 differs from COMSOL by `0.6823%` in power/current and
`0.4508%` in maximum rise; the Joule and temperature centroid distances are `6.156 um` and
`0.277 um`. This diagnoses the coarse open-verifier discretization. It does not alter the
original six-case review and does not resolve particle-network percolation or experimental
contact-resistance calibration.

## Evidence Integrity Contract

`scripts/build_electrothermal_loading_manifest.py` hashes the source inputs, preregistrations,
implementation, workflow, tests, prepared grids, six COMSOL models/logs/fields, six base FVM
cases, the preserved wrapper failure, and the three refinement levels. Verification requires:

1. six successful COMSOL summaries, logs, and `.mph` models;
2. six open loading summaries and three refinement summaries;
3. exactly the two multiplier-1 cases failing the original gate;
4. every non-case global loading gate passing;
5. `fvm_refinement_pass` while `original_loading_decision` remains `review`;
6. every recorded canonical byte count and SHA-256 matching the repository file. Text files use
   LF-normalized bytes for Windows/Linux portability; binary `.mph` and images use raw bytes.

This contract proves provenance and file integrity, not physical calibration.

## Al Native-Oxide Contact Preregistration

The archived true-3D run supplies 96 particles, 115 direct `pair/gran/local` contacts, and
50 Al-Al edges. Its graph, electrode nodes, Hertz radii, material labels, and hashes are frozen.
No DEM or COMSOL solve is part of this gate.

The source ledger is `data/source/al_oxide_contact_parameter_sources.csv`. Aluminum powder
measurements support a per-particle passivation thickness sweep of `5/6/8 nm`. Effective-film
resistivities `1e6/1e9/1e12 ohm m` are deliberately broad screening values: the endpoints are
literature discussion values for thin-film tunneling and bulk alumina, while `1e9` is only their
logarithmic midpoint. None is a compacted-powder calibration.

For archived Hertz radius `a`, the preregistered bounds are

```text
R_clean = rho_Al / (2a)
A = pi a^2
R_film = rho_f (2 d_particle) / A
R_intact = R_clean + R_film
```

The primary effective rupture hypothesis uses metallic area fraction `f_m`:

```text
G_metal = sqrt(f_m) / R_clean
G_film = (1-f_m) / R_film
R_edge = 1 / (G_metal + G_film)
```

The frozen identifiability grid is
`f_m={0,1e-12,1e-10,1e-8,1e-6,1e-4,1e-2,1}` with `d_particle=6 nm` and
`rho_f=1e6 ohm m`. It is a numerical sweep, not a rupture-probability prior.

The next implementation must solve the full Dirichlet/KCL resistor network, report equivalent
resistance separately from weighted shortest-path resistance, and verify relative KCL and power
balance errors at `1e-10`. Fixed `0.1 V` and normalized fixed `1 A` cases must show the expected
opposite power monotonicity as bridge fraction increases. Per-edge voltage divided by the two-film
thickness is compared with a `4-5e8 V/m` device-film breakdown boundary only as a diagnostic; it
must not be interpreted as a powder mechanical-rupture threshold.

The immutable preregistration is `al_oxide_contact_preregistration.md`, and the machine-readable
contract is `data/source/al_oxide_contact_preregistered_parameters.json`. Passing the future
calculation can establish only bounded network sensitivity. Experimental calibration still requires
oxide-thickness characterization and pressure-resistance-loading histories for the same powder.

## Archived-Graph Oxide-Network Result

The offline solver validates the three preregistered SHA-256 values before reading the graph. Of
50 Al-Al edges, 39 edges and 30 nodes belong to components touching both electrode sets. Remaining
one-sided components are retained in `edge_results.csv` with zero transport current; they are not
silently deleted or allowed to make the KCL matrix singular.

The clean full-network equivalent resistance is `0.0146764894 ohm`, while the weighted shortest
path is `0.0353279646 ohm`. The full network is therefore about 41.5% of the shortest-path value,
directly showing why a single path cannot represent parallel transport.

The nine complete-film scenarios span `2.807547216e9-4.492075546e15 ohm`. In the primary rupture
sweep, equivalent resistance falls from `3.369056660e9 ohm` at `f_m=0` to the clean value at
`f_m=1`; even `f_m=1e-12` gives `1.467642478e4 ohm`. This is a model sensitivity showing that tiny
metallic bridges can dominate an insulating film. It is not evidence that the archived powder has
that rupture fraction.

All 18 scenarios keep shortest path `95->41->36->27->33` and top-five Joule edge IDs
`43;36;29;34;38`. Uniform `f_m` therefore changes magnitudes but not hotspot topology. Edge-specific
rupture or sintering feedback is required before claiming hotspot migration. No edge exceeds the
`4e8 V/m` device-film diagnostic at fixed `0.1 V`; mechanical rupture remains unconstrained.

All eight preregistered gates pass. Maximum relative KCL residual is `2.132e-15`, and maximum
relative source-to-edge power error is `3.969e-15`. Fixed voltage power rises with bridge fraction;
normalized fixed-current power falls. The very large fixed-`1 A` intact-film power is only a limiting
direction check and is not an admissible experimental or thermal prediction.
