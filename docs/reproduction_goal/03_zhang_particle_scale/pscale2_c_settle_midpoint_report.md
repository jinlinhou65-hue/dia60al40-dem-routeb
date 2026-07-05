# Zhang pscale=2 C Settle Midpoint Results

## Conclusion

Reject settle scale 2 as well as scale 4. Restore settle scale 1 and stop using dwell duration as the next C calibration variable; test one different loading/contact control.

## Three-Way Comparison

| Settle scale | Mean P95 MPa | P95 CV | Trend pass | Pressure window | Pass + window |
|---:|---:|---:|---:|---:|---:|
| 1 | 574.211 | 0.0396 | 4/5 | 3/5 | 2/5 |
| 2 | 563.323 | 0.1268 | 5/5 | 0/5 | 0/5 |
| 4 | 567.232 | 0.0911 | 5/5 | 1/5 | 1/5 |

## Paired Seeds

| Seed | Settle 1 P95 | Settle 2 P95 | Settle 4 P95 | 2-1 MPa | S2 trend | S2 pressure | S2 both |
|---:|---:|---:|---:|---:|---|---|---|
| 0 | 573.483 | 536.402 | 574.407 | -37.080 | pass | review | review |
| 1 | 543.867 | 568.082 | 557.364 | +24.215 | pass | review | review |
| 2 | 607.732 | 674.741 | 526.498 | +67.010 | pass | review | review |
| 3 | 575.955 | 478.278 | 651.920 | -97.677 | pass | review | review |
| 4 | 570.019 | 559.112 | 525.970 | -10.908 | pass | review | review |

## Acceptance

| Artifact | Workflow | Paired seeds | Runtime | Mean pressure | CV | Tradeoff | Decision |
|---|---|---|---|---|---|---|---|
| pass | pass | pass | pass | review | review | review | c_settle_midpoint_not_better |
