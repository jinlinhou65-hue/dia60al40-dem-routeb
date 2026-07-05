# Zhang pscale=2 C Loading-Rate Recheck Results

## Conclusion

Restore the 50 cm/s baseline and stop using loading rate as the next C variable; test one contact-law or damping control while keeping settle scale 1.

## Loading-Rate Comparison

| Metric | 50 cm/s baseline | 25 cm/s test | Change |
|---|---:|---:|---:|
| Mean P95 MPa | 574.211 | 578.432 | +4.221 |
| P95 CV | 0.0396 | 0.0528 | +33.52% |
| Trend pass | 4/5 | 5/5 | +1 |
| Pressure window | 3/5 | 3/5 | +0 |
| Pass + window | 2/5 | 3/5 | +1 |

## Paired Seeds

| Seed | 50 cm/s P95 | 25 cm/s P95 | Delta MPa | Delta % | Pressure | Trend | Both |
|---:|---:|---:|---:|---:|---|---|---|
| 0 | 573.483 | 628.783 | +55.300 | +9.64% | pass | pass | pass |
| 1 | 543.867 | 576.160 | +32.293 | +5.94% | pass | pass | pass |
| 2 | 607.732 | 567.845 | -39.887 | -6.56% | review | pass | review |
| 3 | 575.955 | 545.873 | -30.082 | -5.22% | review | pass | review |
| 4 | 570.019 | 573.499 | +3.480 | +0.61% | pass | pass | pass |

## Acceptance

| Artifact | Workflow | Runtime | Mean pressure | CV | Trend | Combined coverage | Decision |
|---|---|---|---|---|---|---|---|
| pass | pass | pass | pass | review | pass | pass | c_loading_rate_not_better |
