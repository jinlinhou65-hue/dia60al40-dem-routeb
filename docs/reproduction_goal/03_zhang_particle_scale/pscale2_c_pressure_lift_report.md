# Zhang pscale=2 C Pressure-Lift Recheck Results

## Conclusion

The Emax lift improved C but only 2/5 seeds pass both gates. Keep Emax=72.581 GPa as the pressure reference, but do not raise Emax again as the sole control. Next change one loading-path or contact-relaxation variable to reduce seed variance, then rerun the same five seeds with mu held at 0.654.

## Hypothesis Test

| Metric | Baseline | Pressure lift | Change |
|---|---:|---:|---:|
| Emax GPa | 63.462 | 72.581 | +14.37% |
| Mean P95 MPa | 524.619 | 574.211 | +9.45% |
| P95 CV | 0.0804 | 0.0396 | -50.80% |
| Pass + window seeds | 1/5 | 2/5 | +1 seed |

The Emax increase was 14.37%, while mean P95 increased only 9.45% (response ratio 0.658). The proportional 600 MPa hypothesis therefore over-predicted the ensemble mean by 25.789 MPa.

## Paired Seeds

| Seed | Baseline P95 | Lift P95 | Delta MPa | Delta % | Pressure Gate | Trend | Both |
|---:|---:|---:|---:|---:|---|---|---|
| 0 | 493.878 | 573.483 | +79.605 | +16.12% | pass | review | review |
| 1 | 496.226 | 543.867 | +47.642 | +9.60% | review | pass | review |
| 2 | 586.646 | 607.732 | +21.085 | +3.59% | pass | pass | pass |
| 3 | 550.731 | 575.955 | +25.224 | +4.58% | pass | pass | pass |
| 4 | 495.614 | 570.019 | +74.405 | +15.01% | review | pass | review |

## Acceptance

| Artifact | Workflow | Mean pressure | All-seed pressure | All-seed trend | Seed robust | Decision |
|---|---|---|---|---|---|---|
| pass | pass | pass | review | review | review | c_pressure_lift_improves_but_not_seed_robust |

## Files

- `data/pscale2_c_pressure_lift_candidates.csv`
- `data/pscale2_c_pressure_lift_paired.csv`
- `data/pscale2_c_pressure_lift_acceptance.csv`
- `data/pscale2_c_pressure_lift_summary.json`
- `figures/pscale2_c_pressure_lift_paired.png`
