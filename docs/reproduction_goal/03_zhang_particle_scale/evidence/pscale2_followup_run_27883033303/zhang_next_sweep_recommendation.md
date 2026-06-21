# Zhang Next Sweep Recommendation

- Status: `ready`
- Selected artifact: `dia60al40-dem-artifacts-sizeC-pscale2-Emax63.462-mu0.654-seed2`
- Diagnosis: `candidate_pass`
- Pressure target: `600 MPa`
- Estimated light runs: `9`

## Reason

p95=587 MPa is inside Zhang's 572-638 MPa endpoint window and the force-chain trend candidate passes, so hold the best mu/E pair fixed and validate robustness across seeds and diamond size cases

## Workflow Dispatch Inputs

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"C\", \"D\", \"E\"]",
  "e_al_emax_sweep_json": "[\"63.462\"]",
  "mu_scale_json": "[\"0.654\"]",
  "runtime_profile": "demo"
}
```

## Follow-up

If the seed/size matrix remains inside the pressure window with Zhang pass trends, promote the parameter pair to the next fidelity upgrade instead of broadening the light calibration sweep.
