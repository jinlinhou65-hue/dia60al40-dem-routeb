# Zhang Calibration Ensemble Report

- Runs summarized: `6`
- Runs with pass candidate: `4`

## Best Candidate By DEM Run

| Artifact | Size | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeC-Emax36.261-mu0.77-seed0 | C | 0 | 36.261 | 0.77 | pass | 0.1 | 2 | 0.154894 | -1.32046 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.77-seed0 | C | 0 | 41.686 | 0.77 | pass | 0.1 | 2 | 0.144433 | -1.32046 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.7-seed0 | C | 0 | 41.686 | 0.7 | pass | 0.05 | 2 | 0.0119111 | -0.426456 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-Emax36.261-mu0.7-seed0 | C | 0 | 36.261 | 0.7 | pass | 0.05 | 2 | 0.00324459 | -0.426456 | candidate_pass |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.63-seed0 | C | 0 | 41.686 | 0.63 | review | 2 | 2 | 0.960542 | 0.781911 | needs_d1_decrease |
| dia60al40-dem-artifacts-sizeC-Emax36.261-mu0.63-seed0 | C | 0 | 36.261 | 0.63 | review | 2 | 2 | 0.955137 | 0.533164 | needs_d1_decrease |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 6 | 4 | 0.371694 | -0.363126 |
| mu_scale | 0.63 | 2 | 0 | 0.957839 | 0.657538 |
| mu_scale | 0.7 | 2 | 2 | 0.00757783 | -0.426456 |
| mu_scale | 0.77 | 2 | 2 | 0.149664 | -1.32046 |
| e_al_emax_gpa | 36.261 | 3 | 2 | 0.371092 | -0.404584 |
| e_al_emax_gpa | 41.686 | 3 | 2 | 0.372295 | -0.321669 |
