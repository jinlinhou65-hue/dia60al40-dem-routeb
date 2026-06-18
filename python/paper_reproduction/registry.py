from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .pdf_evidence import get_pdf_evidence


@dataclass(frozen=True)
class PaperTarget:
    key: str
    paper: str
    title: str
    source_basis: list[str]
    paper_methods: list[str]
    reproduced_algorithms: list[str]
    calibration_targets: list[str]
    expected_outputs: list[str]
    acceptance_gates: list[str]
    current_backend: str
    next_backend_steps: list[str]


PAPER_TARGETS = [
    PaperTarget(
        key="zhang",
        paper="Zhang",
        title="Multi-scale mechanical inhomogeneity in metal-powder compaction",
        source_basis=[
            "2D DEM iron-powder die, 10 mm by 15 mm, about 3000 particles",
            "particle diameter 148-296 um, density 7800 kg/m3, E=209 GPa, nu=0.25",
            "Hertz-Mindlin-Deresiewicz contact, Coulomb friction, damping 0.2",
            "upper punch speed 0.2 m/s to axial strain 0.25 and about 600 MPa",
        ],
        paper_methods=[
            "contact-force Gini index",
            "contact-force participation index",
            "force-chain extraction with force-above-mean and minimum chain length 3",
            "force-chain strength inhomogeneity D1",
            "measurement-circle local y-stress inhomogeneity D2",
        ],
        reproduced_algorithms=[
            "synthetic pressure-density trajectory",
            "contact-force Gini and participation trend checks",
            "D1 and D2 trend checks",
            "real DEM stage-series post-processing from handoff particle CSV files",
        ],
        calibration_targets=[
            "pressure and relative density increase with axial strain",
            "Gini and D1 decrease as the force network homogenizes",
            "D2 decreases as local stress becomes more uniform",
            "larger wall or particle friction should increase inhomogeneity",
        ],
        expected_outputs=[
            "zhang/zhang_multiscale_metrics.csv",
            "series_network_metrics.csv",
            "series_trend_checks.json",
        ],
        acceptance_gates=[
            "pressure_mpa increasing",
            "relative_density or actual_rho_total increasing",
            "contact_gini decreasing",
            "contact_participation increasing",
            "force_chain_strength_inhomogeneity_d1 decreasing",
            "local_stress_inhomogeneity_d2 decreasing",
        ],
        current_backend="proxy plus Route-B DEM stage-series post-processing",
        next_backend_steps=[
            "replace overlap-inferred contacts with solver contact-force export",
            "add explicit mu_p and mu_w sweeps",
            "compare pressure-density curve against the reported 572-638 MPa endpoint",
        ],
    ),
    PaperTarget(
        key="yuan",
        paper="Yuan",
        title="Mechanical mechanism and arch-bridge structure in powder compaction",
        source_basis=[
            "DEM die 0.016 m by 0.020 m, initial porosity about 0.22",
            "particle density 7890 kg/m3, nu=0.29, E=80 GPa, damping 0.25",
            "wall stiffness 2e12 N/m, particle friction 0.2, punch speed 2 cm/s",
            "reported Heckel fit ln(1/(1-rho_v)) = 0.0015 P + 1.9752",
            "MPFEM handoff with 160 particles, 300-400 um, plane strain, 600 MPa",
        ],
        paper_methods=[
            "DEM force-chain extraction",
            "arch-bridge identification from strong connected force chains",
            "arch count, obstruction, strength, direction angle, and buckling angle",
            "particle-shape comparison using circle, hexagon, and strip proxies",
        ],
        reproduced_algorithms=[
            "shape-dependent arch metric generator",
            "arch candidates from inferred contact network",
            "stage-series arch count, strength, direction, and buckling outputs",
        ],
        calibration_targets=[
            "arch count increases then fluctuates with pressure",
            "arch strength growth slows after about 100 MPa",
            "main arch direction stays near 90 degrees",
            "lower aspect-ratio strip particles reduce arch obstruction",
        ],
        expected_outputs=[
            "yuan/yuan_arch_bridge_metrics.csv",
            "stage_details/*_arches.csv",
            "series_network_metrics.csv",
        ],
        acceptance_gates=[
            "arch_count positive",
            "circle arch_count greater than strip arch_count",
            "circle arch strength greater than strip arch strength",
            "arch direction angle finite",
            "arch buckling angle finite",
        ],
        current_backend="proxy shape sweep plus Route-B contact-network arch extraction",
        next_backend_steps=[
            "add particle-shape backend, such as clump, polygon, or superquadric DEM",
            "calibrate strong-contact threshold against force-chain images",
            "export arch topology for direct visual comparison",
        ],
    ),
    PaperTarget(
        key="liu",
        paper="Liu",
        title="Coupled compaction-sintering densification and microstructure evolution",
        source_basis=[
            "Huang, Heckel, and Kawakita compaction equations are fitted to density-pressure data",
            "compaction exports density, pore, contact area, neck, residual stress, and contact force",
            "sintering uses early-stage neck growth with diffusion terms",
            "temperature enters diffusion through Arrhenius D = D0 exp(-Q/RT)",
        ],
        paper_methods=[
            "Heckel linearization",
            "Huang pressure-density fit",
            "Kawakita compression fit",
            "contact-force to electrical current and Joule heat coupling",
            "temperature-dependent neck-growth proxy",
        ],
        reproduced_algorithms=[
            "compaction curve generator",
            "Heckel, Huang, and Kawakita fit functions",
            "contact electrical-thermal network",
            "force-current and Joule heat-neck correlation checks",
        ],
        calibration_targets=[
            "density increases with pressure",
            "all three compaction models produce identifiable fits",
            "normal force positively correlates with current",
            "Joule heat positively correlates with neck growth",
        ],
        expected_outputs=[
            "liu/liu_compaction_curve.csv",
            "liu/liu_compaction_fits.csv",
            "liu/liu_electrothermal_sintering.csv",
            "liu/liu_coupling_summary.json",
            "series_compaction_fits.csv",
        ],
        acceptance_gates=[
            "relative_density increasing",
            "Heckel fit exists",
            "Huang fit exists",
            "Kawakita fit exists",
            "force-current correlation positive",
            "Joule heat-neck correlation positive",
        ],
        current_backend="proxy compaction/electrothermal coupling plus Route-B stage fits",
        next_backend_steps=[
            "calibrate contact conductance from contact radius or force law",
            "replace neck proxy with a diffusion-based sintering step",
            "add temperature field solve and material softening feedback",
        ],
    ),
    PaperTarget(
        key="li",
        paper="Li",
        title="Densification law of coated composite powder under compaction",
        source_basis=[
            "Cu@Fe core-shell powder modeled with discrete FEM and multi-particle FEM",
            "9-particle and 197-particle random models with Johnson-Cook plasticity",
            "Cu and Fe material parameters include E, nu, density, heat capacity, thermal conductivity",
            "main sweeps: Cu fraction, temperature, wall friction, pressing speed, aspect ratio",
        ],
        paper_methods=[
            "relative density from particle area over die area",
            "Heckel fit for Fe and Cu20@Fe80 curves",
            "wall-friction, temperature, pressing-speed, composition, and aspect-ratio sweeps",
            "coated shell as softer, more conductive deformation path",
        ],
        reproduced_algorithms=[
            "equivalent coated-powder parameter sweep generator",
            "density trend checks for composition, temperature, friction, speed, and aspect ratio",
            "stage schema gate for replacing the equivalent model with MPFEM outputs",
        ],
        calibration_targets=[
            "Cu fraction increases relative density from Fe to Cu30@Fe70",
            "temperature increases density, with diminishing high-pressure effect",
            "wall friction reduces density",
            "pressing speed reduces density at fixed pressure",
            "aspect ratio near 2:1 gives the highest density among tested ratios",
        ],
        expected_outputs=[
            "li/li_coated_powder_sweeps.csv",
            "paper_trend_checks.json",
            "series_acceptance_summary.csv",
        ],
        acceptance_gates=[
            "Cu coating improves density",
            "temperature improves density",
            "wall friction reduces density",
            "pressing speed reduces density",
            "aspect ratio near 2 is favorable",
        ],
        current_backend="equivalent material/process sweep proxy",
        next_backend_steps=[
            "add core-shell particle geometry or MPFEM handoff",
            "calibrate Cu/Fe Johnson-Cook parameters and thermal expansion",
            "separate compaction softening from oxidation/thermal-expansion effects",
        ],
    ),
]


