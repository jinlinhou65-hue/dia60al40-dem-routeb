# Zhang Sweep Artifact Report

- DEM workflow run: [28709925303](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/28709925303)
- Source artifact: `dia60al40-dem-ensemble-summary`
- Artifact id: `8082751629`
- SHA-256 verified: `6cde0e89856c6fd3be2808d182053cf64a4ea5ae198526898344819bf6232b27`
- DEM runs summarized: `5`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 5 | 574.211 | 543.867 | 607.732 | 63.8643 | 0.0395742 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed0 | 72.581 | 0.654 | 573.483 | review | needs_participation_increase | 2 | 2 | -0.000624888 | -0.43069 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed1 | 72.581 | 0.654 | 543.867 | pass | candidate_pass | 0.05 | 2 | 0.0782535 | -1.35961 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed2 | 72.581 | 0.654 | 607.732 | pass | candidate_pass | 0.05 | 2 | 0.0648796 | -1.15928 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed3 | 72.581 | 0.654 | 575.955 | pass | candidate_pass | 0.1 | 2 | 0.0726251 | -0.957276 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed4 | 72.581 | 0.654 | 570.019 | pass | candidate_pass | 0.75 | 3 | 0.302563 | -0.505916 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 5 | 4 | 0.103539 | -0.882553 |
| particle_count_scale | 2 | 5 | 4 | 0.103539 | -0.882553 |
| mu_scale | 0.654 | 5 | 4 | 0.103539 | -0.882553 |
| e_al_emax_gpa | 72.581 | 5 | 4 | 0.103539 | -0.882553 |

## Next Recommendation

- Diagnosis: `candidate_pass`
- Mode: `size_specific_calibration`
- Estimated run count: `20`
- Reason: only 2/5 seed/size rows both pass Zhang trend gates and fall inside the 572-638 MPa endpoint window, so one global mu/E pair is not robust

```json
{}
```

### Size-specific dispatch plan

| Size | Estimated Runs | Pressure Action | Trend Action | Inputs |
|---|---:|---|---|---|
| C | 20 | mean endpoint pressure is inside Zhang window; keep a narrow endpoint modulus bracket | size case has mixed trend gates; bracket friction around the current value | `{"allow_evidence_mismatch": "true", "dem_seed_json": "[\"0\", \"1\", \"2\", \"3\", \"4\"]", "diamond_size_case_json": "[\"C\"]", "e_al_emax_sweep_json": "[\"68.952\", \"76.21\"]", "mu_scale_json": "[\"0.556\", \"0.752\"]", "runtime_profile": "demo"}` |

## Imported Files

- `artifact_verification.json`
- `ensemble_runs.csv`
- `ensemble_pressure_summary.csv`
- `ensemble_pressure_summary_by_size_case.csv`
- `zhang_calibration_candidates.csv`
- `zhang_calibration_best_by_run.csv`
- `zhang_calibration_group_summary.csv`
- `zhang_calibration_ensemble_report.md`
- `zhang_next_sweep_recommendation.json`
- `zhang_next_sweep_recommendation.md`
