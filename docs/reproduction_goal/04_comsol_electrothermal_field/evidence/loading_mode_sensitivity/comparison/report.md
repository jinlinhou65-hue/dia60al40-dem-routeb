# Stage 04 Loading-Mode COMSOL/FVM Report

Decision: `review`

| Mode | R multiplier | Voltage (V) | COMSOL/FVM power (W/m) | COMSOL/FVM rise (K) | Power diff | Rise diff |
|---|---:|---:|---:|---:|---:|---:|
| fixed_current | 1 | 0.0154982447 | 5.30088 / 5.03859 | 0.021568 / 0.0206894 | 5.074% | 4.158% |
| fixed_current | 10 | 0.1 | 33.9503 / 32.5107 | 0.122656 / 0.117555 | 4.332% | 4.247% |
| fixed_current | 100 | 0.415863389 | 136.393 / 135.2 | 0.325962 / 0.323783 | 0.878% | 0.671% |
| fixed_voltage | 1 | 0.1 | 220.69 / 209.77 | 0.897934 / 0.861355 | 5.074% | 4.158% |
| fixed_voltage | 10 | 0.1 | 33.9503 / 32.5107 | 0.122656 / 0.117555 | 4.332% | 4.247% |
| fixed_voltage | 100 | 0.1 | 7.88661 / 7.81764 | 0.018848 / 0.018722 | 0.878% | 0.671% |

All COMSOL cases use the already accepted 3316-element medium mesh. The loading modes
are a project mechanism extension because the audited Liu PDF does not specify an
electrical boundary condition.

## Boundary

This verifies conditional loading-mode behavior and cross-solver consistency. It does not establish a percolating particle-resolved network or experimental temperature.
