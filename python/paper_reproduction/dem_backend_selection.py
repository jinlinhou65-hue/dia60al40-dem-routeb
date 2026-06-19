from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


CRITERIA_WEIGHTS = {
    "ci_linux_backend": 3,
    "die_compaction_geometry": 3,
    "contact_stress_export": 3,
    "shape_upgrade_path": 2,
    "electrothermal_upgrade_path": 2,
    "paper_algorithm_fit": 3,
    "windows_remote_fit": 2,
    "maintenance_risk": 2,
}


@dataclass(frozen=True)
class BackendCandidate:
    key: str
    name: str
    role: str
    license: str
    official_source: str
    source_basis: list[str]
    strengths: list[str]
    limitations: list[str]
    paper_fit: dict[str, str]
    scores: dict[str, int]

    @property
    def weighted_score(self) -> int:
        return sum(
            self.scores.get(criterion, 0) * weight
            for criterion, weight in CRITERIA_WEIGHTS.items()
        )


BACKEND_CANDIDATES = [
    BackendCandidate(
        key="liggghts_public",
        name="LIGGGHTS-PUBLIC",
        role="selected primary real-DEM backend",
        license="GPL-2.0-or-later",
        official_source="https://github.com/CFDEMproject/LIGGGHTS-PUBLIC",
        source_basis=[
            "Official repository describes LIGGGHTS-PUBLIC as an open-source DEM particle simulation software.",
            "The current GitHub Actions workflow builds the serial binary on ubuntu-22.04 and reruns staged die compaction.",
        ],
        strengths=[
            "Already produces pressure-density stages, restarts, handoff CSVs, and paper evidence in CI.",
            "Fits the Zhang/Yuan DEM first pass with moving walls, particle contacts, and stage exports.",
            "Keeps Windows as the editing/review machine while Linux workflow handles solver execution.",
        ],
        limitations=[
            "Current route uses spherical particles, so Yuan shape fidelity still needs clumps, polygons, or MPFEM.",
            "Direct pair-force tensor export must replace the current overlap-inferred contact-force proxy.",
            "LIGGGHTS-PUBLIC is older; long-term maintenance risk is higher than LAMMPS mainline.",
        ],
        paper_fit={
            "Zhang": "primary for stress/contact/force-chain stage series",
            "Yuan": "primary first pass for arch graphs; shape backend still needed",
            "Liu": "geometry/contact source for electrothermal post-processing",
            "Li": "particle handoff source only; core-shell MPFEM remains separate",
        },
        scores={
            "ci_linux_backend": 5,
            "die_compaction_geometry": 5,
            "contact_stress_export": 4,
            "shape_upgrade_path": 3,
            "electrothermal_upgrade_path": 3,
            "paper_algorithm_fit": 5,
            "windows_remote_fit": 5,
            "maintenance_risk": 2,
        },
    ),
    BackendCandidate(
        key="lammps_granular",
        name="LAMMPS GRANULAR package",
        role="main fallback and future maintained backend",
        license="GPL-2.0-or-later",
        official_source="https://docs.lammps.org/Howto_granular.html",
        source_basis=[
            "LAMMPS granular documentation lists sphere particles, wall/gran fixes, fabric tensors, and heat-flow options.",
            "pair_style granular supports normal, tangential, rolling, and twisting contact models.",
        ],
        strengths=[
            "More actively maintained upstream than LIGGGHTS-PUBLIC.",
            "Has granular heat conduction hooks and fabric tensor outputs useful for Liu/Zhang metrics.",
            "Supports clusters, BPM, and superellipsoids for Yuan shape upgrades.",
        ],
        limitations=[
            "Requires rewriting the existing LIGGGHTS deck and output parser contracts.",
            "Mesh-wall and staged die workflow must be reproven in CI before replacing LIGGGHTS.",
            "Not yet used by this repository's successful workflow artifacts.",
        ],
        paper_fit={
            "Zhang": "strong fallback for contact/fabric statistics",
            "Yuan": "good shape upgrade path through clusters or superellipsoids",
            "Liu": "strong thermal-contact upgrade path",
            "Li": "handoff source; core-shell FEM still separate",
        },
        scores={
            "ci_linux_backend": 3,
            "die_compaction_geometry": 3,
            "contact_stress_export": 4,
            "shape_upgrade_path": 5,
            "electrothermal_upgrade_path": 5,
            "paper_algorithm_fit": 4,
            "windows_remote_fit": 4,
            "maintenance_risk": 5,
        },
    ),
    BackendCandidate(
        key="yade",
        name="YADE",
        role="research backend for custom contact laws and rapid Python studies",
        license="GPL",
        official_source="https://yade-dem.org/doc/",
        source_basis=[
            "YADE documents an extensible open-source DEM framework with C++ computation and Python control.",
            "Its Python layer is attractive for paper-style metric extraction and algorithm experiments.",
        ],
        strengths=[
            "Good for reproducing PFC-like algorithm studies and custom contact laws.",
            "Python scene construction and post-processing match the current solver-neutral layer.",
            "Useful for fast experiments before committing to a heavier production backend.",
        ],
        limitations=[
            "Windows execution remains awkward, so workflow or Linux VM remains preferred.",
            "Repository has no passing YADE workflow yet.",
            "Core-shell MPFEM and calibrated thermal sintering still require extra coupling.",
        ],
        paper_fit={
            "Zhang": "good research reproduction of contact-force statistics",
            "Yuan": "good arch and custom shape/contact experiments",
            "Liu": "post-processing source; thermal solve still external",
            "Li": "limited to particle arrangement handoff",
        },
        scores={
            "ci_linux_backend": 3,
            "die_compaction_geometry": 3,
            "contact_stress_export": 4,
            "shape_upgrade_path": 4,
            "electrothermal_upgrade_path": 2,
            "paper_algorithm_fit": 4,
            "windows_remote_fit": 3,
            "maintenance_risk": 4,
        },
    ),
    BackendCandidate(
        key="mercurydpm",
        name="MercuryDPM",
        role="C++ candidate for complex industrial particle simulations",
        license="open source",
        official_source="https://www.mercurydpm.org/",
        source_basis=[
            "MercuryDPM describes itself as open-source code for discrete particle simulations.",
            "Its documentation highlights complex walls, polydisperse packings, and self-tests across platforms.",
        ],
        strengths=[
            "Strong C++ driver model for controlled particle, wall, and interaction setup.",
            "Cross-platform story is better than YADE/LIGGGHTS for local exploration.",
            "Useful future candidate if workflow builds become more stable than LIGGGHTS.",
        ],
        limitations=[
            "Would require a new driver and new parser interfaces.",
            "Less directly aligned with the current LIGGGHTS deck and workflow artifacts.",
            "Electrothermal and core-shell coupling still need custom extension work.",
        ],
        paper_fit={
            "Zhang": "possible contact-statistics backend",
            "Yuan": "possible arch backend with custom drivers",
            "Liu": "post-processing source unless custom heat coupling is added",
            "Li": "handoff source only",
        },
        scores={
            "ci_linux_backend": 3,
            "die_compaction_geometry": 4,
            "contact_stress_export": 4,
            "shape_upgrade_path": 3,
            "electrothermal_upgrade_path": 2,
            "paper_algorithm_fit": 3,
            "windows_remote_fit": 4,
            "maintenance_risk": 4,
        },
    ),
    BackendCandidate(
        key="chrono_deme",
        name="Project Chrono DEM / DEM-Engine",
        role="future GPU/clump backend",
        license="BSD-3-Clause",
        official_source="https://api.projectchrono.org/deme_usage.html",
        source_basis=[
            "Chrono DEM documentation describes GPU granular dynamics through CUDA or HIP.",
            "DEM-Engine supports clump-represented particles interacting with mesh bodies and analytical boundaries.",
        ],
        strengths=[
            "Best long-term path for high-throughput clump or mesh-body granular simulations.",
            "Permissive license and active Project Chrono ecosystem.",
            "Attractive for Yuan shape upgrades after the CPU workflow is calibrated.",
        ],
        limitations=[
            "GPU requirements do not match the current lightweight GitHub Actions demo.",
            "Current Chrono DEM docs emphasize mono-disperse spheres in the DEM module; DEME adds clumps but needs a new build path.",
            "Not necessary until direct-force CPU evidence and paper gates are stable.",
        ],
        paper_fit={
            "Zhang": "future acceleration path after metric contracts are stable",
            "Yuan": "strong future clump/shape route",
            "Liu": "possible heat/contact extension path after GPU setup",
            "Li": "handoff source only",
        },
        scores={
            "ci_linux_backend": 2,
            "die_compaction_geometry": 4,
            "contact_stress_export": 3,
            "shape_upgrade_path": 5,
            "electrothermal_upgrade_path": 2,
            "paper_algorithm_fit": 3,
            "windows_remote_fit": 2,
            "maintenance_risk": 4,
        },
    ),
]


