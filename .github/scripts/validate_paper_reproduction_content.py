from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path


PAPER_TITLES = {
    "zhang": "Zhang",
    "yuan": "Yuan",
    "liu": "Liu",
    "li": "Li",
}

CORE_FILES = [
    "summary.json",
    "dem_backend_selection.json",
    "dem_backend_selection.md",
    "paper_reproduction_manifest.json",
    "paper_reproduction_report.md",
    "paper_trend_checks.json",
    "paper_acceptance_summary.csv",
]

ZHANG_REQUIRED_FIELDS = {
    "step",
    "axial_strain",
    "pressure_mpa",
    "relative_density",
    "contact_count",
    "contact_force_mean",
    "contact_force_std",
    "contact_gini",
    "contact_participation",
    "strong_contact_threshold",
    "strong_contact_fraction",
    "force_chain_count",
    "force_chain_mean_length",
    "force_chain_mean_strength",
    "force_chain_strength_std",
    "force_chain_strength_inhomogeneity_d1",
    "measurement_circle_count",
    "local_stress_mean",
    "local_stress_std",
    "local_stress_inhomogeneity_d2",
}

ZHANG_FRICTION_REQUIRED_FIELDS = {
    "friction_type",
    "wall_mu",
    "particle_mu",
    "contact_gini",
    "contact_participation",
    "force_chain_strength_inhomogeneity_d1",
    "local_stress_inhomogeneity_d2",
}

LIU_REQUIRED_FIELDS = {
    "contact_id",
    "normal_force",
    "current",
    "joule_heat",
    "temperature_k",
    "dominant_diffusion_mechanism",
    "neck_growth_exponent",
    "neck_ratio",
    "neck_ratio_diffusion",
    "neck_ratio_thermal_gain",
}

LI_REQUIRED_FIELDS = {
    "sweep",
    "cu_fraction",
    "temperature_c",
    "wall_mu",
    "pressing_speed",
    "aspect_ratio",
    "interface_friction_proxy",
    "wall_friction_proxy",
    "flow_factor",
    "thermal_softening_gain",
    "thermal_expansion_penalty",
    "max_von_mises_mpa",
    "predicted_relative_density",
}

LI_CORE_REQUIRED_FIELDS = {
    "composition",
    "cu_fraction",
    "fe_fraction",
    "shell_thickness_ratio",
    "relative_density_600mpa",
    "mean_von_mises_mpa",
    "stress_uniformity_index",
    "plastic_strain_proxy",
    "interface_friction_proxy",
    "wall_friction_proxy",
    "flow_factor",
}

LI_TEMPERATURE_REQUIRED_FIELDS = {
    "material",
    "pressure_mpa",
    "temperature_c",
    "relative_density",
    "thermal_softening_gain",
    "thermal_expansion_penalty",
    "temperature_effect_attenuation",
}

LI_CONVERGENCE_REQUIRED_FIELDS = {
    "pressure_mpa",
    "particle_count",
    "relative_density",
    "density_difference_from_197",
    "rearrangement_contribution",
    "plastic_deformation_contribution",
}

YUAN_REQUIRED_FIELDS = {
    "shape",
    "pressure_mpa",
    "arch_count",
    "arch_mean_length",
    "arch_total_length",
    "arch_mean_strength",
    "arch_obstruction_index",
    "arch_direction_angle_degrees",
    "arch_buckling_angle_degrees",
}


class ContentValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


