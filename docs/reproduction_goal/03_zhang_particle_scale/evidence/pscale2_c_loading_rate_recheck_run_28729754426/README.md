# Zhang Sweep Artifact Report

- DEM workflow run: [28729754426](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/28729754426)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `5`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 5 | 578.432 | 545.873 | 628.783 | 82.9102 | 0.0528413 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed0-settle1-vel25 | 72.581 | 0.654 | 628.783 | pass | candidate_pass | 0.05 | 2 | 0.315335 | -1.32671 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed1-settle1-vel25 | 72.581 | 0.654 | 576.16 | pass | candidate_pass | 0.25 | 2 | 0.190464 | -0.676836 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed2-settle1-vel25 | 72.581 | 0.654 | 567.845 | pass | candidate_pass | 0.75 | 2 | 0.0381716 | -0.813828 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed3-settle1-vel25 | 72.581 | 0.654 | 545.873 | pass | candidate_pass | 0.05 | 2 | 0.259518 | -1.22001 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed4-settle1-vel25 | 72.581 | 0.654 | 573.499 | pass | candidate_pass | 0.05 | 2 | 0.125831 | -1.66664 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 5 | 5 | 0.185864 | -1.1408 |
| particle_count_scale | 2 | 5 | 5 | 0.185864 | -1.1408 |
| mu_scale | 0.654 | 5 | 5 | 0.185864 | -1.1408 |
| e_al_emax_gpa | 72.581 | 5 | 5 | 0.185864 | -1.1408 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `size_specific_calibration`
- Estimated run count: `20`
- Reason: only 3/5 seed/size rows both pass Zhang trend gates and fall inside the 572-638 MPa endpoint window, so one global mu/E pair is not robust

```json
{}
```

### Size-specific dispatch plan

| Size | Estimated Runs | Pressure Action | Trend Action | Inputs |
|---|---:|---|---|---|
| C | 20 | mean endpoint pressure is inside Zhang window; keep a narrow endpoint modulus bracket | all seeds pass Zhang trend gates; keep a narrow friction bracket | `{"allow_evidence_mismatch": "true", "dem_seed_json": "[\"0\", \"1\", \"2\", \"3\", \"4\"]", "diamond_size_case_json": "[\"C\"]", "e_al_emax_sweep_json": "[\"68.952\", \"76.21\"]", "mu_scale_json": "[\"0.589\", \"0.654\"]", "runtime_profile": "demo"}` |

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