def rank_backend_candidates() -> list[BackendCandidate]:
    return sorted(
        BACKEND_CANDIDATES,
        key=lambda candidate: (-candidate.weighted_score, candidate.name),
    )


def selected_backend() -> BackendCandidate:
    selected = [candidate for candidate in BACKEND_CANDIDATES if candidate.role.startswith("selected")]
    if len(selected) != 1:
        raise ValueError("Exactly one selected backend is required")
    return selected[0]


def build_backend_selection_manifest() -> dict[str, object]:
    selected = selected_backend()
    ranked = rank_backend_candidates()
    return {
        "version": 1,
        "decision": selected.name,
        "decision_key": selected.key,
        "policy": (
            "Use LIGGGHTS-PUBLIC for the current real-data CI demo because it is already "
            "green in GitHub Actions; keep the paper metric schema solver-neutral so "
            "LAMMPS, YADE, MercuryDPM, Chrono DEME, or MPFEM exports can replace it."
        ),
        "criteria_weights": dict(CRITERIA_WEIGHTS),
        "ranked_candidates": [
            {**asdict(candidate), "weighted_score": candidate.weighted_score}
            for candidate in ranked
        ],
        "non_open_source_paper_tools": [
            "PFC/PFC2D, MSC.MARC, Abaqus, and COMSOL are treated as paper references or optional calibration tools, not required open-source backends.",
        ],
        "next_backend_upgrades": [
            "wire solver pair-force exports into the existing --contact-dir stage-series contract",
            "add a shape-capable backend for Yuan particle morphology",
            "add a thermal field solve and calibrated diffusion constants for Liu",
            "add MPFEM or FEM handoff for Li core-shell deformation",
        ],
    }


