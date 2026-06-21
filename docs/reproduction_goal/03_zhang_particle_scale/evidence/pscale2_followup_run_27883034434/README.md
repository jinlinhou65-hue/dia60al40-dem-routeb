# Zhang Sweep Artifact Report

- DEM workflow run: [27883034434](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27883034434)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `3`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 3 | 571.72 | 520.277 | 634.795 | 114.518 | 0.10169 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeD-pscale2-Emax57.173-mu0.77-seed2 | 57.173 | 0.77 | 634.795 | review | needs_participation_increase | 1.25 | 3 | -0.136921 | -0.16442 |
| dia60al40-dem-artifacts-sizeD-pscale2-Emax57.173-mu0.847-seed2 | 57.173 | 0.847 | 560.089 | review | needs_physics_calibration | 2 | 2 | -0.115314 | 0.721821 |
| dia60al40-dem-artifacts-sizeD-pscale2-Emax57.173-mu0.963-seed2 | 57.173 | 0.963 | 520.277 | review | needs_d1_decrease | 2 | 2 | 0.931471 | 0.702845 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | D | 3 | 0 | 0.226412 | 0.420082 |
| particle_count_scale | 2 | 3 | 0 | 0.226412 | 0.420082 |
| mu_scale | 0.77 | 1 | 0 | -0.136921 | -0.16442 |
| mu_scale | 0.847 | 1 | 0 | -0.115314 | 0.721821 |
| mu_scale | 0.963 | 1 | 0 | 0.931471 | 0.702845 |
| e_al_emax_gpa | 57.173 | 3 | 0 | 0.226412 | 0.420082 |

## Next Recommendation

- Diagnosis: `needs_participation_increase`
- Mode: `missing`
- Estimated run count: `6`
- Reason: p95 is inside Zhang's pressure endpoint window, so keep a narrow Al modulus bracket; strong-force participation still decreases, so bracket friction scale around the current run

```json
{
  "dem_seed_json": "[\"2\"]",
  "diamond_size_case_json": "[\"D\"]",
  "e_al_emax_sweep_json": "[\"51.456\", \"62.89\"]",
  "mu_scale_json": "[\"0.539\", \"0.77\", \"1.001\"]",
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
