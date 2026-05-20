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

## 2. Run DEM preload

```powershell
Set-Location D:\CodexProjects\liggghts
liggghts -in in.dia60al40_dem_preload.liggghts
```

DEM VTK frames are written to `D:\CodexProjects\liggghts\DEM\dia60al40_*.vtk` if LIGGGHTS is available.

## 3. Export final DEM state to CSV

Open the largest-step VTK in ParaView and export CSV.

```powershell
py D:\CodexProjects\python\check_dem_state.py --input <last_frame>.csv
py D:\CodexProjects\python\convert_liggghts_csv_to_comsol.py --input <last_frame>.csv --mode 2d --output D:\CodexProjects\scripts\comsol_particles.csv
```

## 4. Run COMSOL Route-B skeleton

```powershell
& "D:\Program Files\COMSOL\COMSOL64\Multiphysics\bin\win64\comsolcompile.exe" D:\CodexProjects\comsol\Dia60Al40_ComsolRouteB_Skeleton.java
& "D:\Program Files\COMSOL\COMSOL64\Multiphysics\bin\win64\comsolbatch.exe" `
  -inputfile D:\CodexProjects\comsol\Dia60Al40_ComsolRouteB_Skeleton.class `
  D:\CodexProjects\scripts\comsol_particles.csv `
  D:\CodexProjects\scripts\Dia60Al40_RouteB_FromDEM.mph
```

Route-B uses displacement control: `uTop = 0 0.2 0.5 1 2 3 5 8 12 16 20 25 30 um`.
