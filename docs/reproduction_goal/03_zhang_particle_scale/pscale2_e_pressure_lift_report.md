# Zhang pscale=2 E Pressure-Lift Recheck Results

## Conclusion

Reject Emax=96.417 GPa as a robust E candidate and diagnose the pressure/trend tradeoff before another run.

## Ensemble

| Mean P95 MPa | CV | Trend pass | Pressure window | Pass + window | Seed-2 delta MPa |
|---:|---:|---:|---:|---:|---:|
| 644.331 | 0.0700 | 4/5 | 3/5 | 3/5 | +82.918 |

A proportional per-seed screening approximation gives a common Emax interval of `94.132` to `87.598 GPa`. Because the lower bound exceeds the upper bound, another Emax-only run is not expected to place all five seeds inside the pressure window. This is a diagnostic inference, not a substitute for DEM.

## Seeds

| Seed | P95 MPa | Pressure | Trend | Both | Participation delta | D1 delta |
|---:|---:|---|---|---|---:|---:|
| 0 | 702.232 | review | review | review | -0.0619 | -1.3148 |
| 1 | 632.310 | pass | pass | pass | 0.1457 | -0.9612 |
| 2 | 626.608 | pass | pass | pass | 0.0071 | -0.9424 |
| 3 | 585.884 | pass | pass | pass | 0.4458 | -1.6401 |
| 4 | 674.619 | review | pass | review | 0.1003 | -0.9451 |

## Acceptance

| Solver | Mean pressure | Trend | Combined | Seed-2 pressure | Seed-2 trend | Decision |
|---|---|---|---|---|---|---|
| pass | review | pass | pass | pass | pass | e_pressure_lift_not_sufficient |
