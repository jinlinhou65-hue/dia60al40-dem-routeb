# Zhang Next Sweep Recommendation

- Status: `needs_calibration`
- Selected artifact: `dia60al40-dem-artifacts-sizeE-Emax41.686-mu0.77-seed2`
- Diagnosis: `candidate_pass`
- Pressure target: `600 MPa`
- Estimated light runs: `36`

## Reason

only 2/9 seed/size rows both pass Zhang trend gates and fall inside the 572-638 MPa endpoint window, so one global mu/E pair is not robust

## Workflow Dispatch Inputs

```json
{}
```

## Workflow Dispatch Plan

### Size `C`

- Estimated runs: `12`
- Pressure action: mean endpoint pressure is below Zhang window; raise size-specific endpoint modulus
- Trend action: size case has mixed trend gates; bracket friction around the current value

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"C\"]",
  "e_al_emax_sweep_json": "[\"41.686\", \"44.772\"]",
  "mu_scale_json": "[\"0.654\", \"0.885\"]",
  "runtime_profile": "demo"
}
```

### Size `D`

- Estimated runs: `12`
- Pressure action: mean endpoint pressure is above Zhang window; lower size-specific endpoint modulus
- Trend action: mean strong-force participation does not increase; test lower friction scale

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"D\"]",
  "e_al_emax_sweep_json": "[\"32.737\", \"37.517\"]",
  "mu_scale_json": "[\"0.539\", \"0.77\"]",
  "runtime_profile": "demo"
}
```

### Size `E`

- Estimated runs: `12`
- Pressure action: mean endpoint pressure is above Zhang window; lower size-specific endpoint modulus
- Trend action: all seeds pass Zhang trend gates; keep a narrow friction bracket

```json
{
  "allow_evidence_mismatch": "true",
  "dem_seed_json": "[\"0\", \"1\", \"2\"]",
  "diamond_size_case_json": "[\"E\"]",
  "e_al_emax_sweep_json": "[\"36.471\", \"37.517\"]",
  "mu_scale_json": "[\"0.693\", \"0.77\"]",
  "runtime_profile": "demo"
}
```

## Follow-up

Run separate size-case calibration sweeps instead of repeating the same global seed/size matrix: C needs higher-pressure stabilization, while D/E need lower-pressure brackets or a particle-size dependent contact-law fit.
