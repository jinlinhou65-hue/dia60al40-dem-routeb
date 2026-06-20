# Zhang Sweep Artifact Report

- DEM workflow run: [27882369414](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27882369414)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `3`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 3 | 467.854 | 457.388 | 480.14 | 22.7518 | 0.0245472 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeE-pscale2-Emax57.506-mu0.693-seed2 | 57.506 | 0.693 | 457.388 | review | needs_participation_increase | 0.1 | 2 | -0.026359 | -0.942374 |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax60.533-mu0.693-seed2 | 60.533 | 0.693 | 466.035 | review | needs_participation_increase | 0.1 | 2 | -0.010626 | -0.942374 |
| dia60al40-dem-artifacts-sizeE-pscale2-Emax63.559-mu0.693-seed2 | 63.559 | 0.693 | 480.14 | review | needs_participation_increase | 0.1 | 2 | -0.0619864 | -0.942374 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | E | 3 | 0 | -0.0329904 | -0.942374 |
| particle_count_scale | 2 | 3 | 0 | -0.0329904 | -0.942374 |
| mu_scale | 0.693 | 3 | 0 | -0.0329904 | -0.942374 |
| e_al_emax_gpa | 57.506 | 1 | 0 | -0.026359 | -0.942374 |
| e_al_emax_gpa | 60.533 | 1 | 0 | -0.010626 | -0.942374 |
| e_al_emax_gpa | 63.559 | 1 | 0 | -0.0619864 | -0.942374 |

## Next Recommendation

- Diagnosis: `needs_participation_increase`
- Mode: `missing`
- Estimated run count: `6`
- Reason: p95=480 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; strong-force participation still decreases, so bracket friction scale around the current run

```json
{
  "dem_seed_json": "[\"2\"]",
  "diamond_size_case_json": "[\"E\"]",
  "e_al_emax_sweep_json": "[\"95.338\", \"79.449\"]",
  "mu_scale_json": "[\"0.485\", \"0.693\", \"0.901\"]",
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
