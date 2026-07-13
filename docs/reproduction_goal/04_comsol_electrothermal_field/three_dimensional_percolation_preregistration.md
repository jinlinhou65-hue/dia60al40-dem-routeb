# Stage 04 True-3D Electrical-Percolation Preregistration

## Frozen Question

Can a true three-dimensional, direct LIGGGHTS particle-contact graph form an electrically active
path between the bottom and top electrodes? This question is evaluated before Al oxide-resistance
calibration because a precise edge resistance is not interpretable when no electrode-spanning
particle path exists.

## Existing Evidence Boundary

- The current route-B deck requests particle `z` and all three `contactPoint` components.
- It also applies `fix zlock ... setforce NULL NULL 0.0` and resets every inserted particle to
  `z=0`, so its physical state is strict quasi-2D.
- The archived Stage 04 handoff and direct-contact CSVs omit particle/contact z.
- Existing 2D nonpercolation and homogenized COMSOL fields remain valid for their documented
  purpose, but cannot answer a 3D percolation question.

## Pilot Controls

The first pilot changes only model dimensionality and the particle count needed to occupy a true
thickness. It must preserve the pinned LIGGGHTS source commit, Hertz/history contact law, material
types, force units, direct `pair/gran/local` evidence, gravity direction, and top-punch loading
semantics. It must not run COMSOL.

Before dispatch, record:

1. domain width, initial/final height, and nonzero thickness in um;
2. Al/diamond counts, radius distribution, material volume fraction, and seed;
3. front/back wall geometry and whether periodic z is disabled;
4. settle/load steps, timestep, expected runtime, and a 10-minute GitHub stop budget;
5. electrode-touch tolerance and electrical active-edge threshold ratios;
6. exact output schema and solver commit.

## Required Data Contract

Particle handoff must include `x_um,y_um,z_um,r_um`; direct contacts must include
`nx,ny,nz`, `force_x,force_y,force_z`, `normal_force`, and
`contact_point_x_um,contact_point_y_um,contact_point_z_um`. Missing z, all-zero z span, inferred
contacts, or a direct-contact completeness fraction below 1.0 is a hard failure.

## Percolation Outputs

- particle and active-edge counts by material pair;
- bottom/top electrode node IDs and definitions;
- connected components and electrode-reachable node counts;
- per threshold, whether a bottom-to-top path exists;
- shortest-resistance path node/edge table, bottleneck contact, and total path resistance when a
  path exists;
- auditable 3D network figure showing materials, electrodes, active edges, and the selected path;
- JSON/CSV gate table and hashes of dump, local contact, handoff, parameters, and solver commit.

## Acceptance Gates

1. `z_span_um > 0` for particles and direct contact points.
2. Every exported particle/contact preserves source IDs and all three components.
3. Only `source=liggghts_pair_gran_local` edges enter the graph.
4. Node/edge counts agree between raw evidence, handoff, and analyzer.
5. Electrode membership is based on particle-surface intersection with frozen geometric tolerance.
6. Percolation is reported at conductance thresholds `1e-12`, `1e-9`, and `1e-6` of the maximum;
   the result may be pass or nonpercolating, but must not be changed by adding inferred edges.
7. Electrical path resistance uses a documented clean-contact/Hertz baseline and remains labeled
   uncalibrated until oxide data are introduced.
8. GitHub workflow completes within the frozen budget and uploads raw plus analyzed evidence.

## Stop Rules

- If the current artifacts are all-zero z, do not reinterpret them as 3D.
- If the true-3D pilot cannot generate the frozen composition within the runtime budget, stop and
  reduce particle count once while preserving volume fractions; do not loosen direct-contact gates.
- If no path exists at all three thresholds, preserve `nonpercolating` and diagnose geometry or
  material connectivity before contact-resistance calibration.
- Do not run the existing six COMSOL loading cases or start Stage 06 during this pilot.
