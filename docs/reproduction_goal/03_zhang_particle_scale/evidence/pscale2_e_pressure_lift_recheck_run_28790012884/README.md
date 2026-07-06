# Zhang Sweep Artifact Report

- DEM workflow run: [28790012884](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/28790012884)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `5`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 5 | 644.331 | 585.884 | 702.232 | 116.348 | 0.0700318 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed0-settle1-vel50 | 96.417 | 0.693 | 702.232 | review | needs_participation_increase | 0.05 | 2 | -0.0619075 | -1.31485 |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed1-settle1-vel50 | 96.417 | 0.693 | 632.31 | pass | candidate_pass | 0.05 | 2 | 0.145707 | -0.961173 |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed2-settle1-vel50 | 96.417 | 0.693 | 626.608 | pass | candidate_pass | 0.1 | 2 | 0.0071427 | -0.942374 |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed3-settle1-vel50 | 96.417 | 0.693 | 585.884 | pass | candidate_pass | 0.05 | 2 | 0.445757 | -1.64006 |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed4-settle1-vel50 | 96.417 | 0.693 | 674.619 | pass | candidate_pass | 0.05 | 2 | 0.10029 | -0.945109 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | E | 5 | 4 | 0.127398 | -1.16071 |
| particle_count_scale | 2 | 5 | 4 | 0.127398 | -1.16071 |
| mu_scale | 0.693 | 5 | 4 | 0.127398 | -1.16071 |
| mu_wall_scale | 1.0 | 5 | 4 | 0.127398 | -1.16071 |
| e_al_emax_gpa | 96.417 | 5 | 4 | 0.127398 | -1.16071 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `size_specific_calibration`
- Estimated run count: `20`
- Reason: only 3/5 seed/size rows both pass Zhang trend gates and fall inside the 572-638 MPa endpoint window, so one global mu/E pair is not robust

```json
{}
```

### Size-specific dispatch plan

| Size | Estimated Runs | Pressure Action | Trend Action | Inputs |
|---|---:|---|---|---|
| E | 20 | mean endpoint pressure is above Zhang window; lower size-specific endpoint modulus | size case has mixed trend gates; bracket friction around the current value | `{"allow_evidence_mismatch": "true", "dem_seed_json": "[\"0\", \"1\", \"2\", \"3\", \"4\"]", "diamond_size_case_json": "[\"E\"]", "e_al_emax_sweep_json": "[\"89.783\", \"86.775\"]", "mu_scale_json": "[\"0.589\", \"0.797\"]", "mu_wall_scale_json": "[\"1\"]", "runtime_profile": "demo"}` |

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
