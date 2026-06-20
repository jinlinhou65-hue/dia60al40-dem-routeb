# Zhang Next Sweep Recommendation

- Status: `ready`
- Selected artifact: `dia60al40-dem-artifacts-sizeD-Emax37.517-mu0.77-seed2`
- Diagnosis: `candidate_pass`
- Pressure target: `600 MPa`
- Estimated light runs: `9`

## Reason

p95=621 MPa is inside Zhang's 572-638 MPa endpoint window and the force-chain trend candidate passes, so hold the best mu/E pair fixed and validate robustness across seeds and diamond size cases

## Workflow Dispatch Inputs

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"C\", \"D\", \"E\"]",
  "e_al_emax_sweep_json": "[\"37.517\"]",
  "mu_scale_json": "[\"0.77\"]",
  "runtime_profile": "demo"
}
```

## Follow-up

If the seed/size matrix remains inside the pressure window with Zhang pass trends, promote the parameter pair to the next fidelity upgrade instead of broadening the light calibration sweep.
