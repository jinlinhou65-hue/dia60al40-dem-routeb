# Zhang Size-Specific Sweep Summary

- Imported DEM runs: `27875950305, 27875951506, 27875952754`
- Best-row count: `3`
- Zhang pass rows: `1`
- Pressure-window rows: `0`
- Pass + pressure-window rows: `0`
- Pressure window: `572.0-638.0 MPa`

## Imported Runs

| Run | Rows | URL |
|---|---:|---|
| 27875950305 | 1 | https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27875950305 |
| 27875951506 | 1 | https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27875951506 |
| 27875952754 | 1 | https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27875952754 |

## Size Summary

| Size | Runs | Pass | Pressure Window | Pass + Window | P95 Mean MPa | P95 Min | P95 Max | Best Artifact |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| C | 1 | 1 | 0 | 0 | 411.866 | 411.866 | 411.866 | dia60al40-dem-artifacts-sizeC-pscale2-Emax44.772-mu0.654-seed2 |
| D | 1 | 0 | 0 | 0 | 413.405 | 413.405 | 413.405 | dia60al40-dem-artifacts-sizeD-pscale2-Emax37.517-mu0.77-seed2 |
| E | 1 | 0 | 0 | 0 | 371.868 | 371.868 | 371.868 | dia60al40-dem-artifacts-sizeE-pscale2-Emax37.517-mu0.693-seed2 |

## Interpretation

This report combines the C, D, and E size-specific light DEM sweeps. Rows that pass both the Zhang force-chain trend gate and the 572-638 MPa endpoint pressure window are the immediate candidates for the next higher-fidelity Zhang reproduction step.