def render_backend_selection_markdown() -> str:
    manifest = build_backend_selection_manifest()
    lines = [
        "# DEM Backend Selection",
        "",
        "This route chooses an open-source DEM backend for the real-data demo while",
        "keeping the paper-reproduction algorithms solver-neutral.",
        "",
        "## Decision",
        "",
        f"- Selected backend: {manifest['decision']}",
        f"- Policy: {manifest['policy']}",
        "",
        "## Criteria",
        "",
        "| Criterion | Weight |",
        "|---|---:|",
    ]
    for criterion, weight in manifest["criteria_weights"].items():
        lines.append(f"| `{criterion}` | {weight} |")

    lines.extend(
        [
            "",
            "## Candidate Ranking",
            "",
            "| Rank | Backend | Role | Score | License | Official source |",
            "|---:|---|---|---:|---|---|",
        ]
    )
    for index, candidate in enumerate(manifest["ranked_candidates"], start=1):
        lines.append(
            "| {rank} | {name} | {role} | {score} | {license} | {source} |".format(
                rank=index,
                name=candidate["name"],
                role=candidate["role"],
                score=candidate["weighted_score"],
                license=candidate["license"],
                source=candidate["official_source"],
            )
        )

    for candidate in manifest["ranked_candidates"]:
        lines.extend(
            [
                "",
                f"## {candidate['name']}",
                "",
                f"- Role: {candidate['role']}",
                f"- Official source: {candidate['official_source']}",
                "",
                "### Source Basis",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in candidate["source_basis"])
        lines.extend(["", "### Strengths", ""])
        lines.extend(f"- {item}" for item in candidate["strengths"])
        lines.extend(["", "### Limitations", ""])
        lines.extend(f"- {item}" for item in candidate["limitations"])
        lines.extend(["", "### Paper Fit", ""])
        for paper, fit in candidate["paper_fit"].items():
            lines.append(f"- {paper}: {fit}")

    lines.extend(["", "## Excluded Non-Open-Source Paper Tools", ""])
    lines.extend(f"- {item}" for item in manifest["non_open_source_paper_tools"])
    lines.extend(["", "## Next Backend Upgrades", ""])
    lines.extend(f"- {item}" for item in manifest["next_backend_upgrades"])
    lines.append("")
    return "\n".join(lines)


def write_backend_selection_outputs(outdir: Path) -> dict[str, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "dem_backend_selection.json"
    markdown_path = outdir / "dem_backend_selection.md"
    json_path.write_text(
        json.dumps(build_backend_selection_manifest(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    markdown_path.write_text(render_backend_selection_markdown(), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
