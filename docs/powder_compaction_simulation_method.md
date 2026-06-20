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
This is the preferred first validation path on Windows machines; WSL2 becomes
useful after the workflow is green and parameter iteration needs local
Linux-style solver runs.

### 3a. Run the current Zhang recommended robustness sweep

The Zhang calibration ensemble writes a machine-readable next sweep. After run
`27866838829`, one candidate, `Emax=41.686` GPa and `mu_scale=0.77`,
hits the Zhang 572-638 MPa endpoint window with Zhang force-chain trend
`pass`. The current dispatcher therefore holds that best pair fixed and checks
seed/size robustness:

```text
e_al_emax_sweep_json=["41.686"]
mu_scale_json=["0.77"]
dem_seed_json=["0","1","2"]
diamond_size_case_json=["C","D","E"]
runtime_profile=demo
```

Use the small dispatcher workflow when you want GitHub Actions to launch that
matrix without editing the DEM workflow:

```powershell
gh workflow run zhang-recommended-sweep.yml
```

That dispatcher validates the JSON lists, confirms the run count is 9, and then
dispatches `dia60al40-dem.yml` on the same branch. The resulting DEM workflow
still builds LIGGGHTS-PUBLIC, runs the staged compaction cases, aggregates the
ensemble, and uploads the normal `dia60al40-dem-ensemble-summary` artifact.
For this robustness sweep the dispatcher sets `allow_evidence_mismatch=true`:
complete samples that miss a paper-trend gate are still uploaded and aggregated,
while missing evidence remains a hard failure. This keeps the workflow useful as
a robustness map instead of hiding non-passing seed/size cases.
The earlier two 6-job calibration sweeps were verified by
`zhang-recommended-sweep` runs `27859253983` and `27866837375`, which dispatched
`dia60al40-dem` runs `27859255390` and `27866838829`; the second imported
result shows `Emax=41.686` GPa, `mu_scale=0.77`, P95 `632.842 MPa`, and Zhang
trend `pass`. That is why the current default matrix has moved from calibration
to robustness validation.
That robustness validation was run as `dia60al40-dem` run `27867380830`: the
workflow completed successfully with 9 DEM jobs and the aggregate artifact, but
the global `Emax=41.686`/`mu_scale=0.77` pair is not scientifically robust.
Only 5/9 rows pass the Zhang trend gate, and only 2/9 both pass and fall inside
the 572-638 MPa endpoint window. The next calibration step should therefore be
size-specific rather than another global seed/size matrix. The imported
recommendation now expands into three independent dispatch payloads:

```powershell
gh workflow run zhang-size-specific-sweep.yml
```

That workflow reads
`docs/zhang_sweep_evidence/run_27867380830/zhang_next_sweep_recommendation.json`,
dry-runs the plan, verifies that it expands to 3 payloads and 36 total light DEM
jobs, then dispatches `dia60al40-dem.yml` once per size case. C raises the
endpoint modulus, D lowers endpoint modulus and friction, and E lowers endpoint
modulus with a narrow friction bracket. The DEM workflow keeps push demo runs
cancelable, but manual dispatch runs use a per-run concurrency group so the
three size-specific sweeps do not cancel each other.

### 3b. Import the Zhang sweep artifact into versioned evidence

After a recommended sweep finishes, import its `dia60al40-dem-ensemble-summary`
artifact into `docs/zhang_sweep_evidence/run_<run_id>/`:

```powershell
gh workflow run zhang-sweep-artifact-report.yml `
  -f dem_run_id=27859255390
```

If `dem_run_id` is omitted, the workflow selects the latest successful
`workflow_dispatch` run of `dia60al40-dem.yml` on the same branch. It downloads
the ensemble summary artifact using `GITHUB_TOKEN`, runs
`scripts/import_zhang_sweep_artifact.py`, and commits a compact Markdown/CSV/JSON
evidence bundle back to the branch. This closes the loop from "workflow ran" to
"sweep result is readable in the repository."
On feature branches, run this importer manually or by pushing its workflow file;
after the workflow lands on the repository default branch, the `workflow_run`
trigger imports successful `dia60al40-dem.yml` runs automatically. Either path
keeps the evidence in the repository instead of leaving it only as a downloadable
artifact.
The imported evidence for the two calibration runs is stored in
`docs/zhang_sweep_evidence/run_27859255390/` and
`docs/zhang_sweep_evidence/run_27866838829/`. The imported robustness evidence
is stored in `docs/zhang_sweep_evidence/run_27867380830/`.

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

- particle-particle contacts, gaps, overlaps, normals, and direct solver contact
  forces exported from LIGGGHTS `compute pair/gran/local`;
- virial stress tensor components and fabric tensor anisotropy;
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
If direct LIGGGHTS contact forces are complete, the gate allows Zhang's
contact-participation and D1 monotonic checks to remain `review` in the reduced
demo rather than falsely marking them as calibrated paper reproduction.

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

The workflow converts LIGGGHTS `*_contacts_*.local` dumps into direct
contact-force CSVs with `python/export_liggghts_contact_forces.py`, then supplies
them to `process_stage_series.py` with:

```powershell
py scripts\process_stage_series.py `
  --snapshot-dir liggghts\DEM `
  --pressure-curve liggghts\DEM\pressure_density_curve.csv `
  --outdir outputs\stage_series `
  --width-um 400 `
  --contact-dir liggghts\DEM\contact_forces `
  --contact-glob "{stage_id}_contacts.csv"
```

Each direct contact CSV should include `i`, `j`, and either
`normal_force` or `force_x,force_y`. Optional columns are `nx`, `ny`, `gap_um`,
`overlap_um`, and `source`. If no direct file is present for a stage, the
pipeline falls back to overlap-inferred contacts and records
`contact_source=inferred`.
For the lightweight workflow demo, `contact_source=direct` and
`direct_contact_force_fraction=1.0` are required so contact, current,
temperature, and densification proxies are driven by exported solver contacts.

## Next Fidelity Upgrades

1. Yuan particle shape: add clumps, superquadrics, polygons, or MPFEM handoff so
   circular, hexagonal, and strip powder trends are geometric rather than proxy
   sweeps.
2. Liu thermal field: solve a real temperature field from Joule heat and add
   calibrated diffusion constants and activation energies.
3. Li core-shell deformation: add MPFEM or FEM handoff for Cu@Fe particles with
   Cu/Fe interface friction, plasticity, and thermal expansion.
4. Calibration: compare pressure-density endpoints, force-chain images, arch
   topology, density ranking, and temperature attenuation against the PDF
   anchors before claiming one-to-one reproduction.
