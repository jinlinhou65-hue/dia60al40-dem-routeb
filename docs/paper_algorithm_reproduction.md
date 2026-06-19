# Paper Algorithm Reproduction Track

This folder adds a solver-neutral reproduction route for the four powder
compaction papers. It is separate from the existing LIGGGHTS Route-B workflow.
The goal is to reproduce the algorithms, metrics, and data products used by the
papers before binding the study to one DEM executable.

## Why This Track Exists

YADE and LIGGGHTS are both Linux-oriented DEM tools. On Windows they are better
treated as remote or workflow backends. The paper-algorithm layer keeps the
research logic stable:

1. define the quantities each paper needs,
2. generate the expected CSV/JSON outputs,
3. verify trends and correlations,
4. later replace the deterministic proxy data with YADE, PFC, LAMMPS, LIGGGHTS,
   MPFEM, or COMSOL exports.

## Paper Mapping

| Paper | Reproduced Algorithm Layer | Output |
| --- | --- | --- |
| Zhang | DEM contact-force statistics, force-chain strength D1, measurement-circle local stress D2, and wall/particle friction sensitivity | `zhang/zhang_multiscale_metrics.csv`, `zhang/zhang_friction_sensitivity.csv` |
| Yuan | DEM force-chain extraction and arch-bridge morphology metrics, including count, length, obstruction, strength, direction, and buckling trends | `yuan/yuan_arch_bridge_metrics.csv` |
| Liu | Huang/Heckel/Kawakita compaction fits plus contact electrical-thermal-sintering network | `liu/liu_compaction_curve.csv`, `liu/liu_compaction_fits.csv`, `liu/liu_electrothermal_sintering.csv`, `liu/liu_coupling_summary.json` |
| Li | Equivalent core-shell coated-powder sweeps, interface/wall friction, temperature-pressure attenuation, and particle-count convergence | `li/li_coated_powder_sweeps.csv`, `li/li_core_shell_metrics.csv`, `li/li_temperature_pressure_response.csv`, `li/li_particle_count_convergence.csv` |

## Run

Use `py` on Windows because this machine's `python.exe` is the WindowsApps
placeholder. Use `python3` in Linux workflows.

```powershell
py scripts\run_paper_algorithm_reproduction.py `
  --paper all `
  --outdir outputs\paper_algorithm_reproduction
```

Linux:

```bash
python3 scripts/run_paper_algorithm_reproduction.py \
  --paper all \
  --outdir outputs/paper_algorithm_reproduction
```

GitHub Actions:

```powershell
gh workflow run paper-algorithm-reproduction.yml -f paper=all
```

The workflow runs Python syntax checks, unit tests, generates the four paper
outputs, validates the generated content, and uploads
`outputs/paper_algorithm_reproduction/**` as an artifact. The content gate checks
that acceptance summaries, manifest entries, report PDF evidence anchors, plots,
trend checks, Zhang multiscale/friction fields, Liu electrothermal
diffusion-neck fields, and Li core-shell/convergence fields are present and
passing. It also checks the generated DEM backend-selection JSON/Markdown so
the open-source solver route stays explicit. It does not install YADE or
LIGGGHTS.

For real DEM evidence, run `.github/workflows/dia60al40-dem.yml`. That workflow
builds LIGGGHTS, generates `dem_fem_handoff_stage*.csv` and
`pressure_density_curve.csv`, then automatically runs:

```bash
python3 scripts/process_stage_series.py \
  --snapshot-dir liggghts/DEM \
  --pressure-curve liggghts/DEM/pressure_density_curve.csv \
  --outdir liggghts/DEM/paper_reproduction \
  --width-um 400

python3 scripts/validate_dem_evidence.py \
  --dem-dir liggghts/DEM \
  --outdir liggghts/DEM/paper_reproduction
```

The resulting `liggghts/DEM/paper_reproduction/**` files are uploaded with the
normal DEM artifact bundle. `dem_evidence_summary.csv` and
`dem_evidence_report.md` are the CI gate proving that the artifact contains real
stage dumps, restarts, handoff tables, pressure-density data, paper acceptance
outputs, and runtime controls.

The first-pass algorithm run also writes:

- `dem_backend_selection.json`: machine-readable open-source DEM backend
  decision, scored candidates, non-open-source paper-tool boundary, and next
  backend upgrades
- `dem_backend_selection.md`: readable version of the backend selection route;
  the tracked repository copy is `docs/dem_algorithm_selection.md`
- `paper_reproduction_manifest.json`: machine-readable target registry for the
  four papers, including source basis, reproduced algorithms, expected outputs,
  acceptance gates, current backend, and next backend steps
- `paper_reproduction_manifest.md`: human-readable version of the same registry
- `paper_reproduction_report.md`: integrated result report with acceptance
  status, generated figures, per-paper evidence, and next backend steps
- `plots/*.svg`: dependency-free SVG figures for the Zhang, Yuan, Liu, and Li
  reproduction outputs
