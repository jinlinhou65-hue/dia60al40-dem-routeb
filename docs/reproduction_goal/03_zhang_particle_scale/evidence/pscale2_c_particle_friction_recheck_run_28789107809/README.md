# Zhang Sweep Artifact Report

- DEM workflow run: [28789107809](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/28789107809)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `5`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 5 | 409.996 | 385.385 | 434.123 | 48.7379 | 0.0462856 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed0-settle1-vel50 | 72.581 | 0.654 | 417.418 | review | needs_d1_decrease | 1.5 | 2 | 0.015944 | 0.632063 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed1-settle1-vel50 | 72.581 | 0.654 | 385.385 | pass | candidate_pass | 0.25 | 2 | 0.0385439 | -1.17108 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed2-settle1-vel50 | 72.581 | 0.654 | 415.841 | review | needs_physics_calibration | 2 | 2 | -0.0437264 | 1.40967 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed3-settle1-vel50 | 72.581 | 0.654 | 397.212 | pass | candidate_pass | 1 | 2 | 0.641291 | -0.0698562 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed4-settle1-vel50 | 72.581 | 0.654 | 434.123 | pass | candidate_pass | 0.05 | 2 | 0.529959 | -0.472019 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 5 | 3 | 0.236402 | 0.0657558 |
| particle_count_scale | 2 | 5 | 3 | 0.236402 | 0.0657558 |
| mu_scale | 0.654 | 5 | 3 | 0.236402 | 0.0657558 |
| mu_wall_scale | 1.0 | 5 | 3 | 0.236402 | 0.0657558 |
| e_al_emax_gpa | 72.581 | 5 | 3 | 0.236402 | 0.0657558 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `missing`
- Estimated run count: `6`
- Reason: p95=434 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; a Zhang trend candidate exists, so keep a narrow friction bracket

```json
{
  "dem_seed_json": "[\"4\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"108.871\", \"100.314\"]",
  "mu_scale_json": "[\"0.589\", \"0.654\", \"0.719\"]",
  "mu_wall_scale_json": "[\"1\"]",
  "runtime_profile": "demo"
}
```

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
