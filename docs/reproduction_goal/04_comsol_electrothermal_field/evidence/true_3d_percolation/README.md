# True-3D Direct-Contact Percolation Evidence

## Decision

The frozen lightweight pilot produced a valid direct-contact graph and an Al-only path between
the geometric bottom and top electrodes at all three preregistered conductance thresholds. The
scientific outcome is `percolating_all_thresholds`; the model classification remains
`project_smoke_assumption_not_paper_calibration`.

## Accepted Run

- GitHub Actions run: [29246532552](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/29246532552)
- Commit: `5a26b65b5ba57c7f6b6893018a4fee1369bcab7a`
- Wall time: 140 s; internal runtime gate: 134 s of 600 s
- Artifact ID: `8277633409`
- Artifact SHA-256: `3c6553e97fa1547dc37fefdc7e60a08ae56253b5cfd4517e9f570889abb14ed3`
- LIGGGHTS-PUBLIC commit: `3d5c00f20519e6bb6eb6756f51f1ad36564e649d`

The archive contains 96 particles and 115 `pair/gran/local` direct contacts in both raw and
exported form. Particle z span is `66.1922 um`; contact-point z span is `65.4849 um`. No inferred
edge is admitted.

At threshold ratios `1e-12`, `1e-9`, and `1e-6`, the graph retains 50 active Al-Al edges and the
same five-node electrode path: `95 -> 41 -> 36 -> 27 -> 33`. Its clean-contact Hertz/Holm baseline
resistance is `0.0353279646 ohm`; the largest edge resistance on the path is
`0.0091323630 ohm`. These resistance values are explicitly uncalibrated for native Al oxide.

## Preserved Failure

- GitHub Actions run: [29246371198](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/29246371198)
- Artifact ID: `8277556707`
- Artifact SHA-256: `44ae16d0a52c3cfb1e098b7fb8444e63fdae648fb518e009a3d2fbc83ebc04f7`
- Failure: particle insertion region was already center-safe, while `all_in yes` applied a second
  radius shrink and made its volume unavailable.
- Corrective change: only the three insertion commands changed from `all_in yes` to `all_in no`;
  frozen geometry, composition, seed, contact law, loading path, timestep, and gates were retained.

## Evidence Map

- `run_29246532552/`: accepted raw DEM, exported particles/contacts, analysis tables, 3D figure,
  frozen inputs, logs, runtime gate, and solver provenance.
- `run_29246371198_failure/`: failed rendered deck, log tail, runtime gate, and provenance.
- `archive_manifest.csv`: SHA-256 and byte size for every archived file.

This evidence proves that the frozen smoke geometry can form a true-3D Al direct-contact path. It
does not prove an oxide-film resistance, experimental current, calibrated pressure-density law,
Joule temperature, sintering-neck growth, or densification feedback.
