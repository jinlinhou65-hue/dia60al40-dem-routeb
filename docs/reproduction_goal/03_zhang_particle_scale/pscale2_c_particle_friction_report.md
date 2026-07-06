# Zhang pscale=2 C Interparticle-Friction Recheck Results

## Conclusion

Reject mu_p=0.001 and retain the verified C baseline before another mechanism.

## Paired Comparison

| Metric | Verified baseline | mu_p=0.001 | Change |
|---|---:|---:|---:|
| Mean P95 MPa | 574.211 | 409.996 | -164.215 |
| P95 CV | 0.0396 | 0.0463 | +16.96% |
| Trend pass | 4/5 | 3/5 | |
| Pressure window | 3/5 | 0/5 | |
| Pass + window | 2/5 | 0/5 | |

## Paired Seeds

| Seed | Baseline P95 | Test P95 | Delta MPa | Test pressure | Test trend | Test both |
|---:|---:|---:|---:|---|---|---|
| 0 | 573.483 | 417.418 | -156.064 | review | review | review |
| 1 | 543.867 | 385.385 | -158.482 | review | pass | review |
| 2 | 607.732 | 415.841 | -191.891 | review | review | review |
| 3 | 575.955 | 397.212 | -178.742 | review | pass | review |
| 4 | 570.019 | 434.123 | -135.896 | review | pass | review |

## Acceptance

| Solver | Baseline reuse | Mean pressure | CV | Trend | Combined | Decision |
|---|---|---|---|---|---|---|
| pass | pass | review | review | review | review | c_particle_friction_not_better |