def validate_content(outdir: Path, paper: str = "all") -> dict[str, object]:
    outdir = outdir.resolve()
    expected_keys = list(PAPER_TITLES) if paper == "all" else [paper]
    expected_titles = {PAPER_TITLES[key] for key in expected_keys}
    errors: list[str] = []

    for rel_path in CORE_FILES:
        require((outdir / rel_path).is_file(), errors, f"missing required file: {rel_path}")

    acceptance_rows = read_csv_if_exists(outdir / "paper_acceptance_summary.csv")
    acceptance_by_paper = {row.get("paper", ""): row for row in acceptance_rows}
    require(
        set(acceptance_by_paper) == expected_titles,
        errors,
        f"acceptance papers {sorted(acceptance_by_paper)} did not match expected {sorted(expected_titles)}",
    )
    for title in sorted(expected_titles):
        row = acceptance_by_paper.get(title)
        if not row:
            continue
        require(row.get("status") == "pass", errors, f"{title} acceptance status is not pass")
        require(int_value(row.get("missing")) == 0, errors, f"{title} acceptance has missing checks")
        require(int_value(row.get("mismatch")) == 0, errors, f"{title} acceptance has mismatched checks")

    manifest = read_json_if_exists(outdir / "paper_reproduction_manifest.json", {})
    backend_selection = manifest.get("dem_backend_selection", {})
    require(
        isinstance(backend_selection, dict) and backend_selection.get("decision") == "LIGGGHTS-PUBLIC",
        errors,
        "manifest missing LIGGGHTS-PUBLIC DEM backend decision",
    )
    validate_backend_selection_content(outdir, errors)
    manifest_papers = {
        str(row.get("key", "")): row
        for row in manifest.get("papers", [])
        if isinstance(row, dict)
    }
    require(
        set(manifest_papers) == set(expected_keys),
        errors,
        f"manifest papers {sorted(manifest_papers)} did not match expected {expected_keys}",
    )
    for key in expected_keys:
        row = manifest_papers.get(key, {})
        require(bool(row.get("current_backend")), errors, f"{key} manifest missing current backend")
        require(bool(row.get("reproduced_algorithms")), errors, f"{key} manifest missing reproduced algorithms")
        require(bool(row.get("pdf_evidence")), errors, f"{key} manifest missing PDF evidence anchors")

    summary = read_json_if_exists(outdir / "summary.json", {})
    summary_papers = extract_summary_papers(summary)
    require(
        set(summary_papers) == set(expected_keys),
        errors,
        f"summary papers {sorted(summary_papers)} did not match expected {expected_keys}",
    )
    for key in expected_keys:
        paper_summary = summary_papers.get(key, {})
        outputs = paper_summary.get("outputs", []) if isinstance(paper_summary, dict) else []
        require(bool(outputs), errors, f"{key} summary missing output list")
        for output in outputs:
            require((outdir / key / str(output)).is_file(), errors, f"{key} output missing: {output}")

    report_text = read_text_if_exists(outdir / "paper_reproduction_report.md")
    require("Acceptance Summary" in report_text, errors, "report missing acceptance summary")
    require("PDF evidence anchors" in report_text, errors, "report missing PDF evidence anchors")
    for title in sorted(expected_titles):
        require(f"### {title}:" in report_text, errors, f"report missing section for {title}")

    trend_checks = read_json_if_exists(outdir / "paper_trend_checks.json", [])
    for title in sorted(expected_titles):
        paper_checks = [row for row in trend_checks if row.get("paper") == title]
        require(bool(paper_checks), errors, f"{title} has no trend checks")
        failed = [row.get("label", "unknown") for row in paper_checks if row.get("status") != "pass"]
        require(not failed, errors, f"{title} trend checks failed: {failed}")

    plot_dir = outdir / "plots"
    plots = list(plot_dir.glob("*.svg")) if plot_dir.is_dir() else []
    for key in expected_keys:
        require(
            any(path.name.startswith(f"{key}_") for path in plots),
            errors,
            f"{key} generated no SVG plot",
        )

    if "liu" in expected_keys:
        validate_liu_diffusion_content(outdir / "liu" / "liu_electrothermal_sintering.csv", errors)
        require(
            "diffusion-law" in report_text or "diffusion" in report_text,
            errors,
            "report missing Liu diffusion-law content",
        )
    if "zhang" in expected_keys:
        validate_zhang_multiscale_content(
            outdir / "zhang" / "zhang_multiscale_metrics.csv",
            outdir / "zhang" / "zhang_friction_sensitivity.csv",
            errors,
        )
    if "yuan" in expected_keys:
        validate_yuan_arch_content(outdir / "yuan" / "yuan_arch_bridge_metrics.csv", errors)
    if "li" in expected_keys:
        validate_li_coated_content(outdir / "li", errors)

    if errors:
        raise ContentValidationError(errors)

    return {
        "outdir": str(outdir),
        "paper": paper,
        "papers": expected_keys,
        "acceptance_rows": len(acceptance_rows),
        "trend_checks": len(trend_checks),
        "plots": len(plots),
    }


