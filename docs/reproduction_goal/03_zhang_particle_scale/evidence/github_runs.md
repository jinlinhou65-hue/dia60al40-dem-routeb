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

## pscale=2 Recalibration

| Workflow | Run | Status | Commit |
|---|---:|---|---|
| `zhang-pscale2-recalibration.yml` | [27882364909](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27882364909) | success | `37a9326` |

| DEM run | Artifact id | Artifact digest | Imported directory |
|---:|---:|---|---|
| [27882367107](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27882367107) | `7768483523` | `sha256:19f0d38f9dea517eaa57f6a9c3de7c8d8655bdcfce08cd4a96ba27a97d7134ff` | `evidence/pscale2_recalibration_run_27882367107/` |
| [27882368312](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27882368312) | `7768478594` | `sha256:b9f010164e668380564bd4af2e17a196bf3a6f7781dcb461c119dc40f5f92a16` | `evidence/pscale2_recalibration_run_27882368312/` |
| [27882369414](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27882369414) | `7768477174` | `sha256:6d2775c456c9c4825d82385deea40de7e0c4c16d800df6c1ddde5d801e3a6a0a` | `evidence/pscale2_recalibration_run_27882369414/` |

## pscale=2 Follow-up

| Workflow | Run | Status | Commit |
|---|---:|---|---|
| `zhang-pscale2-followup.yml` | [27883030240](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27883030240) | success | `17302ff` |

| Size | DEM run | Artifact id | Artifact digest | Imported directory |
|---|---:|---:|---|---|
| C | [27883033303](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27883033303) | `7768674921` | `sha256:d3159abb6f033b131fcbf49359bbb0fddce40c1c1b06a4107587342edf0ff69f` | `evidence/pscale2_followup_run_27883033303/` |
| D | [27883034434](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27883034434) | `7768668597` | `sha256:4a9e5795cbf18925bff643aaa50cd86436eb0ff9eada7b6602fea390dece09dc` | `evidence/pscale2_followup_run_27883034434/` |
| E | [27883035658](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27883035658) | `7768669712` | `sha256:b2660a8899b38587c543cb03dd5d4b5d88fd86bc9b654fa47cb9d13f16039b3c` | `evidence/pscale2_followup_run_27883035658/` |

## pscale=2 C Seed Recheck

| Workflow | Run | Status | Commit |
|---|---:|---|---|
| `zhang-pscale2-c-seed-recheck.yml` | [27898768547](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27898768547) | success | `3d3e7cc` |

| DEM run | Artifact id | Artifact digest | Imported directory |
|---:|---:|---|---|
| [27898770533](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27898770533) | `7773522783` | `sha256:d1c03fdba2ce58c7509d7f13bd5066f045c440acd8691af14df443bbd0fc740e` | `evidence/pscale2_c_seed_recheck_run_27898770533/` |

## pscale=2 C Pressure-Lift Recheck

| Workflow | Run | Status | Commit |
|---|---:|---|---|
| `zhang-pscale2-c-pressure-lift-recheck.yml` | [28709922833](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/28709922833) | success | `bd38196` |

| DEM run | Artifact id | Artifact digest | Imported directory |
|---:|---:|---|---|
| [28709925303](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/28709925303) | `8082751629` | `sha256:6cde0e89856c6fd3be2808d182053cf64a4ea5ae198526898344819bf6232b27` | `evidence/pscale2_c_pressure_lift_recheck_run_28709925303/` |

## Imported Artifact

Each run imported the `dia60al40-dem-ensemble-summary` artifact through
`scripts/import_zhang_sweep_artifact.py`. The combined 2x summary is stored in:

`data/combined_2x_27875950305_27875951506_27875952754/`

The interpreted 1x vs 2x comparison is stored in:

- `data/1x_vs_2x_comparison.csv`
- `data/zhang_particle_scale_acceptance.csv`
- `report.md`

The interpreted pscale=2 recalibration result is stored in:

- `data/pscale2_recalibration_candidates.csv`
- `data/pscale2_recalibration_size_summary.csv`
- `data/pscale2_recalibration_acceptance.csv`
- `data/pscale2_recalibration_summary.json`
- `figures/pscale2_recalibration_p95.png`
- `pscale2_recalibration_report.md`

The interpreted pscale=2 follow-up result is stored in:

- `data/pscale2_followup_candidates.csv`
- `data/pscale2_followup_size_summary.csv`
- `data/pscale2_followup_acceptance.csv`
- `data/pscale2_followup_summary.json`
- `figures/pscale2_followup_p95.png`
- `pscale2_followup_report.md`

The interpreted pscale=2 C seed recheck result is stored in:

- `data/pscale2_c_seed_recheck_candidates.csv`
- `data/pscale2_c_seed_recheck_acceptance.csv`
- `data/pscale2_c_seed_recheck_summary.json`
- `figures/pscale2_c_seed_recheck_p95.png`
- `pscale2_c_seed_recheck_report.md`

The interpreted pscale=2 C pressure-lift result is stored in:

- `data/pscale2_c_pressure_lift_candidates.csv`
- `data/pscale2_c_pressure_lift_paired.csv`
- `data/pscale2_c_pressure_lift_acceptance.csv`
- `data/pscale2_c_pressure_lift_summary.json`
- `figures/pscale2_c_pressure_lift_paired.png`
- `pscale2_c_pressure_lift_report.md`
