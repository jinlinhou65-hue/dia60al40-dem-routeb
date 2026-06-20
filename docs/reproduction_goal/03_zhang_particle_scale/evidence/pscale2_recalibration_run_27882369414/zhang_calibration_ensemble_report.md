# Zhang Calibration Ensemble Report

- Runs summarized: `3`
- Runs with pass candidate: `0`

## Best Candidate By DEM Run

| Artifact | Size | PScale | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeE-pscale2-Emax60.533-mu0.693-seed2 | E | 2 | 2 | 60.533 | 0.693 | review | 0.1 | 2 | -0.010626 | -0.942374 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax57.506-mu0.693-seed2 | E | 2 | 2 | 57.506 | 0.693 | review | 0.1 | 2 | -0.026359 | -0.942374 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax63.559-mu0.693-seed2 | E | 2 | 2 | 63.559 | 0.693 | review | 0.1 | 2 | -0.0619864 | -0.942374 | needs_participation_increase |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | E | 3 | 0 | -0.0329904 | -0.942374 |
| particle_count_scale | 2 | 3 | 0 | -0.0329904 | -0.942374 |
| mu_scale | 0.693 | 3 | 0 | -0.0329904 | -0.942374 |
| e_al_emax_gpa | 57.506 | 1 | 0 | -0.026359 | -0.942374 |
| e_al_emax_gpa | 60.533 | 1 | 0 | -0.010626 | -0.942374 |
| e_al_emax_gpa | 63.559 | 1 | 0 | -0.0619864 | -0.942374 |

No DEM run has a Zhang `pass` candidate yet. Treat this as evidence to vary contact law, friction, loading path, particle count, or shape model rather than only force-chain post-processing thresholds.
