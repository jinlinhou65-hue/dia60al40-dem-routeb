# Zhang Sweep Artifact Report

- DEM workflow run: [27875951506](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27875951506)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `1`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 1 | 413.405 | 413.405 | 413.405 | 0 | 0 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeD-pscale2-Emax37.517-mu0.77-seed2 | 37.517 | 0.77 | 413.405 | review | needs_participation_increase | 0.05 | 2 | -0.236693 | -0.765944 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | D | 1 | 0 | -0.236693 | -0.765944 |
| particle_count_scale | 2 | 1 | 0 | -0.236693 | -0.765944 |
| mu_scale | 0.77 | 1 | 0 | -0.236693 | -0.765944 |
| e_al_emax_gpa | 37.517 | 1 | 0 | -0.236693 | -0.765944 |

## Next Recommendation

- Diagnosis: `needs_participation_increase`
- Mode: `missing`
- Estimated run count: `6`
- Reason: p95=413 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; strong-force participation still decreases, so bracket friction scale around the current run

```json
{
  "dem_seed_json": "[\"2\"]",
  "diamond_size_case_json": "[\"D\"]",
  "e_al_emax_sweep_json": "[\"56.276\", \"54.451\"]",
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