def validate_zhang_multiscale_content(metrics_path: Path, friction_path: Path, errors: list[str]) -> None:
    metrics = read_csv_if_exists(metrics_path)
    require(bool(metrics), errors, "Zhang multiscale CSV has no rows")
    if metrics:
        missing_fields = sorted(ZHANG_REQUIRED_FIELDS - set(metrics[0]))
        require(not missing_fields, errors, f"Zhang multiscale CSV missing fields: {missing_fields}")
        chain_counts = [float_value(row.get("force_chain_count")) for row in metrics]
        local_d2 = [float_value(row.get("local_stress_inhomogeneity_d2")) for row in metrics]
        require(
            any(math.isfinite(value) and value > 0.0 for value in chain_counts),
            errors,
            "Zhang force_chain_count never becomes positive",
        )
        require(
            all(math.isfinite(value) and value > 0.0 for value in local_d2),
            errors,
            "Zhang local_stress_inhomogeneity_d2 is not positive and finite",
        )

    friction = read_csv_if_exists(friction_path)
    require(bool(friction), errors, "Zhang friction sensitivity CSV has no rows")
    if not friction:
        return
    missing_friction_fields = sorted(ZHANG_FRICTION_REQUIRED_FIELDS - set(friction[0]))
    require(
        not missing_friction_fields,
        errors,
        f"Zhang friction sensitivity CSV missing fields: {missing_friction_fields}",
    )
    friction_types = {row.get("friction_type", "") for row in friction}
    require({"wall", "particle"} <= friction_types, errors, "Zhang friction sweeps need wall and particle rows")


def validate_liu_diffusion_content(path: Path, errors: list[str]) -> None:
    rows = read_csv_if_exists(path)
    require(bool(rows), errors, "Liu electrothermal-sintering CSV has no rows")
    if not rows:
        return
    fields = set(rows[0])
    missing_fields = sorted(LIU_REQUIRED_FIELDS - fields)
    require(not missing_fields, errors, f"Liu electrothermal CSV missing fields: {missing_fields}")
    mechanisms = {row.get("dominant_diffusion_mechanism", "") for row in rows}
    require(any(mechanisms), errors, "Liu diffusion mechanism field is empty")
    thermal_gains = [float_value(row.get("neck_ratio_thermal_gain")) for row in rows]
    require(
        any(math.isfinite(value) and value > 0.0 for value in thermal_gains),
        errors,
        "Liu neck_ratio_thermal_gain never becomes positive",
    )
    diffusion_ratios = [float_value(row.get("neck_ratio_diffusion")) for row in rows]
    require(
        any(math.isfinite(value) and value > 0.0 for value in diffusion_ratios),
        errors,
        "Liu neck_ratio_diffusion never becomes positive",
    )


def validate_li_coated_content(root: Path, errors: list[str]) -> None:
    sweeps = read_csv_if_exists(root / "li_coated_powder_sweeps.csv")
    core = read_csv_if_exists(root / "li_core_shell_metrics.csv")
    temperature = read_csv_if_exists(root / "li_temperature_pressure_response.csv")
    convergence = read_csv_if_exists(root / "li_particle_count_convergence.csv")

    require_required_fields(sweeps, LI_REQUIRED_FIELDS, "Li sweep CSV", errors)
    require_required_fields(core, LI_CORE_REQUIRED_FIELDS, "Li core-shell CSV", errors)
    require_required_fields(temperature, LI_TEMPERATURE_REQUIRED_FIELDS, "Li temperature-pressure CSV", errors)
    require_required_fields(convergence, LI_CONVERGENCE_REQUIRED_FIELDS, "Li particle-count convergence CSV", errors)
    if core:
        compositions = {row.get("composition", "") for row in core}
        require(
            {"Fe", "Cu10@Fe90", "Cu20@Fe80", "Cu30@Fe70"} <= compositions,
            errors,
            "Li core-shell CSV missing required composition rows",
        )
        interface = [float_value(row.get("interface_friction_proxy")) for row in core]
        require(
            finite_end_delta(interface) < 0.0,
            errors,
            "Li interface friction does not decrease with Cu fraction",
        )
    if temperature:
        low = temperature_density(temperature, "Cu20@Fe80", 300.0, 20.0)
        high = temperature_density(temperature, "Cu20@Fe80", 300.0, 140.0)
        require(
            math.isfinite(low) and math.isfinite(high) and high > low,
            errors,
            "Li temperature-pressure CSV does not raise density with temperature at 300 MPa",
        )
    if convergence:
        early = particle_count_delta(convergence, 300.0)
        final = particle_count_delta(convergence, 600.0)
        require(
            math.isfinite(early) and math.isfinite(final) and final < early and final < 0.001,
            errors,
            "Li particle-count convergence is not demonstrated at 600 MPa",
        )


