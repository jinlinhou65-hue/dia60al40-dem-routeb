# Zhang Next Sweep Recommendation

- Status: `needs_calibration`
- Selected artifact: `dia60al40-dem-artifacts-sizeC-pscale2-Emax72.581-mu0.654-seed2`
- Diagnosis: `candidate_pass`
- Pressure target: `600 MPa`
- Estimated light runs: `20`

## Reason

only 2/5 seed/size rows both pass Zhang trend gates and fall inside the 572-638 MPa endpoint window, so one global mu/E pair is not robust

## Workflow Dispatch Inputs

```json
{}
```

## Workflow Dispatch Plan

### Size `C`

- Estimated runs: `20`
- Pressure action: mean endpoint pressure is inside Zhang window; keep a narrow endpoint modulus bracket
- Trend action: size case has mixed trend gates; bracket friction around the current value

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\", \"3\", \"4\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"68.952\", \"76.21\"]",
  "mu_scale_json": "[\"0.556\", \"0.752\"]",
  "runtime_profile": "demo"
}
```

## Follow-up

Run separate size-case calibration sweeps instead of repeating the same global seed/size matrix: C needs higher-pressure stabilization, while D/E need lower-pressure brackets or a particle-size dependent contact-law fit.
