# Zhang Sweep Artifact Report

- DEM workflow run: [27874059503](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874059503)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `12`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 12 | 601.89 | 525.814 | 658.477 | 132.662 | 0.0730697 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.654-seed0 | 41.686 | 0.654 | 556.016 | review | needs_participation_increase | 0.05 | 2 | -0.215443 | -0.986791 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.654-seed1 | 41.686 | 0.654 | 525.814 | review | needs_participation_increase | 0.1 | 2 | -0.0126537 | -0.773635 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.654-seed2 | 41.686 | 0.654 | 558.685 | pass | candidate_pass | 0.05 | 2 | 0.305067 | -1.26129 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.885-seed0 | 41.686 | 0.885 | 549.872 | pass | candidate_pass | 0.25 | 2 | 0.207876 | -0.595887 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.885-seed1 | 41.686 | 0.885 | 629.598 | review | needs_d1_decrease | 2 | 2 | 0.926926 | 0.761023 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.885-seed2 | 41.686 | 0.885 | 630.318 | review | needs_participation_increase | 0.75 | 2 | -0.0608832 | -0.187713 |
| dia60al40-dem-artifacts-sizeC-Emax44.772-mu0.654-seed0 | 44.772 | 0.654 | 586.072 | review | needs_participation_increase | 0.05 | 2 | -0.209535 | -0.986791 |
| dia60al40-dem-artifacts-sizeC-Emax44.772-mu0.654-seed1 | 44.772 | 0.654 | 658.477 | review | needs_participation_increase | 0.1 | 2 | -0.0593714 | -0.773635 |
| dia60al40-dem-artifacts-sizeC-Emax44.772-mu0.654-seed2 | 44.772 | 0.654 | 634.203 | pass | candidate_pass | 0.05 | 2 | 0.332003 | -1.26129 |
| dia60al40-dem-artifacts-sizeC-Emax44.772-mu0.885-seed0 | 44.772 | 0.885 | 638.891 | pass | candidate_pass | 0.25 | 2 | 0.158126 | -0.595887 |
| dia60al40-dem-artifacts-sizeC-Emax44.772-mu0.885-seed1 | 44.772 | 0.885 | 633.388 | review | needs_d1_decrease | 1.5 | 2 | 0.899276 | 1.07488 |
| dia60al40-dem-artifacts-sizeC-Emax44.772-mu0.885-seed2 | 44.772 | 0.885 | 621.348 | review | needs_participation_increase | 0.5 | 2 | -0.166689 | -0.187713 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 12 | 4 | 0.175392 | -0.481227 |
| mu_scale | 0.654 | 6 | 2 | 0.0233445 | -1.00724 |
| mu_scale | 0.885 | 6 | 2 | 0.327439 | 0.0447836 |
| e_al_emax_gpa | 41.686 | 6 | 2 | 0.191815 | -0.507382 |
| e_al_emax_gpa | 44.772 | 6 | 2 | 0.158968 | -0.455073 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `seed_size_robustness`
- Estimated run count: `9`
- Reason: p95=634 MPa is inside Zhang's 572-638 MPa endpoint window and the force-chain trend candidate passes, so hold the best mu/E pair fixed and validate robustness across seeds and diamond size cases

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"C\", \"D\", \"E\"]",
  "e_al_emax_sweep_json": "[\"44.772\"]",
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
