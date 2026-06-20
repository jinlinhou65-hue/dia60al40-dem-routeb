# Zhang Sweep Artifact Report

- DEM workflow run: [27867380830](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27867380830)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `9`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 9 | 669.49 | 510.77 | 787.592 | 276.821 | 0.160421 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.77-seed0 | 41.686 | 0.77 | 632.842 | pass | candidate_pass | 0.1 | 2 | 0.144433 | -1.32046 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.77-seed1 | 41.686 | 0.77 | 532.332 | review | needs_participation_increase | 0.05 | 2 | -0.0298141 | -1.04237 |
| dia60al40-dem-artifacts-sizeC-Emax41.686-mu0.77-seed2 | 41.686 | 0.77 | 510.77 | review | needs_d1_decrease | 2 | 2 | 0.954169 | 0.623926 |
| dia60al40-dem-artifacts-sizeD-Emax41.686-mu0.77-seed0 | 41.686 | 0.77 | 787.592 | review | needs_participation_increase | 0.25 | 2 | -0.0708973 | -0.964074 |
| dia60al40-dem-artifacts-sizeD-Emax41.686-mu0.77-seed1 | 41.686 | 0.77 | 756.278 | review | needs_participation_increase | 1 | 2 | -0.127762 | -0.646442 |
| dia60al40-dem-artifacts-sizeD-Emax41.686-mu0.77-seed2 | 41.686 | 0.77 | 748.198 | pass | candidate_pass | 0.1 | 2 | 0.0903001 | -0.627505 |
| dia60al40-dem-artifacts-sizeE-Emax41.686-mu0.77-seed0 | 41.686 | 0.77 | 754.247 | pass | candidate_pass | 0.75 | 2 | 0.0988269 | -0.318278 |
| dia60al40-dem-artifacts-sizeE-Emax41.686-mu0.77-seed1 | 41.686 | 0.77 | 727.172 | pass | candidate_pass | 0.1 | 2 | 0.037351 | -0.955001 |
| dia60al40-dem-artifacts-sizeE-Emax41.686-mu0.77-seed2 | 41.686 | 0.77 | 575.977 | pass | candidate_pass | 0.1 | 2 | 0.0187333 | -0.962857 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 3 | 1 | 0.356263 | -0.579634 |
| diamond_size_case | D | 3 | 1 | -0.0361197 | -0.746007 |
| diamond_size_case | E | 3 | 3 | 0.0516371 | -0.745379 |
| mu_scale | 0.77 | 9 | 5 | 0.123927 | -0.69034 |
| e_al_emax_gpa | 41.686 | 9 | 5 | 0.123927 | -0.69034 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Estimated run count: `9`
- Reason: p95=576 MPa is inside Zhang's 572-638 MPa endpoint window and the force-chain trend candidate passes, so hold the best mu/E pair fixed and validate robustness across seeds and diamond size cases

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"C\", \"D\", \"E\"]",
  "e_al_emax_sweep_json": "[\"41.686\"]",
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
