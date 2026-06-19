# DEM Backend Selection

This route chooses an open-source DEM backend for the real-data demo while
keeping the paper-reproduction algorithms solver-neutral.

## Decision

- Selected backend: LIGGGHTS-PUBLIC
- Policy: Use LIGGGHTS-PUBLIC for the current real-data CI demo because it is already green in GitHub Actions; keep the paper metric schema solver-neutral so LAMMPS, YADE, MercuryDPM, Chrono DEME, or MPFEM exports can replace it.

## Criteria

| Criterion | Weight |
|---|---:|
| `ci_linux_backend` | 3 |
| `die_compaction_geometry` | 3 |
| `contact_stress_export` | 3 |
| `shape_upgrade_path` | 2 |
| `electrothermal_upgrade_path` | 2 |
| `paper_algorithm_fit` | 3 |
| `windows_remote_fit` | 2 |
| `maintenance_risk` | 2 |

## Candidate Ranking

| Rank | Backend | Role | Score | License | Official source |
|---:|---|---|---:|---|---|
| 1 | LIGGGHTS-PUBLIC | selected primary real-DEM backend | 83 | GPL-2.0-or-later | https://github.com/CFDEMproject/LIGGGHTS-PUBLIC |
| 2 | LAMMPS GRANULAR package | main fallback and future maintained backend | 80 | GPL-2.0-or-later | https://docs.lammps.org/Howto_granular.html |
| 3 | MercuryDPM | C++ candidate for complex industrial particle simulations | 68 | open source | https://www.mercurydpm.org/ |
| 4 | YADE | research backend for custom contact laws and rapid Python studies | 68 | GPL | https://yade-dem.org/doc/ |
| 5 | Project Chrono DEM / DEM-Engine | future GPU/clump backend | 62 | BSD-3-Clause | https://api.projectchrono.org/deme_usage.html |

## LIGGGHTS-PUBLIC

- Role: selected primary real-DEM backend
- Official source: https://github.com/CFDEMproject/LIGGGHTS-PUBLIC

### Source Basis

- Official repository describes LIGGGHTS-PUBLIC as an open-source DEM particle simulation software.
- The current GitHub Actions workflow builds the serial binary on ubuntu-22.04 and reruns staged die compaction.

### Strengths

- Already produces pressure-density stages, restarts, handoff CSVs, and paper evidence in CI.
- Fits the Zhang/Yuan DEM first pass with moving walls, particle contacts, and stage exports.
- Keeps Windows as the editing/review machine while Linux workflow handles solver execution.

### Limitations

- Current route uses spherical particles, so Yuan shape fidelity still needs clumps, polygons, or MPFEM.
- Direct pair-force export is now wired into the stage-series contact contract; next work is calibration and richer particle shape.
- LIGGGHTS-PUBLIC is older; long-term maintenance risk is higher than LAMMPS mainline.

### Paper Fit

- Zhang: primary for stress/contact/force-chain stage series
- Yuan: primary first pass for arch graphs; shape backend still needed
- Liu: geometry/contact source for electrothermal post-processing
- Li: particle handoff source only; core-shell MPFEM remains separate

## LAMMPS GRANULAR package

- Role: main fallback and future maintained backend
- Official source: https://docs.lammps.org/Howto_granular.html

### Source Basis

- LAMMPS granular documentation lists sphere particles, wall/gran fixes, fabric tensors, and heat-flow options.
- pair_style granular supports normal, tangential, rolling, and twisting contact models.

### Strengths

- More actively maintained upstream than LIGGGHTS-PUBLIC.
- Has granular heat conduction hooks and fabric tensor outputs useful for Liu/Zhang metrics.
- Supports clusters, BPM, and superellipsoids for Yuan shape upgrades.

### Limitations

- Requires rewriting the existing LIGGGHTS deck and output parser contracts.
- Mesh-wall and staged die workflow must be reproven in CI before replacing LIGGGHTS.
- Not yet used by this repository's successful workflow artifacts.

### Paper Fit

- Zhang: strong fallback for contact/fabric statistics
- Yuan: good shape upgrade path through clusters or superellipsoids
- Liu: strong thermal-contact upgrade path
- Li: handoff source; core-shell FEM still separate

## MercuryDPM

- Role: C++ candidate for complex industrial particle simulations
- Official source: https://www.mercurydpm.org/

### Source Basis

- MercuryDPM describes itself as open-source code for discrete particle simulations.
- Its documentation highlights complex walls, polydisperse packings, and self-tests across platforms.

### Strengths

- Strong C++ driver model for controlled particle, wall, and interaction setup.
- Cross-platform story is better than YADE/LIGGGHTS for local exploration.
- Useful future candidate if workflow builds become more stable than LIGGGHTS.

### Limitations

- Would require a new driver and new parser interfaces.
- Less directly aligned with the current LIGGGHTS deck and workflow artifacts.
- Electrothermal and core-shell coupling still need custom extension work.

### Paper Fit

- Zhang: possible contact-statistics backend
- Yuan: possible arch backend with custom drivers
- Liu: post-processing source unless custom heat coupling is added
- Li: handoff source only

## YADE

- Role: research backend for custom contact laws and rapid Python studies
- Official source: https://yade-dem.org/doc/

### Source Basis

- YADE documents an extensible open-source DEM framework with C++ computation and Python control.
- Its Python layer is attractive for paper-style metric extraction and algorithm experiments.

### Strengths

- Good for reproducing PFC-like algorithm studies and custom contact laws.
- Python scene construction and post-processing match the current solver-neutral layer.
- Useful for fast experiments before committing to a heavier production backend.

### Limitations

- Windows execution remains awkward, so workflow or Linux VM remains preferred.
- Repository has no passing YADE workflow yet.
- Core-shell MPFEM and calibrated thermal sintering still require extra coupling.

### Paper Fit

- Zhang: good research reproduction of contact-force statistics
- Yuan: good arch and custom shape/contact experiments
- Liu: post-processing source; thermal solve still external
- Li: limited to particle arrangement handoff

## Project Chrono DEM / DEM-Engine

- Role: future GPU/clump backend
- Official source: https://api.projectchrono.org/deme_usage.html

### Source Basis

- Chrono DEM documentation describes GPU granular dynamics through CUDA or HIP.
- DEM-Engine supports clump-represented particles interacting with mesh bodies and analytical boundaries.

### Strengths

- Best long-term path for high-throughput clump or mesh-body granular simulations.
- Permissive license and active Project Chrono ecosystem.
- Attractive for Yuan shape upgrades after the CPU workflow is calibrated.

### Limitations

- GPU requirements do not match the current lightweight GitHub Actions demo.
- Current Chrono DEM docs emphasize mono-disperse spheres in the DEM module; DEME adds clumps but needs a new build path.
- Not necessary until direct-force CPU evidence and paper gates are stable.

### Paper Fit

- Zhang: future acceleration path after metric contracts are stable
- Yuan: strong future clump/shape route
- Liu: possible heat/contact extension path after GPU setup
- Li: handoff source only

## Excluded Non-Open-Source Paper Tools

- PFC/PFC2D, MSC.MARC, Abaqus, and COMSOL are treated as paper references or optional calibration tools, not required open-source backends.

## Next Backend Upgrades

- calibrate direct solver pair-force trends against Zhang force-chain figures and pressure endpoints
- add a shape-capable backend for Yuan particle morphology
- add a thermal field solve and calibrated diffusion constants for Liu
- add MPFEM or FEM handoff for Li core-shell deformation
