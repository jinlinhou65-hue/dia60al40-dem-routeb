# Zhang Next Sweep Recommendation

- Status: `needs_calibration`
- Selected artifact: `dia60al40-dem-artifacts-sizeE-pscale2-Emax96.417-mu0.693-wallmu1-seed3-settle1-vel50`
- Diagnosis: `candidate_pass`
- Pressure target: `600 MPa`
- Estimated light runs: `20`

## Reason

only 3/5 seed/size rows both pass Zhang trend gates and fall inside the 572-638 MPa endpoint window, so one global mu/E pair is not robust

## Workflow Dispatch Inputs

```json
{}
```

## Workflow Dispatch Plan

### Size `E`

- Estimated runs: `20`
- Pressure action: mean endpoint pressure is above Zhang window; lower size-specific endpoint modulus
- Trend action: size case has mixed trend gates; bracket friction around the current value

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\", \"3\", \"4\"]",
  "diamond_size_case_json": "[\"E\"]",
  "e_al_emax_sweep_json": "[\"89.783\", \"86.775\"]",
  "mu_scale_json": "[\"0.589\", \"0.797\"]",
  "mu_wall_scale_json": "[\"1\"]",
  "runtime_profile": "demo"
}
```

## Follow-up

Run separate size-case calibration sweeps instead of repeating the same global seed/size matrix: C needs higher-pressure stabilization, while D/E need lower-pressure brackets or a particle-size dependent contact-law fit.
