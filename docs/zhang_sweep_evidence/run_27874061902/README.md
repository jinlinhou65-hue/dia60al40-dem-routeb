# Zhang Sweep Artifact Report

- DEM workflow run: [27874061902](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874061902)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `12`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 12 | 588.477 | 479.676 | 686.995 | 207.318 | 0.113038 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeD-Emax32.737-mu0.539-seed0 | 32.737 | 0.539 | 488.322 | review | needs_d1_decrease | 2 | 2 | 0.950133 | 0.576402 |
| dia60al40-dem-artifacts-sizeD-Emax32.737-mu0.539-seed1 | 32.737 | 0.539 | 542.494 | review | needs_participation_increase | 0.5 | 2 | -0.0421536 | -0.741289 |
| dia60al40-dem-artifacts-sizeD-Emax32.737-mu0.539-seed2 | 32.737 | 0.539 | 622.54 | review | needs_participation_increase | 0.25 | 2 | -0.0956068 | -0.611134 |
| dia60al40-dem-artifacts-sizeD-Emax32.737-mu0.77-seed0 | 32.737 | 0.77 | 547.13 | review | needs_participation_increase | 0.25 | 2 | -0.0608373 | -0.964074 |
| dia60al40-dem-artifacts-sizeD-Emax32.737-mu0.77-seed1 | 32.737 | 0.77 | 629.009 | review | needs_participation_increase | 1 | 2 | -0.167077 | -0.646442 |
| dia60al40-dem-artifacts-sizeD-Emax32.737-mu0.77-seed2 | 32.737 | 0.77 | 479.676 | pass | candidate_pass | 0.1 | 2 | 0.210019 | -0.627505 |
| dia60al40-dem-artifacts-sizeD-Emax37.517-mu0.539-seed0 | 37.517 | 0.539 | 546.823 | review | needs_d1_decrease | 2 | 2 | 0.940773 | 0.584357 |
| dia60al40-dem-artifacts-sizeD-Emax37.517-mu0.539-seed1 | 37.517 | 0.539 | 610.439 | review | needs_participation_increase | 0.5 | 2 | -0.00469086 | -0.741289 |
| dia60al40-dem-artifacts-sizeD-Emax37.517-mu0.539-seed2 | 37.517 | 0.539 | 686.995 | review | needs_participation_increase | 0.25 | 2 | -0.115479 | -0.611134 |
| dia60al40-dem-artifacts-sizeD-Emax37.517-mu0.77-seed0 | 37.517 | 0.77 | 620.518 | review | needs_participation_increase | 0.25 | 2 | -0.00649517 | -0.964074 |
| dia60al40-dem-artifacts-sizeD-Emax37.517-mu0.77-seed1 | 37.517 | 0.77 | 667.204 | review | needs_participation_increase | 0.75 | 2 | -0.120834 | -0.685699 |
| dia60al40-dem-artifacts-sizeD-Emax37.517-mu0.77-seed2 | 37.517 | 0.77 | 620.578 | pass | candidate_pass | 0.1 | 2 | 0.146838 | -0.627505 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | D | 12 | 2 | 0.136216 | -0.504949 |
| mu_scale | 0.539 | 6 | 0 | 0.272163 | -0.257348 |
| mu_scale | 0.77 | 6 | 2 | 0.000268824 | -0.75255 |
| e_al_emax_gpa | 32.737 | 6 | 1 | 0.132413 | -0.502341 |
| e_al_emax_gpa | 37.517 | 6 | 1 | 0.140019 | -0.507557 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `seed_size_robustness`
- Estimated run count: `9`
- Reason: p95=621 MPa is inside Zhang's 572-638 MPa endpoint window and the force-chain trend candidate passes, so hold the best mu/E pair fixed and validate robustness across seeds and diamond size cases

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"C\", \"D\", \"E\"]",
  "e_al_emax_sweep_json": "[\"37.517\"]",
  "mu_scale_json": "[\"0.77\"]",
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
