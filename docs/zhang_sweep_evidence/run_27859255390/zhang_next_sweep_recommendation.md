# Zhang Next Sweep Recommendation

- Status: `ready`
- Selected artifact: `dia60al40-dem-artifacts-sizeC-Emax24.174-mu0.7-seed0`
- Diagnosis: `candidate_pass`
- Pressure target: `600 MPa`
- Estimated light runs: `6`

## Reason

p95=348 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; a Zhang trend candidate exists, so keep a narrow friction bracket

## Workflow Dispatch Inputs

```json
{
  "dem_seed_json": "[\"0\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"36.261\", \"41.686\"]",
  "mu_scale_json": "[\"0.63\", \"0.7\", \"0.77\"]",
  "runtime_profile": "demo"
}
```

## Follow-up

If any candidate reaches Zhang pass trends, rerun the best mu/E pair with dem_seed_json=["0","1","2"] and diamond_size_case_json=["C","D","E"].
