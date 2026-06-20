# PDF-anchored paper reproduction map

This document records the reproducible method extracted from the four user-provided
PDFs. It is intentionally tied to PDF page anchors so later code changes can be
checked against the papers instead of drifting into generic DEM examples.

## Overall route

The selected open solver route is LIGGGHTS-PUBLIC for the real DEM demo, run on
Linux/GitHub Actions. Python is used for deck rendering, post-processing, paper
metrics, and evidence gates. Windows is kept as the editing and artifact review
environment.
The backend choice is tracked in `docs/dem_algorithm_selection.md`:
LIGGGHTS-PUBLIC is the current workflow-proven backend, while LAMMPS, YADE,
MercuryDPM, and Chrono DEM/DEME remain documented upgrade or fallback routes.

The current implemented chain is:

1. Render and run a staged powder compaction DEM deck.
2. Export stage dumps, restarts, pressure-density curve, and DEM-FEM handoff CSVs.
3. Infer contact network, force-chain proxies, arch candidates, electrical current,
   Joule heat, temperature estimate, and diffusion-law neck growth from each stage.
4. Produce one paper-level acceptance table for Zhang, Yuan, Liu, and Li.
5. Validate that a real DEM artifact contains all required stage files and paper
   reproduction evidence.

## Zhang - multiscale mechanical inhomogeneity

PDF anchors:

- p1: the paper studies macro stress, meso force chains, and micro contact-force
  inhomogeneity with Gini, participation, D1, and D2.
- p3: DEM model is 10 mm x 15 mm with 3000 iron particles, diameter 148-296 um,
  mean 222 um, density 7800 kg/m3, E=209 GPa, nu=0.25, friction 0.25, punch
  speed 0.2 m/s, endpoint about 600 MPa; experiment/simulation endpoint is
  572 MPa vs 638 MPa.
- p4: contact-force Gini and participation are defined; force chains require
  force above mean, at least three particles, and an angle threshold based on
  mean coordination.
- p5: local stress is averaged in measurement circles and D2 is the normalized
  standard deviation of local y-stress.

Reproduction method:

- DEM backend: run staged compaction and export particle/contact state.
- Metrics: pressure, density, mean coordination, contact-force mean/std/Gini,
  participation, strong-contact fraction, force-chain count/length/strength/D1,
  measurement-circle local stress mean/std/D2, and wall/particle friction sweeps.
- Gate: pressure/density/participation increase while Gini/D1/D2 decrease; wall
  and particle friction increase inhomogeneity, with particle friction producing
  the stronger micro contact and meso force-chain response.
- Current status: workflow DEM artifacts now export direct LIGGGHTS
  `pair/gran/local` contact forces, which feed the virial stress tensor, fabric
  tensor, force-chain, and electrothermal post-processing. Calibration against
  thesis force-chain images and measured force distributions remains the next
  Zhang-specific step.

## Yuan - arch bridge structure

PDF anchors:

- p18-p19: DEM model is 0.016 m x 0.020 m, initial porosity 0.22, E=80 GPa,
  nu=0.29, friction 0.20, wall stiffness 2e12 N/m, punch speed 2 cm/s, endpoint
  600 MPa; Heckel fit has R2=0.9784.
- p22-p23: MPFEM model uses 160 particles, 300-400 um, Abaqus plane strain,
  0.01 mm mesh, Johnson-Cook material parameters, and 600 MPa endpoint.
- p40-p42: arch criteria and arch metrics are defined: length, strength, buckling
  angle, and direction angle.
- p43-p49: particle shape controls densification and arch evolution; lower AR
  strip powder improves density and lowers arch obstruction.

Reproduction method:

- DEM/MPFEM target: use DEM for particle arrangement and contact graph; use MPFEM
  later when deformable particle shape is required.
- Metrics: arch count, mean length, total length, obstruction index, strength,
  buckling angle, direction angle, and shape-dependent trends.
- Gate: arch count has an interior peak, total length fluctuates, strength growth
  slows after about 100 MPa, direction stays near 90 degrees, circle proxy has
  stronger obstruction than strip proxy, and real stage-series arch outputs exist.
- Current limitation: LIGGGHTS route uses spherical particles; clumps, polygons,
  superquadrics, or MPFEM are needed for exact circle/hexagon/strip reproduction.

## Liu - compaction-sintering coupling

PDF anchors:

- p2: the paper is a cross-scale modelling review covering nonlinear elastic,
  rigid-plastic compressible, and generalized plastic models.
- p4: Huang, Heckel, and Kawakita pressure-density equations are stated.
- p9: compaction microstructure should be passed to sintering as initial density,
  pores, residual stress, and diffusion-path information.
- p11-p14: sintering neck-growth laws are listed for volume diffusion,
  grain-boundary diffusion, surface diffusion, Coble, and Nabarro-Herring routes.
- p14: referenced DEM sintering geometries use relative density milestones
  0.784, 0.836, 0.894, and 0.950.

Reproduction method:

