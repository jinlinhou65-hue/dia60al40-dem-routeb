# Zhang Calibration Ensemble Report

- Runs summarized: `5`
- Runs with pass candidate: `4`

## Best Candidate By DEM Run

| Artifact | Size | PScale | Seed | Emax GPa | Mu Scale | Wall Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed3-settle1-vel50 | E | 2 | 3 | 96.417 | 0.693 | 1 | pass | 0.05 | 2 | 0.445757 | -1.64006 | candidate_pass |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed1-settle1-vel50 | E | 2 | 1 | 96.417 | 0.693 | 1 | pass | 0.05 | 2 | 0.145707 | -0.961173 | candidate_pass |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed4-settle1-vel50 | E | 2 | 4 | 96.417 | 0.693 | 1 | pass | 0.05 | 2 | 0.10029 | -0.945109 | candidate_pass |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed2-settle1-vel50 | E | 2 | 2 | 96.417 | 0.693 | 1 | pass | 0.1 | 2 | 0.0071427 | -0.942374 | candidate_pass |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed0-settle1-vel50 | E | 2 | 0 | 96.417 | 0.693 | 1 | review | 0.05 | 2 | -0.0619075 | -1.31485 | needs_participation_increase |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | E | 5 | 4 | 0.127398 | -1.16071 |
| particle_count_scale | 2 | 5 | 4 | 0.127398 | -1.16071 |
| mu_scale | 0.693 | 5 | 4 | 0.127398 | -1.16071 |
| mu_wall_scale | 1.0 | 5 | 4 | 0.127398 | -1.16071 |
| e_al_emax_gpa | 96.417 | 5 | 4 | 0.127398 | -1.16071 |
