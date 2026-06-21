# Zhang Sweep Artifact Report

- DEM workflow run: [27898770533](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27898770533)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `5`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 5 | 524.619 | 493.878 | 586.646 | 92.7682 | 0.0804299 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax63.462-mu0.654-seed0 | 63.462 | 0.654 | 493.878 | pass | candidate_pass | 1.5 | 2 | 0.0183545 | -0.525466 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax63.462-mu0.654-seed1 | 63.462 | 0.654 | 496.226 | pass | candidate_pass | 0.1 | 2 | 0.090727 | -1.35863 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax63.462-mu0.654-seed2 | 63.462 | 0.654 | 586.646 | pass | candidate_pass | 0.05 | 2 | 0.0650829 | -1.15928 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax63.462-mu0.654-seed3 | 63.462 | 0.654 | 550.731 | review | needs_participation_increase | 0.1 | 2 | -0.0016301 | -0.957276 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax63.462-mu0.654-seed4 | 63.462 | 0.654 | 495.614 | pass | candidate_pass | 0.75 | 3 | 0.311607 | -0.505916 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 5 | 4 | 0.0968282 | -0.901313 |
| particle_count_scale | 2 | 5 | 4 | 0.0968282 | -0.901313 |
| mu_scale | 0.654 | 5 | 4 | 0.0968282 | -0.901313 |
| e_al_emax_gpa | 63.462 | 5 | 4 | 0.0968282 | -0.901313 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `size_specific_calibration`
- Estimated run count: `20`
- Reason: only 1/5 seed/size rows both pass Zhang trend gates and fall inside the 572-638 MPa endpoint window, so one global mu/E pair is not robust

```json
{}
```

### Size-specific dispatch plan

| Size | Estimated Runs | Pressure Action | Trend Action | Inputs |
|---|---:|---|---|---|
| C | 20 | mean endpoint pressure is below Zhang window; raise size-specific endpoint modulus | size case has mixed trend gates; bracket friction around the current value | `{"allow_evidence_mismatch": "true", "dem_seed_json": "[\"0\", \"1\", \"2\", \"3\", \"4\"]", "diamond_size_case_json": "[\"C\"]", "e_al_emax_sweep_json": "[\"63.462\", \"72.581\"]", "mu_scale_json": "[\"0.556\", \"0.752\"]", "runtime_profile": "demo"}` |

## Imported Files

- `ensemble_runs.csv`
- `ensemble_pressure_summary.csv`
- `ensemble_pressure_summary_by_size_case.csv`
- `zhang_calibration_candidates.csv`
- `zhang_calibration_best_by_run.csv`
- `zhang_calibration_group_summary.csv`
- `zhang_calibration_ensemble_report.md`
- `zhang_next_sweep_recommendation.json`
- `zhang_next_sweep_recommendation.md`
