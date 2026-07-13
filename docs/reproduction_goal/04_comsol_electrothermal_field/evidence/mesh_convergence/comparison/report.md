# Stage 04 COMSOL Mesh Convergence Report

Decision: `mesh_pass`

| Level | hmax (um) | hmin (um) | Elements | DOF | Min quality | Joule power (W/m) | Max rise (K) |
|---|---:|---:|---:|---:|---:|---:|---:|
| coarse | 12.000 | 1.500 | 1512 | 6258 | 0.7193 | 396.307677 | 0.640089 |
| medium | 8.000 | 1.000 | 3316 | 13570 | 0.6652 | 396.328061 | 0.639814 |
| fine | 5.000 | 0.625 | 8390 | 34050 | 0.6694 | 396.218160 | 0.639695 |

- Medium/fine Joule-power difference: `0.028%`.
- Medium/fine maximum-rise difference: `0.019%`.
- Coarse/fine Joule-power difference: `0.023%`.
- Coarse/fine maximum-rise difference: `0.062%`.

## Boundary

Mesh convergence is evaluated for the fixed homogenized smoke model only; it does not calibrate contact resistance or material properties.
