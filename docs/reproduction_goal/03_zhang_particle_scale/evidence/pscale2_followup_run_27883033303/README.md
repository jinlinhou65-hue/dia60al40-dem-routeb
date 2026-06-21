# Zhang Sweep Artifact Report

- DEM workflow run: [27883033303](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27883033303)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `4`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 4 | 554.813 | 527.446 | 586.646 | 59.2003 | 0.043853 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax60.462-mu0.654-seed2 | 60.462 | 0.654 | 551.239 | pass | candidate_pass | 0.05 | 2 | 0.0833793 | -1.15928 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax61.462-mu0.654-seed2 | 61.462 | 0.654 | 527.446 | pass | candidate_pass | 0.05 | 2 | 0.0921823 | -1.15928 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax62.462-mu0.654-seed2 | 62.462 | 0.654 | 553.922 | pass | candidate_pass | 0.05 | 2 | 0.0855055 | -1.15928 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax63.462-mu0.654-seed2 | 63.462 | 0.654 | 586.646 | pass | candidate_pass | 0.05 | 2 | 0.0650829 | -1.15928 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 4 | 4 | 0.0815375 | -1.15928 |
| particle_count_scale | 2 | 4 | 4 | 0.0815375 | -1.15928 |
| mu_scale | 0.654 | 4 | 4 | 0.0815375 | -1.15928 |
| e_al_emax_gpa | 60.462 | 1 | 1 | 0.0833793 | -1.15928 |
| e_al_emax_gpa | 61.462 | 1 | 1 | 0.0921823 | -1.15928 |
| e_al_emax_gpa | 62.462 | 1 | 1 | 0.0855055 | -1.15928 |
| e_al_emax_gpa | 63.462 | 1 | 1 | 0.0650829 | -1.15928 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `seed_size_robustness`
- Estimated run count: `9`
- Reason: p95=587 MPa is inside Zhang's 572-638 MPa endpoint window and the force-chain trend candidate passes, so hold the best mu/E pair fixed and validate robustness across seeds and diamond size cases

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"C\", \"D\", \"E\"]",
  "e_al_emax_sweep_json": "[\"63.462\"]",
  "mu_scale_json": "[\"0.654\"]",
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
