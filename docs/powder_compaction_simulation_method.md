# Powder Compaction Simulation Method

This document is the executable route for the full study target: stress
distribution changes particle contacts, contacts change current and temperature
fields, and those fields affect densification.

## Current Scope

The repository now has two validated layers.

1. Paper-algorithm reproduction: deterministic, solver-neutral tables for
   Zhang, Yuan, Liu, and Li.
2. Real DEM demo: LIGGGHTS-PUBLIC staged compaction on GitHub Actions, followed
   by the same paper metric post-processing and evidence gates.

The current result is a verified feasibility route, not a final calibrated
thesis reproduction. It is ready for controlled fidelity upgrades.

## Backend Route

The current backend decision is documented in
`docs/dem_algorithm_selection.md`.

- Current real-data backend: LIGGGHTS-PUBLIC on ubuntu-22.04 GitHub Actions.
- Reason: it already builds, runs staged die compaction, exports stage data, and
  passes the paper evidence gates in CI.
- Main fallback: LAMMPS GRANULAR package after a deck rewrite and parser proof.
- Research fallback: YADE for rapid Python-driven contact-law experiments.
- Future shape/GPU path: Project Chrono DEM/DEME after CPU evidence is
  calibrated.
- Non-open-source paper tools such as PFC/PFC2D, MSC.MARC, Abaqus, and COMSOL
  are references or optional calibration tools, not required execution
  backends.

## Execution Procedure

### 1. Reproduce the four papers without a DEM solver

Run:

```powershell
py scripts\run_paper_algorithm_reproduction.py `
  --paper all `
  --outdir outputs\paper_algorithm_reproduction
```

This writes:

- Zhang: multiscale contact-force, force-chain, and local-stress
  inhomogeneity metrics.
- Yuan: arch count, length, obstruction, strength, direction, and buckling
  metrics.
- Liu: pressure-density fits plus contact electrical-thermal and
  diffusion-neck metrics.
- Li: coated-powder composition, temperature-pressure, friction, speed, aspect
  ratio, and particle-count convergence metrics.
- Shared outputs: acceptance summary, trend checks, manifest, report, plots,
  and DEM backend selection.

### 2. Validate the paper outputs

Run:

```powershell
py .github\scripts\validate_paper_reproduction_content.py `
  --paper all `
  --outdir outputs\paper_algorithm_reproduction
```

The gate must pass before changing DEM backends. It proves that the paper
schemas, trend checks, PDF anchors, plots, and backend decision are present.

### 3. Run the real DEM stage-series demo in workflow

Use GitHub Actions rather than Windows for the solver:

```powershell
gh workflow run dia60al40-dem.yml `
  -f runtime_profile=demo `
  -f mu_scale_json='["1.0"]' `
  -f dem_seed_json='["0"]' `
  -f diamond_size_case_json='["C"]'
```

The workflow builds LIGGGHTS-PUBLIC, renders the deck, generates meshes, runs
six density stages, exports DEM-FEM handoff CSVs, processes the stage series,
and validates the evidence bundle.

### 4. Convert each DEM stage into paper metrics

The workflow runs this automatically, but the command is:

```powershell
py scripts\process_stage_series.py `
  --snapshot-dir liggghts\DEM `
  --pressure-curve liggghts\DEM\pressure_density_curve.csv `
  --outdir outputs\stage_series `
  --width-um 400
```

For each stage, the post-processor infers:

- particle-particle contacts, gaps, overlaps, normals, and force proxies;
- force-chain and arch candidates;
- conductance, current, Joule heat, particle heat source, and temperature;
- diffusion mechanism, neck ratio, and heat-isolated thermal neck increment;
- paper acceptance rows for Zhang, Yuan, Liu, and Li.

### 5. Validate real DEM evidence

Run:

```powershell
py scripts\validate_dem_evidence.py `
  --dem-dir liggghts\DEM `
  --outdir liggghts\DEM\paper_reproduction
```

The gate proves that the artifact contains real stage dumps, restarts, pressure
curve data, handoff tables, stage-series paper metrics, electrothermal outputs,
and runtime controls.

## Data Contract

Any backend that replaces LIGGGHTS must export or be converted into these
contracts.

| Contract | Required purpose |
|---|---|
| `pressure_density_curve.csv` | macro pressure, target density, actual density, height, and force history |
| `dem_fem_handoff_stage*.csv` | particle id, material, position, radius, stage density, and contact count |
| `series_network_metrics.csv` | Zhang/Yuan/Liu/Li coupled stage metrics |
| `stage_details/*_contacts.csv` | contact graph and normal-force evidence |
| `stage_details/*_arches.csv` | arch-bridge topology evidence |
| `stage_details/*_electrothermal_contacts.csv` | contact conductance, current, and Joule heat |
| `stage_details/*_electrothermal_particles.csv` | particle heat, temperature, diffusion mechanism, and neck growth |
| `dem_evidence_summary.csv` | one-row real-artifact gate result |

## Next Fidelity Upgrades

1. Direct DEM force export: replace overlap-inferred contact-force proxies with
   solver pair forces, contact stress tensors, and fabric tensors.
2. Yuan particle shape: add clumps, superquadrics, polygons, or MPFEM handoff so
   circular, hexagonal, and strip powder trends are geometric rather than proxy
   sweeps.
3. Liu thermal field: solve a real temperature field from Joule heat and add
   calibrated diffusion constants and activation energies.
4. Li core-shell deformation: add MPFEM or FEM handoff for Cu@Fe particles with
   Cu/Fe interface friction, plasticity, and thermal expansion.
5. Calibration: compare pressure-density endpoints, force-chain images, arch
   topology, density ranking, and temperature attenuation against the PDF
   anchors before claiming one-to-one reproduction.
