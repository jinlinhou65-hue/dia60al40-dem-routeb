# Zhang pscale=2 C Seed Recheck Results

## Conclusion

C is not seed-robust: 1/5 seeds both pass trend and fall inside the Zhang pressure window, 1/5 are in the pressure window, and 4/5 pass trend. Raise pressure or adjust loading/contact law while preserving the trend gate before moving to 4x.

## Seed Summary

| Run | Seeds | Pass | In Pressure Window | Pass And Window | P95 Mean MPa | P95 Min | P95 Max | CV | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 27898770533 | 5 | 4 | 1 | 1 | 524.619 | 493.878 | 586.646 | 0.0804 | c_candidate_not_seed_robust |

## Seed Rows

| Seed | P95 MPa | Pressure Gate | Trend | Participation Delta | D1 Delta | Diagnosis |
|---:|---:|---|---|---:|---:|---|
| 0 | 493.878 | review | pass | 0.0183545 | -0.525466 | candidate_pass |
| 1 | 496.226 | review | pass | 0.090727 | -1.35863 | candidate_pass |
| 2 | 586.646 | pass | pass | 0.0650829 | -1.15928 | candidate_pass |
| 3 | 550.731 | review | review | -0.0016301 | -0.957276 | needs_participation_increase |
| 4 | 495.614 | review | pass | 0.311607 | -0.505916 | candidate_pass |

## Acceptance

| Size | Artifact | Workflow | Pressure Window | Trend | Robust | Decision |
|---|---|---|---|---|---|---|
| C | pass | pass | review | review | review | c_candidate_not_seed_robust |

## Files

- `data/pscale2_c_seed_recheck_candidates.csv`
- `data/pscale2_c_seed_recheck_acceptance.csv`
- `data/pscale2_c_seed_recheck_summary.json`
- `figures/pscale2_c_seed_recheck_p95.png`
