from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from .core import contact_gini, contact_participation
from .network import Contact, Particle, read_contacts, read_particles
from .validation import trend_direction


DEFAULT_THRESHOLD_FACTORS = [0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
DEFAULT_MIN_CHAIN_LENGTHS = [3]


def calibrate_zhang_force_chains(
    *,
    snapshot_dir: Path,
    pressure_curve: Path,
    contact_dir: Path,
    outdir: Path,
    threshold_factors: list[float] | None = None,
    min_chain_lengths: list[int] | None = None,
    contact_glob: str = "{stage_id}_contacts.csv",
    length_unit: str = "um",
) -> dict[str, object]:
    threshold_factors = threshold_factors or DEFAULT_THRESHOLD_FACTORS
    min_chain_lengths = min_chain_lengths or DEFAULT_MIN_CHAIN_LENGTHS
    stages = read_stage_rows(pressure_curve)
    detail_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for threshold_factor in threshold_factors:
        for min_chain_length in min_chain_lengths:
            parameter_rows: list[dict[str, object]] = []
            for stage in stages:
                stage_id = str(stage["stage_id"])
                particles = read_particles(
                    snapshot_dir / f"dem_fem_handoff_{stage_id}.csv",
                    length_unit=length_unit,
                )
                contacts = read_contacts(
                    contact_dir / contact_glob.format(stage_id=stage_id),
                    particles,
                    length_unit=length_unit,
                )
                metrics = force_chain_metrics(
                    particles,
                    contacts,
                    threshold_factor=threshold_factor,
                    min_chain_length=min_chain_length,
                )
                row = {
                    "stage_id": stage_id,
                    "pressure_mpa": optional_float(stage.get("pressure_mpa")),
                    "actual_rho_total": optional_float(stage.get("actual_rho_total")),
                    "threshold_factor": threshold_factor,
                    "min_chain_length": min_chain_length,
                    **metrics,
                }
                detail_rows.append(row)
                parameter_rows.append(row)
            summary_rows.append(summarize_parameter_rows(parameter_rows))

    summary_rows.sort(key=summary_sort_key)
    for rank, row in enumerate(summary_rows, start=1):
        row["rank"] = rank

    outdir.mkdir(parents=True, exist_ok=True)
    detail_path = outdir / "zhang_force_chain_calibration.csv"
    summary_path = outdir / "zhang_force_chain_calibration_summary.csv"
    report_path = outdir / "zhang_force_chain_calibration_report.md"
    json_path = outdir / "zhang_force_chain_calibration_summary.json"
    write_csv(detail_path, detail_rows)
    write_csv(summary_path, summary_rows)
    json_path.write_text(
        json.dumps(summary_rows, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report_path.write_text(render_report(summary_rows, detail_rows), encoding="utf-8")
    return {
        "detail_csv": str(detail_path),
        "summary_csv": str(summary_path),
        "summary_json": str(json_path),
        "report": str(report_path),
        "parameter_count": len(summary_rows),
        "stage_count": len(stages),
    }


def force_chain_metrics(
    particles: list[Particle],
    contacts: list[Contact],
    *,
    threshold_factor: float,
    min_chain_length: int,
) -> dict[str, float | int | None]:
    forces = [contact.normal_force for contact in contacts]
    mean_force = mean(forces) or 0.0
    threshold = threshold_factor * mean_force
    strong = [contact for contact in contacts if contact.normal_force >= threshold]
    chains = connected_force_chains(strong, min_chain_length=min_chain_length)
    chain_strengths = [sum(contact.normal_force for contact in chain) for chain in chains]
    chain_lengths = [len({pid for contact in chain for pid in (contact.i, contact.j)}) for chain in chains]
    strong_forces = [contact.normal_force for contact in strong]
    return {
        "particle_count": len(particles),
        "contact_count": len(contacts),
        "mean_contact_force": mean_force,
        "strong_force_threshold": threshold,
        "strong_contact_count": len(strong),
        "strong_contact_fraction": len(strong) / len(contacts) if contacts else 0.0,
        "contact_participation": contact_participation(forces),
        "strong_force_participation": contact_participation(strong_forces),
        "contact_gini": contact_gini(forces),
        "strong_force_gini": contact_gini(strong_forces),
        "force_chain_count": len(chains),
        "force_chain_mean_length": mean(chain_lengths),
        "force_chain_mean_strength": mean(chain_strengths),
        "force_chain_strength_d1": normalized_std(chain_strengths),
    }


def connected_force_chains(
    contacts: list[Contact],
    *,
    min_chain_length: int,
) -> list[list[Contact]]:
    adjacency: dict[int, list[Contact]] = {}
    for contact in contacts:
        adjacency.setdefault(contact.i, []).append(contact)
        adjacency.setdefault(contact.j, []).append(contact)
    seen: set[int] = set()
    chains: list[list[Contact]] = []
    for start in sorted(adjacency):
        if start in seen:
            continue
        stack = [start]
        component: set[int] = set()
        component_contacts: dict[tuple[int, int], Contact] = {}
        seen.add(start)
        while stack:
            current = stack.pop()
            component.add(current)
            for contact in adjacency.get(current, []):
                key = (min(contact.i, contact.j), max(contact.i, contact.j))
                component_contacts[key] = contact
                other = contact.j if contact.i == current else contact.i
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        if len(component) >= min_chain_length:
            chains.append(list(component_contacts.values()))
    return chains


def summarize_parameter_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    participation = numeric_values(rows, "strong_force_participation")
    d1 = numeric_values(rows, "force_chain_strength_d1")
    chain_counts = numeric_values(rows, "force_chain_count")
    participation_trend = trend_direction(participation)
    d1_trend = trend_direction(d1)
    chain_coverage = sum(1 for value in chain_counts if value > 0) / len(rows) if rows else 0.0
    trend_score = int(participation_trend == "increasing") + int(d1_trend == "decreasing")
    status = "pass" if trend_score == 2 and chain_coverage >= 0.5 else "review"
    return {
        "threshold_factor": rows[0]["threshold_factor"] if rows else None,
        "min_chain_length": rows[0]["min_chain_length"] if rows else None,
        "status": status,
        "trend_score": trend_score,
        "chain_coverage": chain_coverage,
        "participation_trend": participation_trend,
        "participation_first": participation[0] if participation else None,
        "participation_last": participation[-1] if participation else None,
        "d1_trend": d1_trend,
        "d1_first": d1[0] if d1 else None,
        "d1_last": d1[-1] if d1 else None,
        "max_chain_count": max(chain_counts) if chain_counts else 0,
        "stage_count": len(rows),
    }


def render_report(
    summary_rows: list[dict[str, object]],
    detail_rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Zhang Force-Chain Calibration Report",
        "",
        "This report scans strong-contact thresholds and minimum chain lengths on direct contact-force stages.",
        (
            "A `pass` row is a calibration candidate, not a paper-level claim; it means the reduced run "
            "shows increasing strong-force participation and decreasing chain-strength D1 under that parameterization."
        ),
        "",
        "## Ranked Parameters",
        "",
        "| Rank | Threshold | Min Chain Length | Status | Score | Coverage | Participation Trend | D1 Trend |",
        "|---:|---:|---:|---|---:|---:|---|---|",
    ]
    for row in summary_rows:
        lines.append(
            "| {rank} | {threshold} | {length} | {status} | {score} | {coverage} | {participation} | {d1} |".format(
                rank=row.get("rank"),
                threshold=format_number(row.get("threshold_factor")),
                length=row.get("min_chain_length"),
                status=row.get("status"),
                score=row.get("trend_score"),
                coverage=format_number(row.get("chain_coverage")),
                participation=row.get("participation_trend"),
                d1=row.get("d1_trend"),
            )
        )
    lines.extend(
        [
            "",
            "## Best Parameter Stage Trace",
            "",
            "| Stage | Pressure MPa | Density | Strong Contacts | Chains | Strong Participation | D1 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    if summary_rows:
        best = summary_rows[0]
        rows = [
            row
            for row in detail_rows
            if row.get("threshold_factor") == best.get("threshold_factor")
            and row.get("min_chain_length") == best.get("min_chain_length")
        ]
        for row in rows:
            lines.append(
                "| {stage} | {pressure} | {density} | {strong} | {chains} | {participation} | {d1} |".format(
                    stage=row.get("stage_id"),
                    pressure=format_number(row.get("pressure_mpa")),
                    density=format_number(row.get("actual_rho_total")),
                    strong=row.get("strong_contact_count"),
                    chains=row.get("force_chain_count"),
                    participation=format_number(row.get("strong_force_participation")),
                    d1=format_number(row.get("force_chain_strength_d1")),
                )
            )
    lines.append("")
    return "\n".join(lines)


def read_stage_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not fieldnames:
            handle.write("")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def numeric_values(rows: list[dict[str, object]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = optional_float(row.get(field))
        if value is not None and math.isfinite(value):
            values.append(value)
    return values


def normalized_std(values: list[float]) -> float:
    clean = [value for value in values if math.isfinite(value)]
    if len(clean) <= 1:
        return 0.0
    avg = sum(clean) / len(clean)
    if avg == 0.0:
        return 0.0
    variance = sum((value - avg) ** 2 for value in clean) / len(clean)
    return math.sqrt(variance) / abs(avg)


def mean(values: list[float | int]) -> float | None:
    clean: list[float] = []
    for value in values:
        if value is None:
            continue
        number = float(value)
        if math.isfinite(number):
            clean.append(number)
    return sum(clean) / len(clean) if clean else None


def optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def summary_sort_key(row: dict[str, object]) -> tuple[int, float, float, float]:
    status_rank = 0 if row.get("status") == "pass" else 1
    score = optional_float(row.get("trend_score")) or 0.0
    coverage = optional_float(row.get("chain_coverage")) or 0.0
    threshold = optional_float(row.get("threshold_factor")) or 0.0
    return status_rank, -score, -coverage, threshold


def format_number(value: object) -> str:
    number = optional_float(value)
    if number is None:
        return "missing"
    return f"{number:.6g}"
