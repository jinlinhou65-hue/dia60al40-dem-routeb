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
| COMSOL 6.4 | 3316 quadratic triangular elements, 13570 DOF | Licensed main field solver |
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
particle-resolved contact resistance, mesh independence, and multi-stage thermal history
remain later requirements.
