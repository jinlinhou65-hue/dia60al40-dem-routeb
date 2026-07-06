# Stage 04 Electrothermal MVP Smoke Report

Decision: `smoke_pass`

| Metric | COMSOL 6.4 | Open FVM | Relative difference |
|---|---:|---:|---:|
| Joule power (W/m depth) | 396.328061 | 391.593371 | 1.202% |
| Maximum temperature rise (K) | 0.639814 | 0.636193 | 0.568% |

- Potential field normalized RMSE: `0.002930`.
- Temperature field normalized RMSE: `0.007652`.
- COMSOL exported field nodes: `1735`.
- All gates require finite fields, correct voltage limits, a clean COMSOL log, and cross-solver agreement.

## Boundary

This proves a reproducible DEM-contact-to-electrothermal smoke route. It does not validate experimental conductivity, contact resistance, or particle-resolved fields.
