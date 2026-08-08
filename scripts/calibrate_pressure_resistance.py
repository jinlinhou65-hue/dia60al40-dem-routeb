from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import NormalDist
from typing import Any


class DataContractError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_value(raw: str, spec: dict[str, Any], row_number: int) -> Any:
    value = raw.strip()
    name = spec["name"]
    if not value:
        if spec.get("required"):
            raise DataContractError(f"row {row_number}: required field {name} is blank")
        return None
    try:
        if spec["type"] == "number":
            parsed: Any = float(value)
            if not math.isfinite(parsed):
                raise ValueError
        elif spec["type"] == "integer":
            parsed = int(value)
        elif spec["type"] == "date":
            parsed = date.fromisoformat(value).isoformat()
        else:
            parsed = value
    except (ValueError, TypeError) as exc:
        raise DataContractError(f"row {row_number}: invalid {spec['type']} in {name}: {value!r}") from exc
    if "enum" in spec and parsed not in spec["enum"]:
        raise DataContractError(f"row {row_number}: {name}={parsed!r} is not in {spec['enum']}")
    if "minimum" in spec and parsed < spec["minimum"]:
        raise DataContractError(f"row {row_number}: {name} is below {spec['minimum']}")
    if "exclusive_minimum" in spec and parsed <= spec["exclusive_minimum"]:
        raise DataContractError(f"row {row_number}: {name} must exceed {spec['exclusive_minimum']}")
    if "maximum" in spec and parsed > spec["maximum"]:
        raise DataContractError(f"row {row_number}: {name} exceeds {spec['maximum']}")
    return parsed


def values_close(field: str, left: Any, right: Any) -> bool:
    if not isinstance(left, float) or not isinstance(right, float):
        return left == right
    if field in {"al_fraction", "diamond_fraction"}:
        return math.isclose(left, right, abs_tol=1e-6)
    if field == "specimen_temperature_k":
        return math.isclose(left, right, abs_tol=1.0)
    return math.isclose(left, right, rel_tol=0.02, abs_tol=1e-12)


def validate_cross_fields(records: list[dict[str, Any]], schema: dict[str, Any]) -> None:
    rules = schema["cross_field_rules"]
    seen_records: set[str] = set()
    seen_repeat_pairs: set[tuple[str, str, int]] = set()
    conditions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        record_id = row["record_id"]
        if record_id in seen_records:
            raise DataContractError(f"duplicate record_id: {record_id}")
        seen_records.add(record_id)
        repeat_key = (row["condition_id"], row["specimen_id"], row["repeat_index"])
        if repeat_key in seen_repeat_pairs:
            raise DataContractError(f"duplicate condition/specimen/repeat tuple: {repeat_key}")
        seen_repeat_pairs.add(repeat_key)
        if not math.isclose(
            row["al_fraction"] + row["diamond_fraction"],
            1.0,
            abs_tol=float(rules["composition_sum_absolute_tolerance"]),
        ):
            raise DataContractError(f"{record_id}: Al and diamond fractions do not sum to one")
        if row["source_mode"] == "fixed_voltage" and row["applied_voltage_v"] is None:
            raise DataContractError(f"{record_id}: fixed_voltage requires applied_voltage_v")
        if row["source_mode"] == "fixed_current" and row["applied_current_a"] is None:
            raise DataContractError(f"{record_id}: fixed_current requires applied_current_a")
        lead = row["lead_contact_resistance_ohm"]
        if row["wiring_mode"] == "two_wire":
            if lead is None:
                raise DataContractError(f"{record_id}: two_wire requires lead_contact_resistance_ohm")
            if lead >= row["measured_resistance_ohm"]:
                raise DataContractError(f"{record_id}: lead/contact resistance leaves non-positive sample R")
        elif lead not in (None, 0.0):
            raise DataContractError(f"{record_id}: four_wire lead/contact resistance must be blank or zero")
        voltage, current = row["measured_voltage_v"], row["measured_current_a"]
        if voltage is not None and current is not None:
            inferred = voltage / current
            relative = abs(inferred - row["measured_resistance_ohm"]) / row["measured_resistance_ohm"]
            if relative > float(rules["voltage_current_resistance_relative_tolerance"]):
                raise DataContractError(f"{record_id}: V/I and measured resistance differ by {relative:.3%}")
        conditions[row["condition_id"]].append(row)
    for condition_id, rows in conditions.items():
        baseline = rows[0]
        for row in rows[1:]:
            for field in rules["condition_invariant_fields"]:
                if not values_close(field, baseline[field], row[field]):
                    raise DataContractError(f"condition {condition_id}: inconsistent {field}")
    histories: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        histories[(row["specimen_id"], row["cycle_index"])].append(row)
    for key, rows in histories.items():
        rows.sort(key=lambda item: item["measurement_index"])
        if len({row["measurement_index"] for row in rows}) != len(rows):
            raise DataContractError(f"history {key}: duplicate measurement_index")
        for stage, increasing in (("loading", True), ("unloading", False)):
            pressures = [row["pressure_pa"] for row in rows if row["loading_stage"] == stage]
            for previous, current in zip(pressures, pressures[1:]):
                tolerance = max(abs(previous), abs(current), 1.0) * 1e-9
                if increasing and current + tolerance < previous:
                    raise DataContractError(f"history {key}: loading pressure decreases")
                if not increasing and current - tolerance > previous:
                    raise DataContractError(f"history {key}: unloading pressure increases")


