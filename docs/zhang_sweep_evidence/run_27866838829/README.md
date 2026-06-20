# Zhang Sweep Artifact Report

- DEM workflow run: [27866838829](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27866838829)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `6`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 6 | 546.429 | 481.608 | 632.842 | 151.234 | 0.0984018 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-Emax36.261-mu0.63-seed0 | 36.261 | 0.63 | 502.224 | review | needs_d1_decrease | 2 | 2 | 0.955137 | 0.533164 |
| dia60al40-dem-artifacts-sizeC-Emax36.261-mu0.7-seed0 | 36.261 | 0.7 | 481.608 | pass | candidate_pass | 0.05 | 2 | 0.00324459 | -0.426456 |
| dia60al40-dem-artifacts-sizeC-Emax36.261-mu0.77-seed0 | 36.261 | 0.77 | 556.269 | pass | candidate_pass | 0.1 | 2 | 0.154894 | -1.32046 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.63-seed0 | 41.686 | 0.63 | 534.727 | review | needs_d1_decrease | 2 | 2 | 0.960542 | 0.781911 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.7-seed0 | 41.686 | 0.7 | 570.904 | pass | candidate_pass | 0.05 | 2 | 0.0119111 | -0.426456 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.77-seed0 | 41.686 | 0.77 | 632.842 | pass | candidate_pass | 0.1 | 2 | 0.144433 | -1.32046 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 6 | 4 | 0.371694 | -0.363126 |
| mu_scale | 0.63 | 2 | 0 | 0.957839 | 0.657538 |
| mu_scale | 0.7 | 2 | 2 | 0.00757783 | -0.426456 |
| mu_scale | 0.77 | 2 | 2 | 0.149664 | -1.32046 |
| e_al_emax_gpa | 36.261 | 3 | 2 | 0.371092 | -0.404584 |
| e_al_emax_gpa | 41.686 | 3 | 2 | 0.372295 | -0.321669 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Estimated run count: `6`
- Reason: p95=556 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; a Zhang trend candidate exists, so keep a narrow friction bracket

```json
{
  "dem_seed_json": "[\"0\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"54.392\", \"45.326\"]",
  "mu_scale_json": "[\"0.693\", \"0.77\", \"0.847\"]",
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
