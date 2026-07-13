# Stage 04 Loading-Mode Sensitivity Preregistration

## Scientific Question

For the already frozen material-aware continuum mapping, does raising Al-Al contact
resistance produce the opposite Joule-heating response under fixed voltage and fixed current,
as required by `P=V^2/R` and `P=I^2 R`? Does the hotspot location remain invariant when only
the amplitude of the same linear field is rescaled?

## Paper-Evidence Boundary

The audited Liu PDF has SHA-256
`023fda662b186f8be43255c115bfe68fc34bb832b05719b6b3759b27f3cabfa9` and 20 PDF pages.
PDF page 13 mentions current-assisted sintering only in a literature review; PDF page 14
cites SPS literature. No applied voltage/current boundary is provided for the reproduced
model. The two loading modes below are therefore a project mechanism extension, not a Liu
paper parameter claim.

## Frozen Inputs

- Particle/contact state: archived `stage5_rho095`, 76 particles and 157 direct contacts.
- Contact mapping and material values: the immutable base parameter file with SHA-256
  `bad8c513dcf63f1b8df7fe365d88c88f551156b8bc68794a6ee8b6ec044f27f7`.
- Al-Al resistance multipliers: `1`, `10`, and `100`; no new fit parameter is introduced.
- FVM grid: `81 x 43`; kernel and property bounds remain unchanged.
- COMSOL mesh: `hmax=8 um`, `hmin=1 um`, expected 3316 elements. No mesh study is repeated.
- Thermal boundary: both electrodes at `293.15 K`; side boundaries insulated.
- Electrical physics remains linear and temperature-independent in this screening model.

## Loading Families

1. **Fixed voltage:** all three resistance cases use `0.1 V`.
2. **Fixed current:** first solve the multiplier-10 reference at `0.1 V`; freeze its FVM top
   current per metre depth as `Iref`. For every resistance case, set
   `Vcase = Iref / (Icase_at_0.1V / 0.1V)` and rerun both FVM and COMSOL.

Within each family, only the Al-Al resistance multiplier changes. The fixed-current target is
computed once before the remaining cases and is never retuned.

## Expected Trends And Gates

1. Fixed voltage: power and maximum temperature rise must be nonincreasing with resistance.
2. Fixed current: power and maximum temperature rise must be nondecreasing with resistance.
3. FVM electrical balance error must be at most `1e-8`; fixed-current error at most `1e-10`.
4. Multiplier-10 fixed-voltage and fixed-current cases must coincide because they define `Iref`.
5. For a given resistance case, fixed-voltage and fixed-current Joule/temperature hotspot
   coordinates must coincide on the FVM grid; only amplitudes may change.
6. Each licensed COMSOL run must use the fixed medium mesh and a clean batch log.
7. COMSOL/FVM relative differences for current, Joule power, and maximum temperature rise
   must each be at most `5%` for all six cases.

## Stop Conditions

- Do not alter the previously accepted mesh or contact-resistance range after seeing results.
- Stop and diagnose if a loading-family trend is reversed, conservation fails, the fixed-current
  target drifts, or COMSOL changes element count.
- A pass remains conditional because the two-dimensional active particle network is not
  percolating and the continuum background is not experimentally calibrated.
