# Zhang Size-Specific Sweep Summary

- Imported DEM runs: `27874059503, 27874061902, 27874064063`
- Best-row count: `36`
- Zhang pass rows: `15`
- Pressure-window rows: `15`
- Pass + pressure-window rows: `5`
- Pressure window: `572.0-638.0 MPa`

## Imported Runs

| Run | Rows | URL |
|---|---:|---|
| 27874059503 | 12 | https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874059503 |
| 27874061902 | 12 | https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874061902 |
| 27874064063 | 12 | https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874064063 |

## Size Summary

| Size | Runs | Pass | Pressure Window | Pass + Window | P95 Mean MPa | P95 Min | P95 Max | Best Artifact |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| C | 12 | 4 | 6 | 1 | 601.89 | 525.814 | 658.477 | dia60al40-dem-artifacts-sizeC-Emax44.772-mu0.654-seed2 |
| D | 12 | 2 | 5 | 1 | 588.477 | 479.676 | 686.995 | dia60al40-dem-artifacts-sizeD-Emax37.517-mu0.77-seed2 |
| E | 12 | 9 | 4 | 3 | 600.834 | 498.327 | 655.389 | dia60al40-dem-artifacts-sizeE-Emax37.517-mu0.693-seed2 |

## Interpretation

This report combines the C, D, and E size-specific light DEM sweeps. Rows that pass both the Zhang force-chain trend gate and the 572-638 MPa endpoint pressure window are the immediate candidates for the next higher-fidelity Zhang reproduction step.
