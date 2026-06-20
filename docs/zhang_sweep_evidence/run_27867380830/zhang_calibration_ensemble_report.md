# Zhang Calibration Ensemble Report

- Runs summarized: `9`
- Runs with pass candidate: `5`

## Best Candidate By DEM Run

| Artifact | Size | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.77-seed0 | C | 0 | 41.686 | 0.77 | pass | 0.1 | 2 | 0.144433 | -1.32046 | candidate_pass |
| dia60al40-dem-artifacts-sizeE-Emax41.686-mu0.77-seed0 | E | 0 | 41.686 | 0.77 | pass | 0.75 | 2 | 0.0988269 | -0.318278 | candidate_pass |
| dia60al40-dem-artifacts-sizeD-Emax41.686-mu0.77-seed2 | D | 2 | 41.686 | 0.77 | pass | 0.1 | 2 | 0.0903001 | -0.627505 | candidate_pass |
| dia60al40-dem-artifacts-sizeE-Emax41.686-mu0.77-seed1 | E | 1 | 41.686 | 0.77 | pass | 0.1 | 2 | 0.037351 | -0.955001 | candidate_pass |
| dia60al40-dem-artifacts-sizeE-Emax41.686-mu0.77-seed2 | E | 2 | 41.686 | 0.77 | pass | 0.1 | 2 | 0.0187333 | -0.962857 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.77-seed1 | C | 1 | 41.686 | 0.77 | review | 0.05 | 2 | -0.0298141 | -1.04237 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeD-Emax41.686-mu0.77-seed0 | D | 0 | 41.686 | 0.77 | review | 0.25 | 2 | -0.0708973 | -0.964074 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.77-seed2 | C | 2 | 41.686 | 0.77 | review | 2 | 2 | 0.954169 | 0.623926 | needs_d1_decrease |
| dia60al40-dem-artifacts-sizeD-Emax41.686-mu0.77-seed1 | D | 1 | 41.686 | 0.77 | review | 1 | 2 | -0.127762 | -0.646442 | needs_participation_increase |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 3 | 1 | 0.356263 | -0.579634 |
| diamond_size_case | D | 3 | 1 | -0.0361197 | -0.746007 |
| diamond_size_case | E | 3 | 3 | 0.0516371 | -0.745379 |
| mu_scale | 0.77 | 9 | 5 | 0.123927 | -0.69034 |
| e_al_emax_gpa | 41.686 | 9 | 5 | 0.123927 | -0.69034 |
