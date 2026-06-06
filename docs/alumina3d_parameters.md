# 3D Alumina Compaction Parameters

This workflow models a screening-scale uniaxial DEM compaction of spherical
alumina particles in a cylindrical die.

## Geometry

- Particle material: alumina (`Al2O3`)
- Particle diameter: `30 um`
- Particle count: `2000`
- Die inner diameter: `500 um`
- Initial die height: `700 um`
- Target relative density stages: `0.22`, `0.25`, `0.28`, `0.30`

With 2000 monodisperse spheres of radius 15 um, the solid particle volume is
about `2.827e-5 cm3`. The selected die diameter gives about 16.7 particle
diameters across the die, while the initial height gives a loose bulk insertion
volume fraction near 0.206 so LIGGGHTS can insert all particles robustly before
compaction. The first CI-validated density ladder is deliberately conservative;
after the 2000-particle gate passes, higher final densities can be swept as a
calibration extension.

## Material Values

Dense alumina is recorded with:

- density: `3.95 g/cm3`
- Young's modulus: `365 GPa`
- Poisson ratio: `0.24`

Engineering ceramic tables report alumina density near 3.90 g/cm3, Young's
modulus around 365 GPa, and Poisson ratio around 0.25. Ceramic property tables
also commonly list 99.9% alumina modulus near 380 GPa and Poisson ratio near
0.22.

The DEM deck uses a reduced Hertz stiffness of `0.50 GPa` for the alumina
particles and `5 GPa` for die/punch surfaces. This is intentional: explicit DEM
timesteps scale severely with contact stiffness, and published DEM workflows
often reduce particle stiffness for tractable simulation when the objective is
packing/force-trend screening rather than calibrated contact deformation.

The CI deck uses `98.1 cm/s2` settling gravity, or 0.1 g, to reduce boundary
tunneling risk during small-scale explicit DEM verification. Full-gravity
settling and punch-speed sweeps are left as calibration runs after the
2000-particle geometry gate passes.

Contact parameters are initial screening values:

- particle-particle friction: `0.45`
- particle-wall friction: `0.35`
- particle-particle restitution: `0.35`
- particle-wall restitution: `0.25`

These should be calibrated against angle of repose, die-wall friction, or a
known press curve before treating pressure predictions as quantitative.

## Reproduction Basis

The workflow follows the same broad sequence used in powder compaction DEM
papers:

1. generate die/punch STL geometry,
2. insert a loose particle bed,
3. settle it under gravity,
4. move a top punch through staged displacements,
5. record punch force and relative density,
6. verify final particle count, size, and wall bounds.

The open-access LIGGGHTS/EDEM powder-compaction comparison by
Ramirez-Aragon et al. is the closest implementation guide. It compares EDEM
with LIGGGHTS-PUBLIC, studies cohesive contact models for powder compaction,
and reports that timestep, STL conversion tolerance, and punch speed all affect
accuracy and computational cost. This project starts from the simpler
non-cohesive Hertz-Mindlin route and keeps the cohesive SJKR/SJKR2 extension as
the next calibration step.

The cold uniaxial powder-compaction DEM paper by Rojek et al. supports the
mechanical scope used here: spherical-particle DEM can represent low-pressure
densification mechanisms through particle rearrangement and deformation. This
workflow therefore targets a baseline pressure-density trend, not a calibrated
final ceramic green-body law.

## Sources Used

- Ramirez-Aragon et al., "Comparison of Cohesive Models in EDEM and LIGGGHTS
  for Simulating Powder Compaction", Materials 2018:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6267572/
- Rojek et al., "Discrete element simulation of powder compaction in cold
  uniaxial pressing with low pressure", Computational Particle Mechanics 2016:
  https://www.ippt.pan.pl/repository/open/o3416.pdf
- Bihani and Daigle, "Uniaxial Compaction and Force-chain Analysis of
  Bidisperse Grain Packs", Zenodo software archive with LIGGGHTS scripts:
  https://zenodo.org/records/4021433
- CFDEMproject/LIGGGHTS-PUBLIC official open-source DEM code:
  https://github.com/CFDEMproject/LIGGGHTS-PUBLIC
- LIGGGHTS `fix insert/pack` documentation: target particle-count insertion in
  a defined region is used for the 2000-particle gate.
- Engineering ceramic material-property tables for alumina density, elastic
  modulus, and Poisson ratio.

## Workflow Gate

GitHub Actions runs `.github/workflows/alumina3d-dem.yml`. The gate builds
LIGGGHTS-PUBLIC from source, generates the cylindrical die STL files, renders
the 2000-particle alumina deck, runs the final compaction stage, and verifies
that the final dump still contains exactly 2000 type-1 alumina particles with
30 um diameter inside the die envelope. The workflow is also triggered by
pushes to `main` and `codex/alumina3d-dem-workflow` so prototype repairs rerun
the same verification gate without requiring manual dispatch.
