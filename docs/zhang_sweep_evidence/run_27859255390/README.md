# Zhang Sweep Artifact Report

- DEM workflow run: [27859255390](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27859255390)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `6`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 6 | 538.866 | 285.491 | 851.212 | 565.721 | 0.401007 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-Emax18-mu0.7-seed0 | 18 | 0.7 | 285.491 | pass | candidate_pass | 0.05 | 2 | 0.0102707 | -0.426456 |
| dia60al40-dem-artifacts-sizeC-Emax18-mu1-seed0 | 18 | 1 | 715.644 | review | needs_participation_increase | 0.1 | 2 | -0.69186 | -0.339947 |
| dia60al40-dem-artifacts-sizeC-Emax18-mu1.3-seed0 | 18 | 1.3 | 555.232 | review | needs_participation_increase | 0.5 | 2 | -0.428077 | -0.686613 |
| dia60al40-dem-artifacts-sizeC-Emax24.174-mu0.7-seed0 | 24.174 | 0.7 | 347.947 | pass | candidate_pass | 0.05 | 2 | 0.0486253 | -0.426456 |
| dia60al40-dem-artifacts-sizeC-Emax24.174-mu1-seed0 | 24.174 | 1 | 477.669 | review | needs_participation_increase | 0.75 | 3 | -0.324931 | -0.305002 |
| dia60al40-dem-artifacts-sizeC-Emax24.174-mu1.3-seed0 | 24.174 | 1.3 | 851.212 | review | needs_participation_increase | 0.5 | 2 | -0.579369 | -0.686613 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 6 | 2 | -0.327557 | -0.478515 |
| mu_scale | 0.7 | 2 | 2 | 0.029448 | -0.426456 |
| mu_scale | 1.0 | 2 | 0 | -0.508396 | -0.322474 |
| mu_scale | 1.3 | 2 | 0 | -0.503723 | -0.686613 |
| e_al_emax_gpa | 18.0 | 3 | 1 | -0.369889 | -0.484339 |
| e_al_emax_gpa | 24.174 | 3 | 1 | -0.285225 | -0.47269 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Estimated run count: `6`
- Reason: p95=348 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; a Zhang trend candidate exists, so keep a narrow friction bracket

```json
{
  "dem_seed_json": "[\"0\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"36.261\", \"41.686\"]",
  "mu_scale_json": "[\"0.63\", \"0.7\", \"0.77\"]",
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
