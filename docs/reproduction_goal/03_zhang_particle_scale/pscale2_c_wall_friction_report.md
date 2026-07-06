# Zhang pscale=2 C Sidewall-Friction Recheck Results

## Conclusion

Reject mu_w=0.001, restore wall scale 1, and return to the contact-model audit before another variable.

## Paired Comparison

| Metric | mu_w=0.05232 | mu_w=0.001 | Change |
|---|---:|---:|---:|
| Mean P95 MPa | 574.211 | 565.114 | -9.097 |
| P95 CV | 0.0396 | 0.0561 | +41.71% |
| Trend pass | 4/5 | 3/5 | |
| Pressure window | 3/5 | 2/5 | |
| Pass + window | 2/5 | 1/5 | |

## Paired Seeds

| Seed | Baseline P95 | Test P95 | Delta MPa | Test pressure | Test trend | Test both |
|---:|---:|---:|---:|---|---|---|
| 0 | 573.483 | 522.994 | -50.489 | review | pass | review |
| 1 | 543.867 | 567.106 | +23.239 | review | review | review |
| 2 | 607.732 | 608.188 | +0.456 | pass | review | review |
| 3 | 575.955 | 577.420 | +1.466 | pass | pass | pass |
| 4 | 570.019 | 549.861 | -20.158 | review | pass | review |

## Acceptance

| Solver | Baseline | Mean pressure | CV | Trend | Combined | Decision |
|---|---|---|---|---|---|---|
| pass | pass | review | review | review | review | c_wall_friction_not_better |
