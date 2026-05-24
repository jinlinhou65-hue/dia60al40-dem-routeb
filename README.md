# Dia60Al40 DEM → COMSOL Route-B pipeline

## 1. Generate STL meshes

```powershell
py D:\CodexProjects\python\prepare_meshes.py
```

Outputs:

- `D:\CodexProjects\liggghts\meshes\DieBox.stl`
- `D:\CodexProjects\liggghts\meshes\TopPlate.stl`
- `D:\CodexProjects\liggghts\meshes\InsertFace.stl`

All STL coordinates are cgs centimeters. The quasi-2D thickness is `Tcm=0.0090` (slightly larger than the 84 µm DL diameter to give the largest particles geometric headroom against the front/back walls).

## 2. Run staged DEM compaction

```powershell
Set-Location D:\CodexProjects\liggghts
liggghts -in in.dia60al40_dem_staged.liggghts
```

DEM stage dumps and restarts are written to `D:\CodexProjects\liggghts\DEM\`.

The staged workflow separates DEM rearrangement from COMSOL FEM stress analysis:

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

This is the DEM packing target. It is not the Al hardening density used inside COMSOL.

## 3. Verify and export DEM stages to COMSOL CSV

Each stage can be verified directly from the LIGGGHTS custom dump:

```powershell
py D:\CodexProjects\python\verify_dem_stages.py --root D:\CodexProjects\liggghts\DEM
py D:\CodexProjects\python\convert_liggghts_csv_to_comsol.py --input D:\CodexProjects\liggghts\DEM\stage5_rho095_<step>.dump --mode 2d --output D:\CodexProjects\scripts\comsol_particles.csv
```

GitHub Actions runs the staged DEM deck, verifies every stage, and uploads the stage dumps, restarts, logs, STLs, and generated `comsol_particles_stage*.csv` files.

## 4. Run COMSOL Route-B skeleton

```powershell
& "D:\Program Files\COMSOL\COMSOL64\Multiphysics\bin\win64\comsolcompile.exe" D:\CodexProjects\comsol\Dia60Al40_ComsolRouteB_Skeleton.java
& "D:\Program Files\COMSOL\COMSOL64\Multiphysics\bin\win64\comsolbatch.exe" `
  -inputfile D:\CodexProjects\comsol\Dia60Al40_ComsolRouteB_Skeleton.class `
  D:\CodexProjects\scripts\comsol_particles.csv `
  D:\CodexProjects\scripts\Dia60Al40_RouteB_FromDEM.mph
```

Route-B uses displacement control: `uTop = 0 0.2 0.5 1 2 3 5 8 12 16 20 25 30 um`.
