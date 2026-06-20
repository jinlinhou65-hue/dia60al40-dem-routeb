# Zhang Calibration Ensemble Report

- Runs summarized: `1`
- Runs with pass candidate: `0`

## Best Candidate By DEM Run

| Artifact | Size | PScale | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeE-pscale2-Emax37.517-mu0.693-seed2 | E | 2 | 2 | 37.517 | 0.693 | review | 0.1 | 2 | -0.0346251 | -0.942374 | needs_participation_increase |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | E | 1 | 0 | -0.0346251 | -0.942374 |
| particle_count_scale | 2 | 1 | 0 | -0.0346251 | -0.942374 |
| mu_scale | 0.693 | 1 | 0 | -0.0346251 | -0.942374 |
| e_al_emax_gpa | 37.517 | 1 | 0 | -0.0346251 | -0.942374 |

No DEM run has a Zhang `pass` candidate yet. Treat this as evidence to vary contact law, friction, loading path, particle count, or shape model rather than only force-chain post-processing thresholds.
