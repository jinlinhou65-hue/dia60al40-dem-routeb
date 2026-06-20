# Zhang pscale=2 Recalibration Results

## Conclusion

Do not move to 4x yet. C is close but below the pressure window, D has a pressure-window candidate but needs participation tuning, and E remains far below the pressure window. Continue pscale=2 calibration with separate C/D/E actions.

## Size Summary

| Size | Best Emax GPa | Best P95 MPa | Pressure Gate | Trend | Participation Delta | Decision |
|---|---:|---:|---|---|---:|---|
| C | 61.962 | 567.207 | review | pass | 0.052353 | extend_endpoint_modulus_or_loading_path |
| D | 57.173 | 634.795 | pass | review | -0.136921 | hold_pressure_candidate_and_tune_participation |
| E | 63.559 | 480.140 | review | review | -0.0619864 | extend_endpoint_modulus_or_loading_path |

## Acceptance

| Size | Artifact | Workflow | Pressure Window | Trend | Overall |
|---|---|---|---|---|---|
| C | pass | pass | review | pass | review |
| D | pass | pass | pass | review | review |
| E | pass | pass | review | review | review |

## Files

- `data/pscale2_recalibration_candidates.csv`
- `data/pscale2_recalibration_size_summary.csv`
- `data/pscale2_recalibration_acceptance.csv`
- `figures/pscale2_recalibration_p95.png`