def get_paper_targets(keys: list[str] | None = None) -> list[PaperTarget]:
    if not keys or keys == ["all"]:
        return list(PAPER_TARGETS)
    requested = set(keys)
    return [target for target in PAPER_TARGETS if target.key in requested]


def build_manifest(keys: list[str] | None = None) -> dict[str, object]:
    targets = get_paper_targets(keys)
    evidence = get_pdf_evidence([target.key for target in targets])
    return {
        "version": 1,
        "scope": "first-pass paper algorithm reproduction",
        "backend_policy": (
            "Keep paper algorithms, output schemas, and acceptance gates stable while "
            "swapping proxy data for DEM, MPFEM, or electrothermal solver exports."
        ),
        "papers": [
            {**asdict(target), "pdf_evidence": evidence.get(target.key, [])}
            for target in targets
        ],
    }


def write_manifest_outputs(
    outdir: Path,
    *,
    keys: list[str] | None = None,
) -> dict[str, Path]:
    manifest = build_manifest(keys)
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "paper_reproduction_manifest.json"
    markdown_path = outdir / "paper_reproduction_manifest.md"
    json_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    markdown_path.write_text(render_manifest_markdown(manifest), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def render_manifest_markdown(manifest: dict[str, object]) -> str:
    papers = list(manifest["papers"])
    lines = [
        "# Paper Reproduction Manifest",
        "",
        f"- Scope: {manifest['scope']}",
        f"- Backend policy: {manifest['backend_policy']}",
        "",
        "## Paper Targets",
        "",
        "| Paper | Current Backend | Expected Outputs | First Acceptance Gates |",
        "|---|---|---|---|",
    ]
    for paper in papers:
        lines.append(
            "| {paper} | {backend} | {outputs} | {gates} |".format(
                paper=paper["paper"],
                backend=paper["current_backend"],
                outputs="<br>".join(f"`{item}`" for item in paper["expected_outputs"]),
                gates="<br>".join(str(item) for item in paper["acceptance_gates"]),
            )
        )
    for paper in papers:
        lines.extend(
            [
                "",
                f"## {paper['paper']}: {paper['title']}",
                "",
                "### Source Basis",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in paper["source_basis"])
        lines.extend(["", "### Paper Methods", ""])
        lines.extend(f"- {item}" for item in paper["paper_methods"])
        lines.extend(["", "### PDF Evidence", ""])
        for item in paper.get("pdf_evidence", []):
            lines.append(
                "- p{page}: {evidence} Reproduction use: {use} Status: {status}".format(
                    page=item["page"],
                    evidence=item["evidence"],
                    use=item["reproduction_use"],
                    status=item["current_status"],
                )
            )
        lines.extend(["", "### Reproduced Algorithms", ""])
        lines.extend(f"- {item}" for item in paper["reproduced_algorithms"])
        lines.extend(["", "### Calibration Targets", ""])
        lines.extend(f"- {item}" for item in paper["calibration_targets"])
        lines.extend(["", "### Next Backend Steps", ""])
        lines.extend(f"- {item}" for item in paper["next_backend_steps"])
    lines.append("")
    return "\n".join(lines)
