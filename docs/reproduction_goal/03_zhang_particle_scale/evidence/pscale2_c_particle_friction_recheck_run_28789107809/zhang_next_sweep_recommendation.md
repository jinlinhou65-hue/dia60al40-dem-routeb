# Zhang Next Sweep Recommendation

- Status: `ready`
- Selected artifact: `dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-wallmu1-seed4-settle1-vel50`
- Diagnosis: `candidate_pass`
- Pressure target: `600 MPa`
- Estimated light runs: `6`

## Reason

p95=434 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; a Zhang trend candidate exists, so keep a narrow friction bracket

## Workflow Dispatch Inputs

```json
{
  "dem_seed_json": "[\"4\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"108.871\", \"100.314\"]",
  "mu_scale_json": "[\"0.589\", \"0.654\", \"0.719\"]",
  "mu_wall_scale_json": "[\"1\"]",
  "runtime_profile": "demo"
}
```

## Follow-up

If any candidate reaches Zhang pass trends, rerun the best mu/E pair with dem_seed_json=["0","1","2"] and diamond_size_case_json=["C","D","E"].
