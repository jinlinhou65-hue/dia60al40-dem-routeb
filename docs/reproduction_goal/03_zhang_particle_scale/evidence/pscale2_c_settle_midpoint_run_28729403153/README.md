# Zhang Sweep Artifact Report

- DEM workflow run: [28729403153](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/28729403153)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `5`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 5 | 563.323 | 478.278 | 674.741 | 196.463 | 0.12681 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed0-settle2 | 72.581 | 0.654 | 536.402 | pass | candidate_pass | 0.75 | 3 | 0.209913 | -0.423739 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed1-settle2 | 72.581 | 0.654 | 568.082 | pass | candidate_pass | 0.5 | 2 | 0.244832 | -0.363303 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed2-settle2 | 72.581 | 0.654 | 674.741 | pass | candidate_pass | 0.05 | 2 | 0.328186 | -1.47662 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed3-settle2 | 72.581 | 0.654 | 478.278 | pass | candidate_pass | 1 | 4 | 0.127906 | -0.444534 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed4-settle2 | 72.581 | 0.654 | 559.112 | pass | candidate_pass | 0.05 | 2 | 0.389029 | -1.22011 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 5 | 5 | 0.259973 | -0.78566 |
| particle_count_scale | 2 | 5 | 5 | 0.259973 | -0.78566 |
| mu_scale | 0.654 | 5 | 5 | 0.259973 | -0.78566 |
| e_al_emax_gpa | 72.581 | 5 | 5 | 0.259973 | -0.78566 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `missing`
- Estimated run count: `6`
- Reason: p95=568 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; a Zhang trend candidate exists, so keep a narrow friction bracket

```json
{
  "dem_seed_json": "[\"1\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"108.871\", \"90.726\"]",
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
