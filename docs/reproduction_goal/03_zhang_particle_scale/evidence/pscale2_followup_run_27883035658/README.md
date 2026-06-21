# Zhang Sweep Artifact Report

- DEM workflow run: [27883035658](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27883035658)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `3`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 3 | 533.326 | 520.09 | 543.689 | 23.599 | 0.0226107 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeE-pscale2-Emax75.454-mu0.693-seed2 | 75.454 | 0.693 | 520.09 | pass | candidate_pass | 0.1 | 2 | 0.0372898 | -0.942374 |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax79.426-mu0.693-seed2 | 79.426 | 0.693 | 536.199 | review | needs_participation_increase | 0.1 | 2 | -0.0138406 | -0.942374 |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax87.368-mu0.693-seed2 | 87.368 | 0.693 | 543.689 | pass | candidate_pass | 0.1 | 2 | 0.0198942 | -0.942374 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | E | 3 | 2 | 0.0144478 | -0.942374 |
| particle_count_scale | 2 | 3 | 2 | 0.0144478 | -0.942374 |
| mu_scale | 0.693 | 3 | 2 | 0.0144478 | -0.942374 |
| e_al_emax_gpa | 75.454 | 1 | 1 | 0.0372898 | -0.942374 |
| e_al_emax_gpa | 79.426 | 1 | 0 | -0.0138406 | -0.942374 |
| e_al_emax_gpa | 87.368 | 1 | 1 | 0.0198942 | -0.942374 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `missing`
- Estimated run count: `6`
- Reason: p95=544 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; a Zhang trend candidate exists, so keep a narrow friction bracket

```json
{
  "dem_seed_json": "[\"2\"]",
  "diamond_size_case_json": "[\"E\"]",
  "e_al_emax_sweep_json": "[\"131.052\", \"109.21\"]",
  "mu_scale_json": "[\"0.624\", \"0.693\", \"0.762\"]",
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