- Compaction: fit Huang, Heckel, and Kawakita equations to pressure-density data.
- Coupling: map normal force to contact conductance/current; map Joule heat and
  temperature to normalized Wilson/Johnson/Kuczynski/Coble/Nabarro-Herring
  diffusion-law neck growth; use heat-isolated neck increment for coupling
  correlation so particle-size effects do not mask the thermal contribution.
- Gate: density rises; Heckel/Kawakita/Huang fits exist; force-current and
  Joule heat-neck correlations are positive.
- Current limitation: diffusion-law exponents and Arrhenius response are now
  explicit, but alloy-specific diffusion constants and true temperature fields
  still need calibration.

## Li - coated Cu@Fe powder densification

PDF anchors:

- p3-p4: Cu20@Fe80 improves stress distribution and densification vs Fe; wall
  friction blocks densification; temperature raises relative density; pressing
  speed lowers density; Cu 20-25 percent gives lower stress and better plasticity;
  diameter-height ratio near 2:1 gives 96.45 percent relative density.
- p41: temperature raises density, but its effect weakens after 500 MPa.
- p49: increasing Cu content reduces Cu/Fe and Cu-wall friction, improving flow.
- p52: PFC2D generates random coordinates at porosity 0.22 and imports them into
  MSC.MARC for multi-particle core-shell FEM.
- p56: 100- and 197-particle models converge after 500 MPa; 197 particles is a
  practical compromise.
- p71: at 600 MPa, density peaks near diameter-height ratio 2:1.

Reproduction method:

- Equivalent model: sweep Cu fraction, temperature, wall friction, pressing speed,
  and aspect ratio using density, stress, flow, interface-friction, and wall-friction
  proxy laws derived from PDF trends.
- Core-shell outputs: composition table for Fe, Cu10@Fe90, Cu20@Fe80, Cu25@Fe75,
  and Cu30@Fe70 with density at 600 MPa, stress uniformity, plastic strain,
  interface friction, wall friction, and flow factor.
- Temperature-pressure outputs: density is computed at 100, 300, 500, and 600 MPa
  across 20-300 C so the high-pressure weakening of the temperature effect is
  explicitly checked.
- Convergence outputs: 100- and 197-particle densities are compared at 300, 500,
  and 600 MPa to reproduce the paper's reduced-model adequacy criterion.
- Gate: Cu and temperature improve density; wall friction and speed reduce density;
  aspect ratio peaks near 2:1; Cu30@Fe70 > Cu20@Fe80 > Cu10@Fe90 > Fe; interface
  and wall friction decrease with Cu fraction; temperature effect weakens above
  500 MPa; 100- and 197-particle models converge by 600 MPa.
- Current limitation: true core-shell particles require MPFEM or a coupled
  DEM-FEM route; the current open-source DEM route provides the particle handoff
  schema and evidence gates needed to plug that in.

## Acceptance state

The current GitHub demo runs prove both layers can rerun data and produce the
expected evidence bundles:

- Workflow: `paper-algorithm-reproduction`, run `27859253974`, commit `385993f`
- Content gate: acceptance summary, manifest, report PDF evidence anchors,
  generated plots, trend checks, Zhang multiscale fields, Liu diffusion-neck
  fields, Li core-shell/convergence fields, and DEM backend-selection outputs
  all validated
- Workflow: `dia60al40-dem`, run `27859255390`, commit `385993f`
- Artifact: `dia60al40-dem-artifacts-sizeC-Emax12-mu1.0-seed0`
- Evidence summary: 87 checks, 87 pass, 0 missing, 0 mismatch
- Final density: rho_total = 0.95
- Final pressure: 297.8374 MPa
- Stage-series paper acceptance: Li, Liu, and Yuan pass; Zhang is review with
  zero mismatches because direct solver force-chain participation and D1 still
  need paper-level calibration
- Extra stage evidence: every stage exports direct LIGGGHTS contact forces,
  arch candidates,
  electrothermal contact fields, particle temperature fields, diffusion
  mechanisms, diffusion neck ratios, and heat-isolated neck increments
- Zhang calibration artifacts also include a machine-readable next-sweep
  recommendation. When the reduced run remains below the Zhang endpoint
  pressure and force-chain participation still trends the wrong way, the next
  light GitHub Actions sweep is defined over Al endpoint modulus and friction
  scale rather than only over post-processing thresholds. The current 6-job
  recommendation, `e_al_emax_sweep_json=["18","24.174"]` and
  `mu_scale_json=["0.7","1","1.3"]` for seed 0 and size case C, was dispatched
  by `zhang-recommended-sweep` run `27859253983` and completed successfully in
  `dia60al40-dem` run `27859255390`.

This does not yet mean the full thesis/article figures are calibrated one-to-one.
It means the reproduction route is executable, source-backed by the PDFs, and
ready for the next fidelity upgrades: particle-shape backend for Yuan,
diffusion-law sintering and temperature-field solving for Liu, and core-shell
MPFEM for Li.
The consolidated Chinese progress matrix is tracked in
`docs/reproduction_status_matrix_zh.md`.
