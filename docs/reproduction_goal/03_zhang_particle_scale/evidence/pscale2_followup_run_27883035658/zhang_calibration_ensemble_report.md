# Zhang Calibration Ensemble Report

- Runs summarized: `3`
- Runs with pass candidate: `2`

## Best Candidate By DEM Run

| Artifact | Size | PScale | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeE-pscale2-Emax75.454-mu0.693-seed2 | E | 2 | 2 | 75.454 | 0.693 | pass | 0.1 | 2 | 0.0372898 | -0.942374 | candidate_pass |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax87.368-mu0.693-seed2 | E | 2 | 2 | 87.368 | 0.693 | pass | 0.1 | 2 | 0.0198942 | -0.942374 | candidate_pass |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax79.426-mu0.693-seed2 | E | 2 | 2 | 79.426 | 0.693 | review | 0.1 | 2 | -0.0138406 | -0.942374 | needs_participation_increase |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | E | 3 | 2 | 0.0144478 | -0.942374 |
| particle_count_scale | 2 | 3 | 2 | 0.0144478 | -0.942374 |
| mu_scale | 0.693 | 3 | 2 | 0.0144478 | -0.942374 |
| e_al_emax_gpa | 75.454 | 1 | 1 | 0.0372898 | -0.942374 |
| e_al_emax_gpa | 79.426 | 1 | 0 | -0.0138406 | -0.942374 |
| e_al_emax_gpa | 87.368 | 1 | 1 | 0.0198942 | -0.942374 |
