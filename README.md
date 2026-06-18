# Dia60Al40 DEM Pressure-Density Pipeline

## Recommended Execution Path

Run the DEM solve in GitHub Actions on Linux, not directly on Windows. The
project workflow `.github/workflows/dia60al40-dem.yml` pins `ubuntu-22.04`,
builds LIGGGHTS-PUBLIC from source, runs staged compaction, verifies each stage,
exports pressure-density data, plots the results, runs the paper-reproduction
stage-series post-processing, and uploads artifacts.

Use the repository Actions tab, or run:

```powershell
gh workflow run dia60al40-dem.yml `
  -f mu_scale_json='["1.0"]' `
  -f dem_seed_json='["0"]' `
  -f diamond_size_case_json='["C"]'
```

For a broader ensemble, keep the default inputs or provide JSON lists for
`diamond_size_case_json`, `dem_seed_json`, `mu_scale_json`, and
`e_al_emax_sweep_json`. A successful run must produce:

- `liggghts/DEM/stage0_preload_*.dump` through `stage5_rho095_*.dump`
- `liggghts/DEM/pressure_density_curve.csv`
- `liggghts/DEM/pressure_density_summary.csv`
- `liggghts/DEM/dem_fem_handoff_stage*.csv`
- `liggghts/DEM/plastic_morphology_metrics.csv`
- `liggghts/DEM/plots/*.png`
- `liggghts/DEM/paper_reproduction/series_network_metrics.csv`
- `liggghts/DEM/paper_reproduction/series_acceptance_summary.csv`
- `liggghts/DEM/paper_reproduction/series_report.md`

Windows is still useful for editing scripts, reading artifacts, and optional
post-processing. It is not the preferred place to install or run the DEM solver.

## Paper Algorithm Reproduction Track

This repository also contains a solver-neutral track for reproducing the four
powder-compaction papers without binding the first pass to LIGGGHTS:

```powershell
py scripts\run_paper_algorithm_reproduction.py `
  --paper all `
  --outdir outputs\paper_algorithm_reproduction
```

See `docs/paper_algorithm_reproduction.md`. This track reproduces the paper
algorithms and output schemas first: Zhang's multi-scale inhomogeneity metrics,
Yuan's arch-bridge metrics, Liu's compaction/electrothermal/sintering coupling,
and Li's coated-powder sweep laws. Real YADE/PFC/LAMMPS/LIGGGHTS/MPFEM outputs
can later replace the deterministic proxy data while keeping the same CSV/JSON
contracts.

The matching lightweight workflow is:

```powershell
gh workflow run paper-algorithm-reproduction.yml -f paper=all
```

The first-pass run writes `paper_trend_checks.json`,
`paper_acceptance_summary.csv`, `paper_acceptance_report.md`,
`paper_reproduction_manifest.json`, `paper_reproduction_manifest.md`,
`paper_reproduction_report.md`, and dependency-free `plots/*.svg` figures so
each paper has both an explicit trend-gate result and a readable demo artifact
before any full DEM calibration.

To process a real DEM/FEM handoff snapshot through the paper metrics:

```powershell
py scripts\process_particle_snapshot.py `
  --particles liggghts\DEM\dem_fem_handoff_stage5_rho095.csv `
  --outdir outputs\stage5_network `
  --width-um 400 `
  --height-um 120.388289
```

To process the complete pressure-density stage series:

```powershell
py scripts\process_stage_series.py `
  --snapshot-dir liggghts\DEM `
  --pressure-curve liggghts\DEM\pressure_density_curve.csv `
  --outdir outputs\stage_series `
  --width-um 400
```

The stage-series run also writes `series_trend_checks.json` and
`series_acceptance_summary.csv`, so every paper has a visible pass/review/
missing/mismatch status instead of just raw plots.

The main `dia60al40-dem.yml` workflow now runs this stage-series command
automatically after real DEM handoff tables and `pressure_density_curve.csv`
are generated. The `paper-algorithm-reproduction.yml` workflow remains a fast
solver-free check for the paper algorithms themselves.

## 1. Generate STL Meshes

```powershell
py D:\CodexProjects\python\prepare_meshes.py
```

Outputs:

- `D:\CodexProjects\liggghts\meshes\DieBox.stl`
- `D:\CodexProjects\liggghts\meshes\TopPlate.stl`
- `D:\CodexProjects\liggghts\meshes\InsertFace.stl`

All STL coordinates are cgs centimeters. The quasi-2D thickness is `Tcm=0.0090`.

## 2. Run Staged DEM Compaction

```powershell
Set-Location D:\CodexProjects\liggghts
liggghts -in in.dia60al40_dem_staged.liggghts
```

DEM stage dumps and restarts are written to `D:\CodexProjects\liggghts\DEM\`.

The main result is the 2D DEM pressure-density curve:

```text
liggghts/DEM/pressure_density_curve.csv
```

The curve is based on the top punch reaction recorded by `fix mesh/surface/stress`:

```text
pressure_MPa = |top_force_y_dyne| / (Wcm * Tcm) * 1e-7
```

where `Wcm=0.04` and `Tcm=0.0090`. COMSOL is optional and secondary; the primary conclusion is the pressure needed to reach `rho_total ~= 0.95`.

The staged workflow uses DEM for particle rearrangement, contact-network closure, and macro compaction pressure:

| Stage | Target packing metric | Output prefix |
| --- | ---: | --- |
| 0 | preload, about 0.56 | `stage0_preload_*.dump` |
| 1 | 0.65 | `stage1_rho065_*.dump` |
| 2 | 0.72 | `stage2_rho072_*.dump` |
| 3 | 0.80 | `stage3_rho080_*.dump` |
| 4 | 0.88 | `stage4_rho088_*.dump` |
| 5 | 0.95 | `stage5_rho095_*.dump` |

Here:

```text
rho_total = (Al area + diamond area) / (400 um * current top height)
```

## 3. Verify And Export DEM Results

Each stage can be verified directly from the LIGGGHTS custom dump:

```powershell
py D:\CodexProjects\python\verify_dem_stages.py --root D:\CodexProjects\liggghts\DEM
py D:\CodexProjects\python\export_dem_stage_handoff.py --input D:\CodexProjects\liggghts\DEM\stage5_rho095_<step>.dump --stage-id stage5_rho095 --output D:\CodexProjects\liggghts\DEM\dem_fem_handoff_stage5_rho095.csv
```

GitHub Actions runs the staged DEM deck, verifies every stage, and uploads the stage dumps, restarts, logs, STLs, generated `dem_fem_handoff_stage*.csv` files, plots, and the macro `pressure_density_curve.csv`.

The uploaded pressure curve has columns:

```text
stage_id,target_rho_total,actual_rho_total,current_height_um,
top_displacement_um,top_force_y_dyne,top_force_n,pressure_mpa,
avg_contact_count,max_contact_count,max_overlap_um,worst_overlap_pair
```

Compressed DEM dumps may contain projected 2D particle overlap. In Hertz DEM, that overlap is the elastic contact deformation used to compute contact force; it is not by itself a failed DEM solve. The workflow therefore treats overlap as a reported diagnostic, while particle counts, z-plane locking, and density windows remain hard gates.

The legacy COMSOL geometry CSVs:

```text
liggghts/DEM/comsol_particles_<stage>.csv
```

are geometry-safe files. If projected DEM overlap is present, the converter applies a uniform `radius_shrink_um` just large enough to remove the initial intersections before COMSOL imports the particles.

For each DEM stage the workflow also writes a richer DEM-FEM handoff table:

```text
liggghts/DEM/dem_fem_handoff_<stage>.csv
```

Columns:

```text
stage_id,target_rho_total,actual_rho_total,current_height_um,
particle_id,type,shape,material,x_um,y_um,r_um,
rotation_rad,vx_cm_s,vy_cm_s,contact_count
```

`rotation_rad` is currently `0.0` because the LIGGGHTS model uses spherical DEM particles. The column is included so future clump/superquadric or polygon-orientation output can be passed to COMSOL without changing the handoff schema.

Use `dem_fem_handoff_<stage>.csv` when you need the raw DEM state and contact network. Use `comsol_particles_<stage>.csv` when you need a COMSOL-importable geometry table.

## 4. Optional COMSOL Stage Analysis

COMSOL is no longer the primary route for the pressure-density conclusion. It can still consume selected `comsol_particles_<stage>.csv` files for secondary local-field visualization.
