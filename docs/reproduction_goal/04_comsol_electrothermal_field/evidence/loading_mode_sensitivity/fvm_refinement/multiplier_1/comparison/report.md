# Stage 04 Open-FVM Refinement Diagnostic

Decision: `fvm_refinement_pass`

| Factor | Grid | Nodes | Power (W/m) | Max rise (K) | Balance error |
|---:|---:|---:|---:|---:|---:|
| 1 | 81 x 43 | 3483 | 209.7702 | 0.86135513 | 2.51e-13 |
| 2 | 161 x 85 | 13685 | 217.64196 | 0.8891168 | 1.09e-12 |
| 3 | 241 x 127 | 30607 | 219.18962 | 0.89389496 | 1.11e-12 |

- Factor-2/3 power difference: `0.709%`.
- Factor-2/3 temperature-rise difference: `0.536%`.
- Factor-3/COMSOL power difference: `0.682%`.
- Factor-3/COMSOL rise difference: `0.451%`.
- Top-1% Joule centroid distance: `6.156 um`.
- Top-1% temperature-rise centroid distance: `0.277 um`.

The original six-case loading study remains review; this report tests whether the
open-verifier discretization explains the sole cross-solver threshold miss.
