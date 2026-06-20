# Zhang Next Sweep Recommendation

- Status: `ready`
- Selected artifact: `dia60al40-dem-artifacts-sizeE-pscale2-Emax63.559-mu0.693-seed2`
- Diagnosis: `needs_participation_increase`
- Pressure target: `600 MPa`
- Estimated light runs: `6`

## Reason

p95=480 MPa is below Zhang's 572-638 MPa endpoint window, so sweep higher Al endpoint modulus; strong-force participation still decreases, so bracket friction scale around the current run

## Workflow Dispatch Inputs

```json
{
  "dem_seed_json": "[\"2\"]",
  "diamond_size_case_json": "[\"E\"]",
  "e_al_emax_sweep_json": "[\"95.338\", \"79.449\"]",
  "mu_scale_json": "[\"0.485\", \"0.693\", \"0.901\"]",
  "runtime_profile": "demo"
}
```

## Follow-up

If any candidate reaches Zhang pass trends, rerun the best mu/E pair with dem_seed_json=["0","1","2"] and diamond_size_case_json=["C","D","E"].
