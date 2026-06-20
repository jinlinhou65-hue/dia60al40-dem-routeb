# Zhang 2x GitHub Run Evidence

This file records the GitHub Actions evidence imported into this stage.

## Dispatcher

| Workflow | Run | Status | Commit |
|---|---:|---|---|
| `zhang-scale-pilot.yml` | [27875947935](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27875947935) | success | `6fab730` |

## DEM Runs

| Size | DEM run | Artifact id | Artifact digest | Imported directory |
|---|---:|---:|---|---|
| C | [27875950305](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27875950305) | `7766653550` | `sha256:7ee29be913a99b2aa12621eb24b6ea1dc0573d8a1a6485e51de125a7b1101a52` | `evidence/run_27875950305/` |
| D | [27875951506](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27875951506) | `7766656654` | `sha256:a964a949670fba02fedd3fdc7967bed139bd4ff2e14a8b04e5680e0f1b347269` | `evidence/run_27875951506/` |
| E | [27875952754](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27875952754) | `7766658001` | `sha256:ab83b6ca5aa055eb75fc2583607b276924b99107f70215d25cbef7846f5af558` | `evidence/run_27875952754/` |

## Imported Artifact

Each run imported the `dia60al40-dem-ensemble-summary` artifact through
`scripts/import_zhang_sweep_artifact.py`. The combined 2x summary is stored in:

`data/combined_2x_27875950305_27875951506_27875952754/`

The interpreted 1x vs 2x comparison is stored in:

- `data/1x_vs_2x_comparison.csv`
- `data/zhang_particle_scale_acceptance.csv`
- `report.md`

