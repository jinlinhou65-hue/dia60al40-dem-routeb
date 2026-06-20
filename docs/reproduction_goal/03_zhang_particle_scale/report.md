# Zhang 2x Particle-Scale Interpretation

## Conclusion

Do not launch 4x yet. The 2x DEM runs are complete, but P95 pressures fall below the 572-638 MPa Zhang endpoint window; recalibrate endpoint modulus/loading/contact parameters at pscale=2 first.

The `particle_count_scale=2` C/D/E runs prove the workflow and verifier path are usable, but they do not preserve the Zhang endpoint pressure calibration from the 1x size-specific sweep. This stage should therefore remain `review` until pscale=2 is recalibrated.

## 1x vs 2x Comparison

| Size | 1x P95 MPa | 2x P95 MPa | Delta MPa | Delta % | 2x Status | 2x Diagnosis |
|---|---:|---:|---:|---:|---|---|
| C | 634.203 | 411.866 | -222.337 | -35.06% | pass | candidate_pass |
| D | 620.578 | 413.405 | -207.173 | -33.38% | review | needs_participation_increase |
| E | 604.217 | 371.868 | -232.349 | -38.45% | review | needs_participation_increase |

## Acceptance

| Size | Artifact | Workflow | Pressure Window | Trend | Overall | Decision |
|---|---|---|---|---|---|---|
| C | pass | pass | review | pass | review | rerun_with_higher_endpoint_pressure |
| D | pass | pass | review | review | review | recalibrate_before_4x |
| E | pass | pass | review | review | review | recalibrate_before_4x |

## Files

- `data/combined_2x_27875950305_27875951506_27875952754/combined_best_by_run.csv`
- `data/combined_2x_27875950305_27875951506_27875952754/combined_size_summary.csv`
- `data/1x_vs_2x_comparison.csv`
- `data/zhang_particle_scale_acceptance.csv`
- `figures/p95_1x_vs_2x.png`
- `figures/p95_delta_percent.png`

## Reading Notes

- The 2x runs are complete and suitable as evidence that particle refinement runs in workflow.
- The pressure gate is not met because all three 2x P95 values are below 572 MPa.
- C keeps the Zhang force-chain trend gate as `pass`; D and E need participation-increase recalibration.
- The next physical action is pscale=2 recalibration, not 4x/8x scaling.

## Next Recalibration Matrix

The next workflow is `zhang-pscale2-recalibration.yml`. It keeps pscale, seed,
and friction fixed, and only sweeps endpoint modulus around the value predicted
by `current_Emax * 600 / current_2x_P95`.

| Size | Emax candidates GPa | Mu | Purpose |
|---|---|---:|---|
| C | `61.962, 65.223, 68.484` | 0.654 | Recover pressure while preserving pass trend |
| D | `51.728, 54.451, 57.173` | 0.770 | Recover pressure before friction/contact tuning |
| E | `57.506, 60.533, 63.559` | 0.693 | Recover pressure before friction/contact tuning |

This is intentionally a 9-job pressure-first sweep. It should not be expanded to
4x/8x until the imported pscale=2 recalibration result proves C/D/E can return
to the 572-638 MPa endpoint window.
