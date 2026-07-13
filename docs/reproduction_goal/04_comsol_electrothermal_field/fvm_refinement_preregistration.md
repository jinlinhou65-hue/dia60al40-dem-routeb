# Stage 04 Open-FVM Refinement Diagnostic Preregistration

## Trigger

The six licensed COMSOL solves completed on the fixed 3316-element mesh, but the
multiplier-1 fixed-voltage case had symmetric COMSOL/FVM power and current differences of
`5.0737%`, above the immutable `5%` gate. The original loading-mode decision remains
`review`; this diagnostic does not relax or redefine that gate.

## Single Question

Is the sole global discrepancy caused by the `81 x 43` open-FVM discretization, and do the
two solvers agree on a region-level hotspot even though their single maximum nodes differ?

## Frozen Controls

- Case: `fixed_voltage_multiplier_1` only, at `0.1 V` and `293.15 K` electrode temperature.
- COMSOL evidence: the already completed 3316-element run; no licensed rerun.
- Property source: the exact committed `81 x 43` grid used by COMSOL.
- Refinement changes only the open-solver grid. Electrical and thermal properties are
  bilinearly interpolated from the frozen property table; the contact model is not reevaluated.
- Open grid factors: `1`, `2`, `3`, giving `81 x 43`, `161 x 85`, and `241 x 127` nodes.

## Gates

1. Every open solve must have electrical balance error at most `1e-8`.
2. Factor-2/factor-3 differences in Joule power and maximum temperature rise must each be
   at most `1%`.
3. The factor-3 symmetric relative differences from COMSOL power, inferred current, and
   maximum temperature rise must each be at most the original `5%` gate.
4. Interpolate COMSOL Joule heat and temperature rise to the common `241 x 127` grid.
   For each field, select points at or above its 99th percentile and compute the field-value
   weighted centroid. COMSOL/FVM centroid distance must be at most `24 um`, twice the frozen
   `12 um` contact-kernel width.
5. Single-node maxima remain reported but are not substituted for the preregistered regional
   metric because derivatives at electrodes and different node sets make a lone maximum unstable.

## Stop Rule

If factor 2/3 do not converge or factor 3 remains outside the original cross-solver gate,
retain Stage 04 as `review` and diagnose the governing discretization. Do not refine COMSOL,
alter the property field, or change the 5% threshold.
