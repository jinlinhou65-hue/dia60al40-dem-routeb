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
