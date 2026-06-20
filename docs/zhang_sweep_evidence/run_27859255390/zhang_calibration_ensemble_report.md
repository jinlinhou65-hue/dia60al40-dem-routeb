# Zhang Calibration Ensemble Report

- Runs summarized: `6`
- Runs with pass candidate: `2`

## Best Candidate By DEM Run

| Artifact | Size | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeC-Emax24.174-mu0.7-seed0 | C | 0 | 24.174 | 0.7 | pass | 0.05 | 2 | 0.0486253 | -0.426456 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-Emax18-mu0.7-seed0 | C | 0 | 18 | 0.7 | pass | 0.05 | 2 | 0.0102707 | -0.426456 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-Emax24.174-mu1-seed0 | C | 0 | 24.174 | 1 | review | 0.75 | 3 | -0.324931 | -0.305002 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeC-Emax18-mu1.3-seed0 | C | 0 | 18 | 1.3 | review | 0.5 | 2 | -0.428077 | -0.686613 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeC-Emax24.174-mu1.3-seed0 | C | 0 | 24.174 | 1.3 | review | 0.5 | 2 | -0.579369 | -0.686613 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeC-Emax18-mu1-seed0 | C | 0 | 18 | 1 | review | 0.1 | 2 | -0.69186 | -0.339947 | needs_participation_increase |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 6 | 2 | -0.327557 | -0.478515 |
| mu_scale | 0.7 | 2 | 2 | 0.029448 | -0.426456 |
| mu_scale | 1.0 | 2 | 0 | -0.508396 | -0.322474 |
| mu_scale | 1.3 | 2 | 0 | -0.503723 | -0.686613 |
| e_al_emax_gpa | 18.0 | 3 | 1 | -0.369889 | -0.484339 |
| e_al_emax_gpa | 24.174 | 3 | 1 | -0.285225 | -0.47269 |
