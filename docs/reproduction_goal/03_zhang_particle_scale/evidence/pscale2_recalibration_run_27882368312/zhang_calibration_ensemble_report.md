# Zhang Calibration Ensemble Report

- Runs summarized: `3`
- Runs with pass candidate: `0`

## Best Candidate By DEM Run

| Artifact | Size | PScale | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeD-pscale2-Emax57.173-mu0.77-seed2 | D | 2 | 2 | 57.173 | 0.77 | review | 1.25 | 3 | -0.136921 | -0.16442 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeD-pscale2-Emax54.451-mu0.77-seed2 | D | 2 | 2 | 54.451 | 0.77 | review | 0.05 | 2 | -0.214094 | -0.765944 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeD-pscale2-Emax51.728-mu0.77-seed2 | D | 2 | 2 | 51.728 | 0.77 | review | 0.05 | 2 | -0.234061 | -0.765944 | needs_participation_increase |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | D | 3 | 0 | -0.195025 | -0.565436 |
| particle_count_scale | 2 | 3 | 0 | -0.195025 | -0.565436 |
| mu_scale | 0.77 | 3 | 0 | -0.195025 | -0.565436 |
| e_al_emax_gpa | 51.728 | 1 | 0 | -0.234061 | -0.765944 |
| e_al_emax_gpa | 54.451 | 1 | 0 | -0.214094 | -0.765944 |
| e_al_emax_gpa | 57.173 | 1 | 0 | -0.136921 | -0.16442 |

No DEM run has a Zhang `pass` candidate yet. Treat this as evidence to vary contact law, friction, loading path, particle count, or shape model rather than only force-chain post-processing thresholds.
