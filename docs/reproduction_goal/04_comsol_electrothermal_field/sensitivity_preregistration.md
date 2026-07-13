# Stage 04 Contact-Parameter Sensitivity Preregistration

## Frozen Inputs

- Use only the archived `stage5_rho095` 76-particle state and 157 direct LIGGGHTS contacts.
- Do not infer contacts and do not repeat the completed COMSOL mesh study.
- Keep the continuum grid at `81 x 43`, the conditional voltage at `0.1 V`, and the
  already accepted COMSOL medium mesh at 3316 elements.
- Use the DEM stage-5 elastic constants for Hertz consistency. They are not relabelled as
  measured bulk constants.

## Contact Laws

For each direct contact, compute the Hertz radius and clean constriction resistances:

```text
1/R* = 1/R1 + 1/R2
1/E* = (1-nu1^2)/E1 + (1-nu2^2)/E2
a = (3 F R* / (4 E*))^(1/3)
Re_clean = (rho1 + rho2) / (4 a)
Rth = (1/k1 + 1/k2) / (4 a)
```

For Al-Al contacts, multiply `Re_clean` by `1`, `10`, and `100`. These are bounded
clean-to-oxidized screening states, not fitted oxide properties. For Al-diamond contacts,
add `1/(h A)` to the thermal resistance using the central `h=80 MW/(m2 K)` choice.

## Decisions Fixed Before Running

1. Report contact-type counts and Hertz `a/min(R)` validity warnings.
2. Treat an edge as electrically active only when its conductance is at least `1e-12` of
   the maximum edge conductance; report bottom-to-top percolation before solving fields.
3. Freeze Gaussian-field normalization to the reference multiplier-10 case. Scenario-wise
   renormalization is forbidden because it would erase resistance sensitivity.
4. Report total Joule power, maximum temperature rise, hotspot coordinates, electrical
   balance, and whether the active particle network percolates.
5. Under fixed voltage, expect power and maximum temperature rise not to increase when
   Al-Al resistance is raised. A violation fails the sensitivity gate.

## Interpretation Boundary

The direct network topology is the primary physical screen. The FVM/COMSOL continuum field
is conditional and regularized; it visualizes how an assumed conductive background closes a
2D non-percolating snapshot. It cannot establish experimental temperature or current until
oxide/contact parameters and electrode connectivity are measured or supplied by a 3D model.
