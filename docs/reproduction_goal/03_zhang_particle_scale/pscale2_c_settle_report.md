# Zhang pscale=2 C 4x-Settle Recheck Results

## Conclusion

Reject settle scale 4 for the C baseline: it makes all five trend gates pass, but increases pressure CV and reduces pass+window coverage. Restore settle scale 1. If dwell remains the next variable, test only the bounded midpoint settle scale 2 with Emax=72.581 GPa and mu=0.654 held fixed.

## Settle Hypothesis Test

| Metric | Settle scale 1 | Settle scale 4 | Change |
|---|---:|---:|---:|
| Mean P95 MPa | 574.211 | 567.232 | -6.979 |
| P95 CV | 0.0396 | 0.0911 | +130.22% |
| Trend pass | 4/5 | 5/5 | +1 seed |
| Pressure window | 3/5 | 1/5 | -2 seeds |
| Pass + window | 2/5 | 1/5 | -1 seed |

## Paired Seeds

| Seed | Settle 1 P95 | Settle 4 P95 | Delta MPa | Delta % | Pressure | Trend | Both |
|---:|---:|---:|---:|---:|---|---|---|
| 0 | 573.483 | 574.407 | +0.925 | +0.16% | pass | pass | pass |
| 1 | 543.867 | 557.364 | +13.497 | +2.48% | review | pass | review |
| 2 | 607.732 | 526.498 | -81.234 | -13.37% | review | pass | review |
| 3 | 575.955 | 651.920 | +75.966 | +13.19% | review | pass | review |
| 4 | 570.019 | 525.970 | -44.050 | -7.73% | review | pass | review |

## Acceptance

| Artifact | Workflow | Runtime provenance | All trend | All pressure | Seed robust | Decision |
|---|---|---|---|---|---|---|
| pass | pass | pass | pass | review | review | c_settle_improves_trend_but_worsens_pressure_robustness |

## Files

- `data/pscale2_c_settle_candidates.csv`
- `data/pscale2_c_settle_paired.csv`
- `data/pscale2_c_settle_acceptance.csv`
- `data/pscale2_c_settle_summary.json`
- `figures/pscale2_c_settle_paired.png`
