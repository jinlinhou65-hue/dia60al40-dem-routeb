# Zhang Calibration Ensemble Report

- Runs summarized: `5`
- Runs with pass candidate: `3`

## Best Candidate By DEM Run

| Artifact | Size | PScale | Seed | Emax GPa | Mu Scale | Wall Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed3-settle1-vel50 | C | 2 | 3 | 72.581 | 0.654 | 1 | pass | 1 | 2 | 0.641291 | -0.0698562 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed4-settle1-vel50 | C | 2 | 4 | 72.581 | 0.654 | 1 | pass | 0.05 | 2 | 0.529959 | -0.472019 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed1-settle1-vel50 | C | 2 | 1 | 72.581 | 0.654 | 1 | pass | 0.25 | 2 | 0.0385439 | -1.17108 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed0-settle1-vel50 | C | 2 | 0 | 72.581 | 0.654 | 1 | review | 1.5 | 2 | 0.015944 | 0.632063 | needs_d1_decrease |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed2-settle1-vel50 | C | 2 | 2 | 72.581 | 0.654 | 1 | review | 2 | 2 | -0.0437264 | 1.40967 | needs_physics_calibration |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 5 | 3 | 0.236402 | 0.0657558 |
| particle_count_scale | 2 | 5 | 3 | 0.236402 | 0.0657558 |
| mu_scale | 0.654 | 5 | 3 | 0.236402 | 0.0657558 |
| mu_wall_scale | 1.0 | 5 | 3 | 0.236402 | 0.0657558 |
| e_al_emax_gpa | 72.581 | 5 | 3 | 0.236402 | 0.0657558 |
