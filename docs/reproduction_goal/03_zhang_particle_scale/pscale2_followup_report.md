# Zhang pscale=2 Follow-up Results

## Conclusion

C now has a pscale=2 pressure-window and trend-pass candidate, but D and E are not ready for 4x. Hold C for a seed recheck; for D, pressure and force-chain trend conflict under friction-only tuning; for E, pressure improved but remains below the 572 MPa lower bound.

## Size Summary

| Size | Best Emax GPa | Best Mu | Best P95 MPa | Pressure Gate | Trend | Participation Delta | D1 Delta | Decision |
|---|---:|---:|---:|---|---|---:|---:|---|
| C | 63.462 | 0.654 | 586.646 | pass | pass | 0.0650829 | -1.15928 | candidate_ready_for_seed_recheck |
| D | 57.173 | 0.770 | 634.795 | pass | review | -0.136921 | -0.16442 | hold_pressure_candidate_and_tune_trend |
| E | 87.368 | 0.693 | 543.689 | review | pass | 0.0198942 | -0.942374 | extend_pressure_without_losing_trend |

## Acceptance

| Size | Artifact | Workflow | Pressure Window | Trend | Overall |
|---|---|---|---|---|---|
| C | pass | pass | pass | pass | pass |
| D | pass | pass | pass | review | review |
| E | pass | pass | review | pass | review |

## Files

- `data/pscale2_followup_candidates.csv`
- `data/pscale2_followup_size_summary.csv`
- `data/pscale2_followup_acceptance.csv`
- `figures/pscale2_followup_p95.png`
