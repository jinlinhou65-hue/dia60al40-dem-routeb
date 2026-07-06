# Zhang Contact Model And Parameter Audit

## Audit scope

This audit answers one narrow question before the next DEM run: which contact
parameter can be changed without pretending that two different damping
definitions are equivalent?

The supplied file is not Zhang Wei's 2019 doctoral thesis. Its first page
identifies it as the 2024 journal article *Simulation Study of the
Inhomogeneity Characteristics of Multiscale Mechanics during Metal Powder
Compaction*, DOI `10.3901/JME.2024.02.168`. The article cites the 2019 thesis as
reference 12. Results below therefore reproduce the supplied article and do not
claim access to the full thesis.

Source identity:

| Field | Value |
|---|---|
| Local filename | `金属粉末压制中多尺度力学特征不均匀性模拟研究_张炜.pdf` |
| PDF pages | 10 |
| File size | 1,780,662 bytes |
| SHA-256 | `d26641c507f56b45d90ea0eeefcabc9ff6d52a11903a9cf0076b6fa017bd184f` |
| Article pages | 168-177 |
| Extraction | Selectable text, 10/10 non-empty pages |

## Paper evidence

| Claim | Direct source anchor | Evidence boundary |
|---|---|---|
| The particle contact law is Hertz-Mindlin-Deresiewicz with a Coulomb tangential-force limit and an added damping term. | PDF p.3, printed p.170, section 1.1 | The article names the models but does not print the contact-force equations or solver implementation. |
| Adhesion and particle fracture are omitted. | PDF p.3, printed p.170, section 1.1 | Valid only for the relatively large, non-brittle ferrous particles considered by the article. |
| The model is 10 mm wide, 15 mm high and contains 3,000 particles. | PDF p.3, printed p.170, section 1.2, Fig. 2 discussion | This is a two-dimensional model illustration and parameter set; the article does not identify a software package. |
| Particle density is 7,800 kg/m3; diameter is 148-296 um with 222 um mean; the distribution is approximately uniform. | PDF p.3, printed p.170, section 1.2 | Ferrous powder only. |
| Initial particle-particle and particle-wall friction coefficients are both 0.25. | PDF p.3, printed p.170, section 1.2 | A single-material iron-powder model; it does not provide Al-diamond pair data. |
| Particle Young's modulus is 209 GPa and Poisson's ratio is 0.25. | PDF p.3, printed p.170, section 1.2 | The article separately supplies particle-wall contact stiffness. |
| Normal and tangential damping coefficients between particles are both 0.2. | PDF p.3, printed p.170, section 1.2 | No units, force equation, damping-ratio definition or coefficient-of-restitution conversion is supplied. |
| Particle-wall normal and tangential contact stiffnesses are both 2e12 N/m; initial porosity is 0.19. | PDF p.3, printed p.170, section 1.2 | The article does not state an equivalent wall Young's modulus. |
| Punch velocity is 0.2 m/s and compaction stops at axial strain 0.25, near 600 MPa. | PDF p.3, printed p.170, section 1.2 | This is the article's loading path, not the current reduced CI path. |
| Experiment and simulation end at 572 MPa and 638 MPa, respectively, for 2.25 mm punch travel. | PDF pp.3-4, printed pp.170-171, section 1.3 and Fig. 3 | This is a validation bracket for the ferrous-powder setup, not proof that an Al-diamond demo is calibrated. |
| The sensitivity study varies sidewall and interparticle friction separately over 0.001, 0.1, 0.2 and 0.3. | PDF p.5, printed p.172, section 3.1 | Separate variables are essential to the paper's causal interpretation. |
| Increasing either friction raises multiscale inhomogeneity; interparticle friction has the stronger micro/mesoscale effect, while both matter macroscopically. | PDF pp.6-8, printed pp.173-175, sections 3.1-3.3 | Mechanism language is simulation-based; no independent contact-scale experiment is reported. |

The page-3 visual was checked against the extracted text. It visibly contains
the `0.2` damping coefficient, `2x10^12 N/m` wall stiffness, `0.2 m/s` punch
speed, model geometry and particle count. No coefficient of restitution or
named DEM software appears anywhere in the supplied ten pages.

## Current implementation mapping

| Topic | Paper | Current LIGGGHTS route | Audit |
|---|---|---|---|
| Normal/tangential law | Hertz-Mindlin-Deresiewicz + damping + Coulomb limit | `model hertz tangential history` | Broadly compatible model family. |
| Tangential history | Required by Mindlin-Deresiewicz description | LIGGGHTS integrates tangential relative displacement and applies a Coulomb cap | Compatible at model-family level. |
| Damping input | Normal and tangential damping coefficients `0.2` | `coefficientRestitution` matrix `0.10-0.20`; LIGGGHTS derives `gamma_n` and `gamma_t` from restitution, effective mass, stiffness and overlap | **Not equivalent and not paper-derived.** |
| Friction variables | Separate `mu_p` and `mu_w` sweeps | One `mu_scale` multiplies particle-particle, particle-tool and particle-wall pairs together | **Mechanisms are confounded.** |
| Material | Ferrous powder | Al60-diamond40 composite | Trend-transfer study, not one-to-one material reproduction. |
| Particle count | 3,000 | C/pscale2 has 151 particles | Lightweight workflow evidence only. |
| Loading speed | 0.2 m/s | Accepted demo baseline is 0.5 m/s; 0.25 m/s was tested and rejected by the registered variance gate | Loading path mismatch remains explicit. |
| Endpoint modulus | 209 GPa particle modulus | Al modulus is density-dependent and reaches 72.581 GPa in the current C baseline | Calibrated demo parameter, not a paper value. |
| Pressure bracket | 572-638 MPa experiment/simulation endpoints | Used as an endpoint acceptance window | Useful benchmark, but not material validation. |

