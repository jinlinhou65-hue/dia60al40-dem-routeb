# Zhang Sweep Artifact Report

- DEM workflow run: [27874064063](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874064063)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `12`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 12 | 600.834 | 498.327 | 655.389 | 157.062 | 0.0856829 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeE-Emax36.471-mu0.693-seed0 | 36.471 | 0.693 | 498.327 | pass | candidate_pass | 0.1 | 2 | 0.1925 | -1.04422 |
| dia60al40-dem-artifacts-sizeE-Emax36.471-mu0.693-seed1 | 36.471 | 0.693 | 568.412 | review | needs_participation_increase | 0.25 | 2 | -0.140335 | -0.92545 |
| dia60al40-dem-artifacts-sizeE-Emax36.471-mu0.693-seed2 | 36.471 | 0.693 | 562.171 | pass | candidate_pass | 0.05 | 2 | 0.0581953 | -0.760001 |
| dia60al40-dem-artifacts-sizeE-Emax36.471-mu0.77-seed0 | 36.471 | 0.77 | 635.948 | pass | candidate_pass | 0.75 | 2 | 0.105917 | -0.318278 |
| dia60al40-dem-artifacts-sizeE-Emax36.471-mu0.77-seed1 | 36.471 | 0.77 | 638.61 | pass | candidate_pass | 0.1 | 2 | 0.170375 | -0.955001 |
| dia60al40-dem-artifacts-sizeE-Emax36.471-mu0.77-seed2 | 36.471 | 0.77 | 623.451 | pass | candidate_pass | 0.1 | 2 | 0.0203706 | -0.962857 |
| dia60al40-dem-artifacts-sizeE-Emax37.517-mu0.693-seed0 | 37.517 | 0.693 | 540.413 | pass | candidate_pass | 0.1 | 2 | 0.145573 | -1.04422 |
| dia60al40-dem-artifacts-sizeE-Emax37.517-mu0.693-seed1 | 37.517 | 0.693 | 575.26 | review | needs_participation_increase | 0.25 | 2 | -0.129717 | -0.92545 |
| dia60al40-dem-artifacts-sizeE-Emax37.517-mu0.693-seed2 | 37.517 | 0.693 | 604.217 | pass | candidate_pass | 0.05 | 2 | 0.118728 | -0.760001 |
| dia60al40-dem-artifacts-sizeE-Emax37.517-mu0.77-seed0 | 37.517 | 0.77 | 655.389 | pass | candidate_pass | 0.75 | 2 | 0.0627873 | -0.318278 |
| dia60al40-dem-artifacts-sizeE-Emax37.517-mu0.77-seed1 | 37.517 | 0.77 | 652.615 | pass | candidate_pass | 0.1 | 2 | 0.154257 | -0.955001 |
| dia60al40-dem-artifacts-sizeE-Emax37.517-mu0.77-seed2 | 37.517 | 0.77 | 655.19 | review | needs_participation_increase | 0.1 | 2 | -0.00834023 | -0.962857 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | E | 12 | 9 | 0.0625259 | -0.827634 |
| mu_scale | 0.693 | 6 | 4 | 0.040824 | -0.909889 |
| mu_scale | 0.77 | 6 | 5 | 0.0842278 | -0.745379 |
| e_al_emax_gpa | 36.471 | 6 | 5 | 0.0678371 | -0.827634 |
| e_al_emax_gpa | 37.517 | 6 | 4 | 0.0572147 | -0.827634 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `seed_size_robustness`
- Estimated run count: `9`
- Reason: p95=604 MPa is inside Zhang's 572-638 MPa endpoint window and the force-chain trend candidate passes, so hold the best mu/E pair fixed and validate robustness across seeds and diamond size cases

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"C\", \"D\", \"E\"]",
  "e_al_emax_sweep_json": "[\"37.517\"]",
  "mu_scale_json": "[\"0.693\"]",
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
