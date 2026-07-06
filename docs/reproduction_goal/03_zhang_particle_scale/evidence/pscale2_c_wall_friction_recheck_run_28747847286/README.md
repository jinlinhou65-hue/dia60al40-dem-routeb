# Zhang Sweep Artifact Report

- DEM workflow run: [28747847286](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/28747847286)
- Source artifact: `dia60al40-dem-ensemble-summary`
- DEM runs summarized: `10`

## Pressure Ensemble

| Runs | Mean P95 MPa | Min | Max | Range | CV |
|---:|---:|---:|---:|---:|---:|
| 10 | 569.662 | 522.994 | 608.188 | 85.1939 | 0.0464071 |

## Best Zhang Candidate By DEM Run

| Artifact | Emax GPa | Mu | P95 MPa | Status | Diagnosis | Threshold | Min Chain | Participation Delta | D1 Delta |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu0.019113-seed0-settle1-vel50 | 72.581 | 0.654 | 522.994 | pass | candidate_pass | 0.05 | 2 | 0.10007 | -1.33207 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu0.019113-seed1-settle1-vel50 | 72.581 | 0.654 | 567.106 | review | needs_participation_increase | 0.05 | 2 | -0.0166942 | -1.16973 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu0.019113-seed2-settle1-vel50 | 72.581 | 0.654 | 608.188 | review | needs_participation_increase | 0.1 | 2 | -0.231208 | -0.943578 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu0.019113-seed3-settle1-vel50 | 72.581 | 0.654 | 577.42 | pass | candidate_pass | 0.05 | 2 | 0.177781 | -1.08411 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu0.019113-seed4-settle1-vel50 | 72.581 | 0.654 | 549.861 | pass | candidate_pass | 0.05 | 2 | 0.0104483 | -1.16242 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed0-settle1-vel50 | 72.581 | 0.654 | 573.483 | review | needs_participation_increase | 2 | 2 | -0.000624888 | -0.43069 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed1-settle1-vel50 | 72.581 | 0.654 | 543.867 | pass | candidate_pass | 0.05 | 2 | 0.0782535 | -1.35961 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed2-settle1-vel50 | 72.581 | 0.654 | 607.732 | pass | candidate_pass | 0.05 | 2 | 0.0648796 | -1.15928 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed3-settle1-vel50 | 72.581 | 0.654 | 575.955 | pass | candidate_pass | 0.1 | 2 | 0.0726251 | -0.957276 |
| dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed4-settle1-vel50 | 72.581 | 0.654 | 570.019 | pass | candidate_pass | 0.75 | 3 | 0.302563 | -0.505916 |

## Group Summary

| Group | Value | Runs | Pass Runs | Mean Participation Delta | Mean D1 Delta |
|---|---|---:|---:|---:|---:|
| diamond_size_case | C | 10 | 7 | 0.0558094 | -1.01047 |
| particle_count_scale | 2 | 10 | 7 | 0.0558094 | -1.01047 |
| mu_scale | 0.654 | 10 | 7 | 0.0558094 | -1.01047 |
| mu_wall_scale | 0.019113 | 5 | 3 | 0.00807945 | -1.13838 |
| mu_wall_scale | 1.0 | 5 | 4 | 0.103539 | -0.882553 |
| e_al_emax_gpa | 72.581 | 10 | 7 | 0.0558094 | -1.01047 |

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
| C | 20 | mean endpoint pressure is inside Zhang window; keep a narrow endpoint modulus bracket | size case has mixed trend gates; bracket friction around the current value | `{"allow_evidence_mismatch": "true", "dem_seed_json": "[\"0\", \"1\", \"2\", \"3\", \"4\"]", "diamond_size_case_json": "[\"C\"]", "e_al_emax_sweep_json": "[\"68.952\", \"76.21\"]", "mu_scale_json": "[\"0.556\", \"0.752\"]", "mu_wall_scale_json": "[\"1\"]", "runtime_profile": "demo"}` |

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