For the accepted C baseline (`mu_scale=0.654`), the actual coefficients are:

| Contact pair | Base | Effective baseline |
|---|---:|---:|
| Al-Al | 0.30 | 0.1962 |
| Al-diamond | 0.30 | 0.1962 |
| Diamond-diamond | 0.10 | 0.0654 |
| Al-tool / Al-wall | 0.08 | 0.05232 |
| Diamond-tool / Diamond-wall | 0.08 | 0.05232 |

The current global scale therefore cannot reproduce the paper's independent
`mu_p` and `mu_w` experiments.

## LIGGGHTS source audit

The official LIGGGHTS-PUBLIC source audited on 2026-07-06 was commit
`3d5c00f20519e6bb6eb6756f51f1ad36564e649d`.

- `global_properties.cpp` computes
  `beta = log(e) / sqrt(log(e)^2 + pi^2)` from `coefficientRestitution`.
- `normal_model_hertz.h` then computes separate normal and tangential damping
  constants from `beta`, effective stiffness and effective mass. Tangential
  damping is enabled by default.
- `normal_model_hertz_stiffness.h` accepts explicit `gamman` and `gammat`, but
  multiplies them by effective mass and `sqrt(R_eff * overlap)`. Its input is
  therefore not proven to be the article's unspecified coefficient `0.2`.

Primary references:

- LIGGGHTS Hertz model: https://www.cfdem.com/media/DEM/docu/gran_model_hertz.html
- LIGGGHTS tangential history model: https://www.cfdem.com/media/DEM/docu/gran_tangential_history.html
- Official source: https://github.com/CFDEMproject/LIGGGHTS-PUBLIC

## Decisions

### Prohibited interpretation

Do not set `coefficientRestitution=0.2` merely because the article reports a
damping coefficient of `0.2`. Do not switch to `hertz/stiffness` and set
`gamman=gammat=0.2` without the missing force equation and dimensional
definition. Either action would be a new sensitivity assumption, not a paper
reproduction.

### Next controlled variable

Expose a sidewall-only friction scale while keeping the existing global scale
for backward compatibility. The first paired experiment will compare:

| Control | Baseline | Paper-supported test |
|---|---:|---:|
| Effective Al-wall coefficient | 0.05232 | 0.001 |
| Effective diamond-wall coefficient | 0.05232 | 0.001 |
| Wall scale relative to baseline | 1.0 | 0.019113 |
| Particle-particle coefficients | unchanged | unchanged |
| Particle-tool coefficients | unchanged | unchanged |
| Emax / pscale / size / speed / dwell | 72.581 GPa / 2 / C / 50 cm/s / scale 1 | unchanged |
| Seeds | 0-4 | same paired seeds |

This tests the paper's lowest `mu_w` point without changing restitution or
particle friction. It is a paper-guided sensitivity of the Al-diamond route,
not a claim that the composite has iron-powder friction.

Must-pass acceptance gates, registered before execution:

1. Both baseline and test use the same pinned LIGGGHTS commit.
2. Mean test P95 remains in 572-638 MPa.
3. Test P95 CV is below baseline `0.03957423315`.
4. Trend pass coverage is at least baseline 4/5.
5. Combined pressure-window + trend coverage exceeds baseline 2/5.
6. Every artifact records actual pair coefficients and solver provenance.

Failure of any gate rejects `mu_w=0.001`; it does not trigger restitution
tuning automatically.

### Outcome and successor experiment

The registered sidewall experiment completed in DEM run `28747847286` and
rejected `mu_w=0.001`: mean P95 fell to `565.114 MPa`, CV rose to `0.0561`,
and combined pressure/trend coverage fell to 1/5. The baseline group from the
same pinned run remains the verified reference.

The next experiment therefore follows the article's independent `mu_p` sweep.
It reuses that five-seed baseline and runs only five new test jobs. All three
interparticle pairs are set to effective `mu_p=0.001`; particle-tool and
particle-wall pairs stay at `0.05232`. This is one conceptual particle-friction
variable, despite requiring three pair coefficients in the composite model.
The preregistration is `data/pscale2_c_particle_friction_plan.json`.

That successor experiment completed in run `28789107809`. Effective
`mu_p=0.001` reduced mean P95 from `574.211` to `409.996 MPa`, increased CV
from `0.0396` to `0.0463`, and produced 0/5 combined pressure/trend passes.
It is therefore rejected. The C low-friction branch is closed; this result does
not justify changing the still-undefined damping parameter.

## Confidence and missing evidence

- High confidence: bibliographic identity, model family, reported numerical
  parameters and friction sweep values; these were checked in selectable text
  and visually on PDF p.3.
- Medium confidence: family-level equivalence between the paper contact model
  and LIGGGHTS Hertz/history; exact implementations are not shown in the paper.
- Missing evidence: the article's damping-force equation, damping coefficient
  units/normalization, solver name/version, timestep, and source code.
- Overclaim risk: the 572-638 MPa bracket belongs to a ferrous-powder setup.
  Matching it with an Al-diamond reduced model is calibration evidence, not
  material validation.
