# Zhang Sweep Artifact Report

- DEM workflow run: [28710536524](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/28710536524)
- Source artifact: `dia60al40-dem-ensemble-summary`
- Artifact id: `8082918491`
- SHA-256 verified: `2e9b0b63917057c3e3aec871e3b1410c526c8dc8015451107d4e22c446cd8f89`
- DEM runs summarized: `5`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 5 | 567.232 | 525.97 | 651.92 | 125.95 | 0.091107 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed0-settle4 | 72.581 | 0.654 | 574.407 | pass | candidate_pass | 0.1 | 2 | 0.412537 | -1.15 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed1-settle4 | 72.581 | 0.654 | 557.364 | pass | candidate_pass | 0.1 | 2 | 0.0918895 | -0.982688 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed2-settle4 | 72.581 | 0.654 | 526.498 | pass | candidate_pass | 0.25 | 2 | 0.191575 | -0.77722 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed3-settle4 | 72.581 | 0.654 | 651.92 | pass | candidate_pass | 0.05 | 2 | 0.0796261 | -0.957854 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed4-settle4 | 72.581 | 0.654 | 525.97 | pass | candidate_pass | 0.05 | 2 | 0.131699 | -1.1241 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 5 | 5 | 0.181465 | -0.998373 |
| particle_count_scale | 2 | 5 | 5 | 0.181465 | -0.998373 |
| mu_scale | 0.654 | 5 | 5 | 0.181465 | -0.998373 |
| e_al_emax_gpa | 72.581 | 5 | 5 | 0.181465 | -0.998373 |

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
| C | 20 | mean endpoint pressure is below Zhang window; raise size-specific endpoint modulus | all seeds pass Zhang trend gates; keep a narrow friction bracket | `{"allow_evidence_mismatch": "true", "dem_seed_json": "[\"0\", \"1\", \"2\", \"3\", \"4\"]", "diamond_size_case_json": "[\"C\"]", "e_al_emax_sweep_json": "[\"72.581\", \"76.774\"]", "mu_scale_json": "[\"0.589\", \"0.654\"]", "runtime_profile": "demo"}` |

## Imported Files

- `artifact_verification.json`
- `ensemble_runs.csv`
- `ensemble_pressure_summary.csv`
- `ensemble_pressure_summary_by_size_case.csv`
- `zhang_calibration_candidates.csv`
- `zhang_calibration_best_by_run.csv`
- `zhang_calibration_group_summary.csv`
- `zhang_calibration_ensemble_report.md`
- `zhang_next_sweep_recommendation.json`
- `zhang_next_sweep_recommendation.md`
