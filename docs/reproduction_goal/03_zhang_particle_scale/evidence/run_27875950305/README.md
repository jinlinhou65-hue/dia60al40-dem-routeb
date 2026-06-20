# Zhang Sweep Artifact Report

- DEM workflow run: [27875950305](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27875950305)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `1`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 1 | 411.866 | 411.866 | 411.866 | 0 | 0 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax44.772-mu0.654-seed2 | 44.772 | 0.654 | 411.866 | pass | candidate_pass | 0.05 | 2 | 0.1039 | -1.15928 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 1 | 1 | 0.1039 | -1.15928 |
| particle_count_scale | 2 | 1 | 1 | 0.1039 | -1.15928 |
| mu_scale | 0.654 | 1 | 1 | 0.1039 | -1.15928 |
| e_al_emax_gpa | 44.772 | 1 | 1 | 0.1039 | -1.15928 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `missing`
- Estimated run count: `6`
- Reason: p95=412 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; a Zhang trend candidate exists, so keep a narrow friction bracket

```json
{
  "dem_seed_json": "[\"2\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"67.158\", \"65.223\"]",
  "mu_scale_json": "[\"0.589\", \"0.654\", \"0.719\"]",
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