- `paper_trend_checks.json`: paper-specific trend checks for Zhang, Yuan, Liu,
  and Li
- `paper_acceptance_summary.csv`: one-row-per-paper gate summary
- `paper_acceptance_report.md`: compact Markdown gate report

The PDF-derived source anchors and paper-by-paper method map are documented in
`docs/paper_pdf_reproduction_map.md`. The open-source DEM backend selection is
documented in `docs/dem_algorithm_selection.md`. The same PDF anchors and
backend decision are embedded in `paper_reproduction_manifest.json` and
`paper_reproduction_report.md`.

To regenerate only the manifest:

```powershell
py scripts\generate_paper_reproduction_manifest.py `
  --paper all `
  --outdir outputs\paper_algorithm_reproduction
```

## Process Real Particle Snapshots

When a solver exports a particle snapshot, convert it to a CSV with these
columns:

```text
particle_id,x_um,y_um,r_um,material
```

The existing Route-B `dem_fem_handoff_stage*.csv` already carries compatible
`particle_id`, `x_um`, `y_um`, `r_um`, and `material` fields. Process one stage
with:

```powershell
py scripts\process_particle_snapshot.py `
  --particles liggghts\DEM\dem_fem_handoff_stage5_rho095.csv `
  --outdir outputs\stage5_network `
  --width-um 400 `
  --height-um 120.388289
```

Outputs:

- `contacts_inferred.csv`: inferred particle-particle contacts, gaps, overlaps,
  normals, and normal-force proxy
- `arch_bridges.csv`: strong-contact connected arch-bridge candidates
- `electrothermal_contacts.csv`: contact conductance, current, and Joule heat
- `electrothermal_particles.csv`: particle potential, heat source, temperature,
  diffusion mechanism, growth exponent, neck ratio, and thermal neck increment
- `snapshot_summary.json`: Zhang/Yuan/Liu coupling metrics in one file

This stage bridges the papers: Zhang's stress/contact nonuniformity, Yuan's
arch-bridge structure, and Liu's contact-current-temperature-neck chain can be
computed from the same particle snapshot.

## Process A Full Compaction Stage Series

To reproduce paper figures that evolve with pressure or density, process the
whole stage series:

```powershell
py scripts\process_stage_series.py `
  --snapshot-dir liggghts\DEM `
  --pressure-curve liggghts\DEM\pressure_density_curve.csv `
  --outdir outputs\stage_series `
  --width-um 400 `
  --sintering-law blended `
  --sintering-time-s 1.0 `
  --sintering-rate-scale 1.0
```

Expected outputs:

- `series_network_metrics.csv`: one row per pressure/density stage, including
  contact Gini, participation, D1, D2, arch metrics, and coupling correlations
- `series_compaction_fits.csv` and `series_compaction_fits.json`: Heckel,
  Huang, and Kawakita fitting parameters
- `series_trend_checks.json`: machine-readable paper trend checks with
  `pass`, `review`, `missing`, or `mismatch` status
- `series_acceptance_summary.csv`: one-row-per-paper gate summary
- `series_report.md`: paper-by-paper evidence map for Zhang, Yuan, Liu, and Li
- `dem_evidence_summary.csv`: one-row gate summary for a complete real DEM
  artifact
- `dem_evidence_report.md`: detailed file, stage, curve, paper, and runtime
  evidence table
- `stage_details/*_contacts.csv` and `stage_details/*_arches.csv`: per-stage
  inferred contacts and arch candidates
- `stage_details/*_electrothermal_contacts.csv` and
  `stage_details/*_electrothermal_particles.csv`: per-stage current, Joule heat,
  temperature, diffusion mechanism, neck ratio, and heat-isolated neck-growth
  increment outputs

This is the current bridge from Route-B DEM artifacts to the four-paper
reproduction program: it tracks stress/contact nonuniformity, arch formation,
electrical/thermal transport, and density-related compaction fits in one
repeatable command. Trend mismatches are useful: they identify which modeling
assumption to inspect next rather than silently declaring reproduction success.

## Acceptance Gates

| Paper | First Gate |
| --- | --- |
| Zhang | pressure and relative density increase while Gini, D1, and D2 decrease; wall and particle friction raise inhomogeneity |
| Yuan | arch count rises then fluctuates, total length fluctuates, strength growth slows after about 100 MPa, direction remains near 90 degrees, and circular particles show stronger obstruction than low-aspect-ratio strip proxies |
| Liu | compaction fits are produced and contact force/current/heat/diffusion-neck correlations are positive |
| Li | Cu coating and temperature increase predicted density; wall friction and pressing speed reduce it; core-shell density ranking, interface-friction decrease, high-pressure thermal attenuation, and 100/197-particle convergence pass |

This is not the final calibrated DEM/MPFEM solution. It is the reproducible
algorithm scaffold. Once real particle snapshots are available, the same output
schema should be fed by solver exports instead of the deterministic proxy data.