def validate_yuan_arch_content(path: Path, errors: list[str]) -> None:
    rows = read_csv_if_exists(path)
    require(bool(rows), errors, "Yuan arch-bridge CSV has no rows")
    if not rows:
        return
    missing_fields = sorted(YUAN_REQUIRED_FIELDS - set(rows[0]))
    require(not missing_fields, errors, f"Yuan arch CSV missing fields: {missing_fields}")
    obstruction = [float_value(row.get("arch_obstruction_index")) for row in rows]
    direction = [float_value(row.get("arch_direction_angle_degrees")) for row in rows]
    require(
        any(math.isfinite(value) and value > 0.0 for value in obstruction),
        errors,
        "Yuan arch obstruction never becomes positive",
    )
    require(
        all(not math.isfinite(value) or abs(value - 90.0) <= 8.0 for value in direction),
        errors,
        "Yuan arch direction deviates too far from 90 degrees",
    )


def validate_backend_selection_content(outdir: Path, errors: list[str]) -> None:
    selection = read_json_if_exists(outdir / "dem_backend_selection.json", {})
    require(selection.get("decision") == "LIGGGHTS-PUBLIC", errors, "backend selection JSON has wrong decision")
    ranked = selection.get("ranked_candidates", [])
    names = {row.get("name", "") for row in ranked if isinstance(row, dict)}
    required_names = {
        "LIGGGHTS-PUBLIC",
        "LAMMPS GRANULAR package",
        "YADE",
        "MercuryDPM",
        "Project Chrono DEM / DEM-Engine",
    }
    require(required_names <= names, errors, "backend selection JSON missing required open-source candidates")
    docs = read_text_if_exists(outdir / "dem_backend_selection.md")
    for required in required_names:
        require(required in docs, errors, f"backend selection markdown missing {required}")
    require(
        "PFC/PFC2D" in docs and "non-open-source" in docs.lower(),
        errors,
        "backend selection markdown missing non-open-source paper-tool boundary",
    )


def require_required_fields(
    rows: list[dict[str, str]],
    required: set[str],
    label: str,
    errors: list[str],
) -> None:
    require(bool(rows), errors, f"{label} has no rows")
    if not rows:
        return
    missing_fields = sorted(required - set(rows[0]))
    require(not missing_fields, errors, f"{label} missing fields: {missing_fields}")


def finite_end_delta(values: list[float]) -> float:
    finite_values = [value for value in values if math.isfinite(value)]
    if len(finite_values) < 2:
        return math.nan
    return finite_values[-1] - finite_values[0]


def temperature_density(
    rows: list[dict[str, str]],
    material: str,
    pressure_mpa: float,
    temperature_c: float,
) -> float:
    for row in rows:
        pressure = float_value(row.get("pressure_mpa"))
        temperature = float_value(row.get("temperature_c"))
        if row.get("material") == material and pressure == pressure_mpa and temperature == temperature_c:
            return float_value(row.get("relative_density"))
    return math.nan


def particle_count_delta(rows: list[dict[str, str]], pressure_mpa: float) -> float:
    values = {
        int(float_value(row.get("particle_count"))): float_value(row.get("relative_density"))
        for row in rows
        if float_value(row.get("pressure_mpa")) == pressure_mpa
    }
    if not (math.isfinite(values.get(100, math.nan)) and math.isfinite(values.get(197, math.nan))):
        return math.nan
    return abs(values[197] - values[100])


def extract_summary_papers(summary: object) -> dict[str, object]:
    if not isinstance(summary, dict):
        return {}
    nested = summary.get("papers")
    if isinstance(nested, dict):
        return {key: value for key, value in nested.items() if key in PAPER_TITLES}
    return {key: value for key, value in summary.items() if key in PAPER_TITLES}


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def read_csv_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json_if_exists(path: Path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_text_if_exists(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def int_value(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def float_value(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return math.nan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="outputs/paper_algorithm_reproduction")
    parser.add_argument("--paper", choices=["all", *PAPER_TITLES], default="all")
    args = parser.parse_args()

    try:
        result = validate_content(Path(args.outdir), paper=args.paper)
    except ContentValidationError as exc:
        print("[PAPER CONTENT] status=fail", file=sys.stderr)
        for error in exc.errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(2)

    print("[PAPER CONTENT] status=pass")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
