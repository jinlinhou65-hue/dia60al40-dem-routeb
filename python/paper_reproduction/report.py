from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

from .registry import build_manifest


PALETTE = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]


def generate_paper_report(
    outdir: Path,
    *,
    papers: list[str] | None = None,
) -> dict[str, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    requested = ["zhang", "yuan", "liu", "li"] if not papers or papers == ["all"] else papers
    plots_dir = outdir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    plot_paths = generate_plots(outdir, plots_dir, requested)
    report_path = outdir / "paper_reproduction_report.md"
    report_path.write_text(
        render_report(outdir, requested, plot_paths),
        encoding="utf-8",
    )
    return {"report": report_path, **{f"plot_{idx}": path for idx, path in enumerate(plot_paths)}}


def generate_plots(outdir: Path, plots_dir: Path, papers: list[str]) -> list[Path]:
    paths: list[Path] = []
    if "zhang" in papers:
        paths.extend(plot_zhang(outdir, plots_dir))
    if "yuan" in papers:
        paths.extend(plot_yuan(outdir, plots_dir))
    if "liu" in papers:
        paths.extend(plot_liu(outdir, plots_dir))
    if "li" in papers:
        paths.extend(plot_li(outdir, plots_dir))
    return paths


def plot_zhang(outdir: Path, plots_dir: Path) -> list[Path]:
    rows = read_csv(outdir / "zhang" / "zhang_multiscale_metrics.csv")
    if not rows:
        return []
    density = [(number(row, "pressure_mpa"), number(row, "relative_density")) for row in rows]
    inhomogeneity = [
        (
            "Gini",
            [(number(row, "pressure_mpa"), number(row, "contact_gini")) for row in rows],
        ),
        (
            "D1",
            [
                (number(row, "pressure_mpa"), number(row, "force_chain_strength_inhomogeneity_d1"))
                for row in rows
            ],
        ),
        (
            "D2",
            [(number(row, "pressure_mpa"), number(row, "local_stress_inhomogeneity_d2")) for row in rows],
        ),
    ]
    density_path = plots_dir / "zhang_density_pressure.svg"
    inhomogeneity_path = plots_dir / "zhang_inhomogeneity_pressure.svg"
    write_svg_line_chart(
        density_path,
        title="Zhang: Density Rises With Pressure",
        x_label="Pressure MPa",
        y_label="Relative density",
        series=[("relative density", density)],
    )
    write_svg_line_chart(
        inhomogeneity_path,
        title="Zhang: Contact And Stress Inhomogeneity Decrease",
        x_label="Pressure MPa",
        y_label="Inhomogeneity index",
        series=inhomogeneity,
    )
    return [density_path, inhomogeneity_path]


def plot_yuan(outdir: Path, plots_dir: Path) -> list[Path]:
    rows = read_csv(outdir / "yuan" / "yuan_arch_bridge_metrics.csv")
    if not rows:
        return []
    groups = sorted({row["shape"] for row in rows})
    arch_series = [
        (
            group,
            [(number(row, "pressure_mpa"), number(row, "arch_count")) for row in rows if row["shape"] == group],
        )
        for group in groups
    ]
    strength_series = [
        (
            group,
            [(number(row, "pressure_mpa"), number(row, "arch_mean_strength")) for row in rows if row["shape"] == group],
        )
        for group in groups
    ]
    arch_path = plots_dir / "yuan_arch_count_by_shape.svg"
    strength_path = plots_dir / "yuan_arch_strength_by_shape.svg"
    write_svg_line_chart(
        arch_path,
        title="Yuan: Arch Count Depends On Particle Shape",
        x_label="Pressure MPa",
        y_label="Arch count proxy",
        series=arch_series,
    )
    write_svg_line_chart(
        strength_path,
        title="Yuan: Arch Strength Depends On Particle Shape",
        x_label="Pressure MPa",
        y_label="Arch strength proxy",
        series=strength_series,
    )
    return [arch_path, strength_path]


def plot_liu(outdir: Path, plots_dir: Path) -> list[Path]:
    curve_rows = read_csv(outdir / "liu" / "liu_compaction_curve.csv")
    coupling_rows = read_csv(outdir / "liu" / "liu_electrothermal_sintering.csv")
    paths: list[Path] = []
    if curve_rows:
        curve_path = plots_dir / "liu_compaction_curve.svg"
        write_svg_line_chart(
            curve_path,
            title="Liu: Compaction Density Curve",
            x_label="Pressure MPa",
            y_label="Relative density",
            series=[
                (
                    "relative density",
                    [(number(row, "pressure_mpa"), number(row, "relative_density")) for row in curve_rows],
                )
            ],
        )
        paths.append(curve_path)
    if coupling_rows:
        coupling_path = plots_dir / "liu_contact_coupling.svg"
        write_svg_line_chart(
            coupling_path,
            title="Liu: Contact Force Drives Current And Neck Proxy",
            x_label="Normal force proxy",
            y_label="Response proxy",
            series=[
                (
                    "current",
                    [(number(row, "normal_force"), number(row, "current")) for row in coupling_rows],
                ),
                (
                    "neck ratio",
                    [(number(row, "normal_force"), number(row, "neck_ratio")) for row in coupling_rows],
                ),
            ],
        )
        paths.append(coupling_path)
    return paths


def plot_li(outdir: Path, plots_dir: Path) -> list[Path]:
    rows = read_csv(outdir / "li" / "li_coated_powder_sweeps.csv")
    if not rows:
        return []
    specs = [
        ("composition", "cu_fraction", "Cu fraction", "li_composition_density.svg"),
        ("temperature", "temperature_c", "Temperature C", "li_temperature_density.svg"),
        ("wall_friction", "wall_mu", "Wall friction coefficient", "li_wall_friction_density.svg"),
        ("pressing_speed", "pressing_speed", "Pressing speed", "li_pressing_speed_density.svg"),
        ("aspect_ratio", "aspect_ratio", "Aspect ratio", "li_aspect_ratio_density.svg"),
    ]
    paths: list[Path] = []
    for sweep, x_field, x_label, filename in specs:
        sweep_rows = [row for row in rows if row["sweep"] == sweep]
        if not sweep_rows:
            continue
        path = plots_dir / filename
        write_svg_line_chart(
            path,
            title=f"Li: {x_label} Sweep",
            x_label=x_label,
            y_label="Predicted relative density",
            series=[
                (
                    sweep,
                    [(number(row, x_field), number(row, "predicted_relative_density")) for row in sweep_rows],
                )
            ],
        )
        paths.append(path)
    return paths


def render_report(outdir: Path, papers: list[str], plot_paths: list[Path]) -> str:
    manifest = read_manifest(outdir, papers)
    checks = read_json(outdir / "paper_trend_checks.json", [])
    acceptance = read_csv(outdir / "paper_acceptance_summary.csv")
    summary = read_json(outdir / "summary.json", {})

    lines = [
        "# Powder Compaction Paper Reproduction Report",
        "",
        "This report is generated from the reproducible CSV/JSON outputs in this run.",
        "It is a first-pass algorithm reproduction layer: proxy data can be replaced by DEM, MPFEM, or electrothermal solver exports without changing the evidence schema.",
        "",
        "## Run Outputs",
        "",
        f"- Summary JSON: `{relative(outdir / 'summary.json', outdir)}`",
        f"- Manifest JSON: `{relative(outdir / 'paper_reproduction_manifest.json', outdir)}`",
        f"- Acceptance CSV: `{relative(outdir / 'paper_acceptance_summary.csv', outdir)}`",
        f"- Trend checks JSON: `{relative(outdir / 'paper_trend_checks.json', outdir)}`",
        "",
        "## Acceptance Summary",
        "",
        "| Paper | Status | Pass | Review | Missing | Mismatch |",
        "|---|---|---:|---:|---:|---:|",
    ]
    if acceptance:
        for row in acceptance:
            lines.append(
                f"| {row['paper']} | {row['status']} | {row['pass']} | {row['review']} | {row['missing']} | {row['mismatch']} |"
            )
    else:
        lines.append("| missing | missing | 0 | 0 | 0 | 0 |")

    lines.extend(["", "## Generated Figures", ""])
    if plot_paths:
        for path in plot_paths:
            rel = relative(path, outdir)
            lines.append(f"![{path.stem}]({rel})")
            lines.append("")
    else:
        lines.append("No plots were generated because no paper data files were found.")
        lines.append("")

    lines.extend(
        [
            "## Paper Evidence",
            "",
        ]
    )
    paper_outputs = summary.get("papers", {}) if isinstance(summary, dict) else {}
    for paper in manifest["papers"]:
        key = paper["key"]
        checks_for_paper = [check for check in checks if str(check.get("paper", "")).lower() == key]
        outputs = paper_outputs.get(key, {}).get("outputs", []) if isinstance(paper_outputs, dict) else []
        lines.extend(
            [
                f"### {paper['paper']}: {paper['title']}",
                "",
                f"- Current backend: {paper['current_backend']}",
                "- Reproduced algorithms:",
            ]
        )
        lines.extend(f"  - {item}" for item in paper["reproduced_algorithms"])
        lines.append("- Run output files:")
        if outputs:
            lines.extend(f"  - `{key}/{item}`" for item in outputs)
        else:
            lines.append("  - missing in this run")
        lines.append("- Acceptance checks:")
        if checks_for_paper:
            for check in checks_for_paper:
                lines.append(
                    f"  - {check['label']}: {check['status']} "
                    f"(expected {check['expected']}, actual {format_value(check.get('actual'))})"
                )
        else:
            lines.append("  - no checks found")
        lines.extend(["", "Next backend steps:"])
        lines.extend(f"- {item}" for item in paper["next_backend_steps"])
        lines.append("")
    return "\n".join(lines)


def write_svg_line_chart(
    path: Path,
    *,
    title: str,
    x_label: str,
    y_label: str,
    series: list[tuple[str, list[tuple[float, float]]]],
) -> None:
    clean_series = [
        (label, [(x, y) for x, y in points if math.isfinite(x) and math.isfinite(y)])
        for label, points in series
    ]
    clean_series = [(label, points) for label, points in clean_series if points]
    if not clean_series:
        return

    width = 760
    height = 460
    left = 72
    right = 26
    top = 58
    bottom = 70
    chart_w = width - left - right
    chart_h = height - top - bottom
    xs = [x for _, points in clean_series for x, _ in points]
    ys = [y for _, points in clean_series for _, y in points]
    x_min, x_max = padded_domain(min(xs), max(xs))
    y_min, y_max = padded_domain(min(ys), max(ys))

    def sx(x: float) -> float:
        return left + (x - x_min) / (x_max - x_min) * chart_w

    def sy(y: float) -> float:
        return top + chart_h - (y - y_min) / (y_max - y_min) * chart_h

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222} .axis{stroke:#333;stroke-width:1.2} .grid{stroke:#ddd;stroke-width:1} .label{font-size:13px} .title{font-size:20px;font-weight:700}</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fff"/>',
        f'<text class="title" x="{width / 2:.1f}" y="28" text-anchor="middle">{escape(title)}</text>',
    ]

    for tick in range(6):
        x = left + tick / 5 * chart_w
        value = x_min + tick / 5 * (x_max - x_min)
        lines.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + chart_h}"/>')
        lines.append(f'<text class="label" x="{x:.1f}" y="{top + chart_h + 22}" text-anchor="middle">{value:.3g}</text>')
    for tick in range(6):
        y = top + tick / 5 * chart_h
        value = y_max - tick / 5 * (y_max - y_min)
        lines.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}"/>')
        lines.append(f'<text class="label" x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{value:.3g}</text>')

    lines.append(f'<line class="axis" x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}"/>')
    lines.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}"/>')
    lines.append(f'<text class="label" x="{left + chart_w / 2:.1f}" y="{height - 18}" text-anchor="middle">{escape(x_label)}</text>')
    lines.append(
        f'<text class="label" x="20" y="{top + chart_h / 2:.1f}" text-anchor="middle" transform="rotate(-90 20 {top + chart_h / 2:.1f})">{escape(y_label)}</text>'
    )

    for idx, (label, points) in enumerate(clean_series):
        color = PALETTE[idx % len(PALETTE)]
        ordered = sorted(points)
        polyline = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in ordered)
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{polyline}"/>')
        for x, y in ordered:
            lines.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="3" fill="{color}"/>')
        legend_x = left + 18 + idx * 145
        legend_y = top - 18
        lines.append(f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 22}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<text class="label" x="{legend_x + 28}" y="{legend_y + 4}">{escape(label)}</text>')

    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def padded_domain(low: float, high: float) -> tuple[float, float]:
    if not math.isfinite(low) or not math.isfinite(high):
        return 0.0, 1.0
    if abs(high - low) < 1e-12:
        pad = max(1.0, abs(low)) * 0.1
        return low - pad, high + pad
    pad = (high - low) * 0.08
    return low - pad, high + pad


def read_manifest(outdir: Path, papers: list[str]) -> dict[str, object]:
    path = outdir / "paper_reproduction_manifest.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_manifest(papers)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def number(row: dict[str, str], field: str) -> float:
    value = row.get(field)
    if value in (None, ""):
        return math.nan
    try:
        return float(value)
    except ValueError:
        return math.nan


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def format_value(value) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)
