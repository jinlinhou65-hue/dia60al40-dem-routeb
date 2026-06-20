# Zhang Calibration Ensemble Report

- Runs summarized: `1`
- Runs with pass candidate: `0`

## Best Candidate By DEM Run

| Artifact | Size | PScale | Seed | Emax GPa | Mu Scale | Status | Threshold | Min Chain | Participation Delta | D1 Delta | Diagnosis |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| dia60al40-dem-artifacts-sizeD-pscale2-Emax37.517-mu0.77-seed2 | D | 2 | 2 | 37.517 | 0.77 | review | 0.05 | 2 | -0.236693 | -0.765944 | needs_participation_increase |

## Parameter Group Summary

| Group By | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | D | 1 | 0 | -0.236693 | -0.765944 |
| particle_count_scale | 2 | 1 | 0 | -0.236693 | -0.765944 |
| mu_scale | 0.77 | 1 | 0 | -0.236693 | -0.765944 |
| e_al_emax_gpa | 37.517 | 1 | 0 | -0.236693 | -0.765944 |

No DEM run has a Zhang `pass` candidate yet. Treat this as evidence to vary contact law, friction, loading path, particle count, or shape model rather than only force-chain post-processing thresholds.