def load_records(data_path: Path, schema_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    schema = read_json(schema_path)
    specs = schema["fields"]
    expected = [spec["name"] for spec in specs]
    with data_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected:
            raise DataContractError(
                f"CSV header differs from schema; expected {expected}, observed {reader.fieldnames}"
            )
        records = [
            {spec["name"]: parse_value(raw[spec["name"]], spec, index) for spec in specs}
            for index, raw in enumerate(reader, start=2)
        ]
    validate_cross_fields(records, schema)
    return records, schema


def load_network_curve(path: Path) -> list[tuple[float, float]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.DictReader(handle) if row["model"] == "partial_rupture"]
    curve = sorted(
        (float(row["metallic_bridge_fraction"]), float(row["equivalent_resistance_ohm"]))
        for row in rows
    )
    if len(curve) != 8 or curve[0][0] != 0.0 or curve[-1][0] != 1.0:
        raise DataContractError("network curve does not contain the frozen eight-point f_m grid")
    if any(left[1] < right[1] for left, right in zip(curve, curve[1:])):
        raise DataContractError("network resistance is not nonincreasing with f_m")
    return curve


def invert_network_resistance(target: float, curve: list[tuple[float, float]]) -> dict[str, Any]:
    if target > curve[0][1]:
        return {"status": "boundary_saturated_low", "f_m": None, "f_m_low": 0.0, "f_m_high": 0.0}
    if target < curve[-1][1]:
        return {"status": "boundary_saturated_high", "f_m": None, "f_m_low": 1.0, "f_m_high": 1.0}
    for fraction, resistance in curve:
        if math.isclose(target, resistance, rel_tol=1e-12):
            return {"status": "grid_exact", "f_m": fraction, "f_m_low": fraction, "f_m_high": fraction}
    for (low_f, high_r), (high_f, low_r) in zip(curve, curve[1:]):
        if high_r >= target >= low_r:
            if low_f == 0.0:
                return {
                    "status": "zero_bridge_interval_only",
                    "f_m": None,
                    "f_m_low": 0.0,
                    "f_m_high": high_f,
                }
            weight = (math.log(high_r) - math.log(target)) / (math.log(high_r) - math.log(low_r))
            estimate = math.exp(math.log(low_f) + weight * (math.log(high_f) - math.log(low_f)))
            return {
                "status": "log_interpolated",
                "f_m": estimate,
                "f_m_low": low_f,
                "f_m_high": high_f,
            }
    raise DataContractError("target resistance could not be bracketed")


def corrected_resistance(row: dict[str, Any]) -> float:
    lead = row["lead_contact_resistance_ohm"] or 0.0
    return row["measured_resistance_ohm"] - lead


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def analyze_condition(
    condition_id: str,
    rows: list[dict[str, Any]],
    curve: list[tuple[float, float]],
    config: dict[str, Any],
) -> dict[str, Any]:
    resistances = [corrected_resistance(row) for row in rows]
    mean_r = statistics.fmean(resistances)
    cv = statistics.stdev(resistances) / mean_r if len(resistances) > 1 else math.nan
    specimen_count = len({row["specimen_id"] for row in rows})
    bulk_values = [
        resistance * math.pi * row["specimen_diameter_m"] ** 2 / (4.0 * row["specimen_height_m"])
        for resistance, row in zip(resistances, rows)
    ]
    result: dict[str, Any] = {
        "condition_id": condition_id,
        "data_origin": rows[0]["data_origin"],
        "record_count": len(rows),
        "independent_specimen_count": specimen_count,
        "pressure_pa": statistics.fmean(row["pressure_pa"] for row in rows),
        "loading_stage": rows[0]["loading_stage"],
        "mean_corrected_resistance_ohm": mean_r,
        "replicate_cv": cv,
        "mean_geometry_normalized_resistivity_ohm_m": statistics.fmean(bulk_values),
        "inversion_status": "not_run",
        "f_m": None,
        "f_m_confidence_low": None,
        "f_m_confidence_high": None,
        "leave_one_out_max_relative_residual": None,
    }
    scale = config.get("specimen_resistance_scale_factor")
    if scale is None:
        result["inversion_status"] = "not_identifiable_missing_scale"
        return result
    inversion = invert_network_resistance(mean_r / float(scale), curve)
    result["inversion_status"] = inversion["status"]
    result["f_m"] = inversion["f_m"]
    result["f_m_confidence_low"] = inversion["f_m_low"]
    result["f_m_confidence_high"] = inversion["f_m_high"]
    if inversion["f_m"] is None:
        return result
    loo_residuals = []
    if len(resistances) > 1:
        for index, held_out in enumerate(resistances):
            training_mean = statistics.fmean(resistances[:index] + resistances[index + 1 :])
            loo_residuals.append(abs(held_out - training_mean) / held_out)
        result["leave_one_out_max_relative_residual"] = max(loo_residuals)
    rng = random.Random(int(config["bootstrap_seed"]) + sum(map(ord, condition_id)))
    estimates = []
    for _ in range(int(config["bootstrap_resamples"])):
        sampled_resistances = []
        for _ in resistances:
            sampled_row = rng.choice(rows)
            sampled_value = rng.gauss(
                corrected_resistance(sampled_row),
                sampled_row["resistance_standard_uncertainty_ohm"],
            )
            sampled_resistances.append(max(sampled_value, 1e-300))
        sample_mean = statistics.fmean(sampled_resistances)
        sampled = invert_network_resistance(sample_mean / float(scale), curve)
        if sampled["f_m"] is not None:
            estimates.append(float(sampled["f_m"]))
    if estimates:
        alpha = 1.0 - float(config["confidence_level"])
        result["f_m_confidence_low"] = min(
            float(result["f_m_confidence_low"]), percentile(estimates, alpha / 2.0)
        )
        result["f_m_confidence_high"] = max(
            float(result["f_m_confidence_high"]), percentile(estimates, 1.0 - alpha / 2.0)
        )
    relative_u = config.get("scale_relative_standard_uncertainty")
    if relative_u is not None and float(relative_u) > 0.0:
        z_value = NormalDist().inv_cdf(0.5 + float(config["confidence_level"]) / 2.0)
        for uncertain_scale in (
            float(scale) * max(1e-12, 1.0 - z_value * float(relative_u)),
            float(scale) * (1.0 + z_value * float(relative_u)),
        ):
            uncertain = invert_network_resistance(mean_r / uncertain_scale, curve)
            result["f_m_confidence_low"] = min(
                float(result["f_m_confidence_low"]), float(uncertain["f_m_low"])
            )
            result["f_m_confidence_high"] = max(
                float(result["f_m_confidence_high"]), float(uncertain["f_m_high"])
            )
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else [
        "condition_id", "data_origin", "record_count", "independent_specimen_count", "pressure_pa",
        "loading_stage", "mean_corrected_resistance_ohm", "replicate_cv",
        "mean_geometry_normalized_resistivity_ohm_m", "inversion_status", "f_m",
        "f_m_confidence_low", "f_m_confidence_high", "leave_one_out_max_relative_residual",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def calibrate(
    data_path: Path,
    schema_path: Path,
    config_path: Path,
    scenarios_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    records, schema = load_records(data_path, schema_path)
    config = read_json(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    if config.get("forbid_synthetic_physical_calibration") is not True:
        raise DataContractError("forbid_synthetic_physical_calibration must remain true")
    if config.get("network_model") != "partial_rupture":
        raise DataContractError("only the preregistered partial_rupture curve is accepted")
    if not 0.0 < float(config["confidence_level"]) < 1.0:
        raise DataContractError("confidence_level must lie in (0,1)")
    if int(config["bootstrap_resamples"]) < 1:
        raise DataContractError("bootstrap_resamples must be positive")
    origins = sorted({row["data_origin"] for row in records})
    if len(origins) > 1:
        raise DataContractError("experiment and synthetic_test rows may not be mixed")
    scale = config.get("specimen_resistance_scale_factor")
    if scale is not None:
        if float(scale) <= 0.0:
            raise DataContractError("specimen_resistance_scale_factor must be positive")
        if not config.get("scale_factor_source"):
            raise DataContractError("a non-null scale factor requires scale_factor_source")
        relative_u = config.get("scale_relative_standard_uncertainty")
        if relative_u is None or not 0.0 <= float(relative_u) < 1.0:
            raise DataContractError("a non-null scale factor requires relative uncertainty in [0,1)")
    curve = load_network_curve(scenarios_path)
    accepted = [row for row in records if row["quality_flag"] == "accepted"]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        grouped[row["condition_id"]].append(row)
    results = [analyze_condition(key, grouped[key], curve, config) for key in sorted(grouped)]
    blockers: list[str] = []
    minimum = int(config["minimum_independent_specimens_per_condition"])
    if not records:
        status = "awaiting_real_experiment_data"
    elif not accepted:
        status = "not_identifiable_no_accepted_rows"
    else:
        if scale is None:
            blockers.append("missing_independent_specimen_scale_factor")
        if any(row["independent_specimen_count"] < minimum for row in results):
            blockers.append("insufficient_independent_specimens")
        if any(row["inversion_status"].startswith("boundary_") or row["inversion_status"] == "zero_bridge_interval_only" for row in results):
            blockers.append("boundary_or_zero_bridge_interval")
        if any(row["replicate_cv"] > float(config["maximum_replicate_cv"]) for row in results):
            blockers.append("replicate_cv_exceeds_gate")
        residual_limit = float(config["maximum_leave_one_out_relative_residual"])
        if any(
            row["leave_one_out_max_relative_residual"] is not None
            and row["leave_one_out_max_relative_residual"] > residual_limit
            for row in results
        ):
            blockers.append("leave_one_out_residual_exceeds_gate")
        if scale is None:
            status = "not_identifiable_missing_scale"
        elif origins == ["synthetic_test"]:
            status = "synthetic_validation_only"
        elif blockers:
            status = "not_identifiable_" + blockers[0]
        else:
            status = "experimentally_calibrated_within_preregistered_contract"
    calibrated = status == "experimentally_calibrated_within_preregistered_contract"
    summary = {
        "schema_version": 1,
        "status": status,
        "calibrated": calibrated,
        "row_count": len(records),
        "accepted_row_count": len(accepted),
        "condition_count": len(results),
        "data_origins": origins,
        "blockers": blockers,
        "network_model": config["network_model"],
        "specimen_resistance_scale_factor": scale,
        "claim_boundary": schema["claim_boundary"],
    }
    validation = {
        "status": "contract_valid",
        "row_count": len(records),
        "field_count": len(schema["fields"]),
        "data_origins": origins,
    }
    write_csv(output_dir / "condition_results.csv", results)
    (output_dir / "calibration_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    (output_dir / "validation_report.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    report = [
        "# Pressure-resistance calibration result",
        "",
        f"Status: `{status}`",
        f"Calibrated: `{str(calibrated).lower()}`",
        f"Rows/conditions: `{len(records)} / {len(results)}`",
        "",
        schema["claim_boundary"],
    ]
    if blockers:
        report.extend(["", "Blockers: " + ", ".join(blockers)])
    (output_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "status": status,
        "implementation": {"calibrate_pressure_resistance.py": sha256_file(Path(__file__))},
        "inputs": {
            path.name: sha256_file(path)
            for path in (data_path, schema_path, config_path, scenarios_path)
        },
        "outputs": {
            name: sha256_file(output_dir / name)
            for name in (
                "calibration_summary.json",
                "condition_results.csv",
                "validation_report.json",
                "report.md",
            )
        },
    }
    (output_dir / "evidence_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and invert pressure-resistance experiments")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--network-scenarios", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(calibrate(args.data, args.schema, args.config, args.network_scenarios, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
