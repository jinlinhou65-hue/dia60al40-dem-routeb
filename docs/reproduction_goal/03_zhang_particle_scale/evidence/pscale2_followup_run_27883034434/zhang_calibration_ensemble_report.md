# Zhang Calibration Ensemble Report

- Runs summarized: `3`
- Runs with pass candidate: `0`

## Best Candidate By DEM Run

| Artifact | Size | PScale | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeD-pscale2-Emax57.173-mu0.77-seed2 | D | 2 | 2 | 57.173 | 0.77 | review | 1.25 | 3 | -0.136921 | -0.16442 | needs_participation_increase |
| dia60al40-dem-artifacts-sizeD-pscale2-Emax57.173-mu0.963-seed2 | D | 2 | 2 | 57.173 | 0.963 | review | 2 | 2 | 0.931471 | 0.702845 | needs_d1_decrease |
| dia60al40-dem-artifacts-sizeD-pscale2-Emax57.173-mu0.847-seed2 | D | 2 | 2 | 57.173 | 0.847 | review | 2 | 2 | -0.115314 | 0.721821 | needs_physics_calibration |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | D | 3 | 0 | 0.226412 | 0.420082 |
| particle_count_scale | 2 | 3 | 0 | 0.226412 | 0.420082 |
| mu_scale | 0.77 | 1 | 0 | -0.136921 | -0.16442 |
| mu_scale | 0.847 | 1 | 0 | -0.115314 | 0.721821 |
| mu_scale | 0.963 | 1 | 0 | 0.931471 | 0.702845 |
| e_al_emax_gpa | 57.173 | 3 | 0 | 0.226412 | 0.420082 |

No DEM run has a Zhang `pass` candidate yet. Treat this as evidence to vary contact law, friction, loading path, particle count, or shape model rather than only force-chain post-processing thresholds.
