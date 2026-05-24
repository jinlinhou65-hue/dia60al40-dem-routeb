# Dia60Al40 DEM Pressure-Density Pipeline

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
py D:\CodexProjects\python\convert_liggghts_csv_to_comsol.py --input D:\CodexProjects\liggghts\DEM\stage5_rho095_<step>.dump --mode 2d --auto-shrink-overlap --output D:\CodexProjects\scripts\comsol_particles.csv
```

GitHub Actions runs the staged DEM deck, verifies every stage, and uploads the stage dumps, restarts, logs, STLs, generated `comsol_particles_stage*.csv` files, and the macro `pressure_density_curve.csv`.

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
