# Zhang Sweep Artifact Report

- DEM workflow run: [27882367107](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27882367107)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `3`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 3 | 544.464 | 518.884 | 567.207 | 48.3234 | 0.044606 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax61.962-mu0.654-seed2 | 61.962 | 0.654 | 567.207 | pass | candidate_pass | 0.05 | 2 | 0.052353 | -1.15928 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax65.223-mu0.654-seed2 | 65.223 | 0.654 | 518.884 | pass | candidate_pass | 0.05 | 2 | 0.136583 | -1.15928 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax68.484-mu0.654-seed2 | 68.484 | 0.654 | 547.301 | pass | candidate_pass | 0.05 | 2 | 0.13926 | -1.15928 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 3 | 3 | 0.109399 | -1.15928 |
| particle_count_scale | 2 | 3 | 3 | 0.109399 | -1.15928 |
| mu_scale | 0.654 | 3 | 3 | 0.109399 | -1.15928 |
| e_al_emax_gpa | 61.962 | 1 | 1 | 0.052353 | -1.15928 |
| e_al_emax_gpa | 65.223 | 1 | 1 | 0.136583 | -1.15928 |
| e_al_emax_gpa | 68.484 | 1 | 1 | 0.13926 | -1.15928 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `missing`
- Estimated run count: `6`
- Reason: p95=567 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; a Zhang trend candidate exists, so keep a narrow friction bracket

```json
{
  "dem_seed_json": "[\"2\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"92.943\", \"77.453\"]",
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
