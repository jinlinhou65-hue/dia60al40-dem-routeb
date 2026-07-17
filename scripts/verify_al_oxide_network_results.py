from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


NUMERIC_FIELDS = (
    "equivalent_resistance_ohm",
    "total_power_w_fixed_voltage",
    "total_power_w_fixed_current",
    "relative_kcl_residual",
    "relative_power_balance_error",
    "shortest_path_resistance_ohm",
)
EXACT_FIELDS = (
    "model",
    "shortest_path_nodes",
    "shortest_path_node_count",
    "field_ge_4e8_edge_count",
    "field_ge_5e8_edge_count",
    "top_5_joule_edge_ids",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def verify(candidate: Path, reference: Path) -> dict[str, Any]:
    candidate_summary = json.loads((candidate / "network_summary.json").read_text(encoding="utf-8"))
    reference_summary = json.loads((reference / "network_summary.json").read_text(encoding="utf-8"))
    required = {
        "decision": "bounded_oxide_network_sensitivity_pass",
        "calibrated": False,
        "particle_count": 96,
        "direct_contact_count": 115,
        "al_al_edge_count": 50,
        "scenario_count": 18,
        "all_gate_pass": True,
    }
    for key, expected in required.items():
        if candidate_summary.get(key) != expected:
            raise ValueError(f"candidate summary {key}={candidate_summary.get(key)!r}, expected {expected!r}")
        if reference_summary.get(key) != expected:
            raise ValueError(f"reference summary {key}={reference_summary.get(key)!r}, expected {expected!r}")
    candidate_gates = read_csv(candidate / "gate_table.csv")
    reference_gates = read_csv(reference / "gate_table.csv")
    if not candidate_gates or any(row["status"] != "pass" for row in candidate_gates):
        raise ValueError("candidate has a non-passing preregistered gate")
    if [(row["gate_id"], row["status"]) for row in candidate_gates] != [
        (row["gate_id"], row["status"]) for row in reference_gates
    ]:
        raise ValueError("candidate and reference gate identities differ")
    candidate_rows = {row["scenario_id"]: row for row in read_csv(candidate / "scenarios.csv")}
    reference_rows = {row["scenario_id"]: row for row in read_csv(reference / "scenarios.csv")}
    if set(candidate_rows) != set(reference_rows) or len(candidate_rows) != 18:
        raise ValueError("candidate scenario identities differ from the archived reference")
    maximum_relative_difference = 0.0
    for scenario_id in sorted(candidate_rows):
        observed, expected = candidate_rows[scenario_id], reference_rows[scenario_id]
        for field in EXACT_FIELDS:
            if observed[field] != expected[field]:
                raise ValueError(f"{scenario_id} exact field {field} differs")
        for field in NUMERIC_FIELDS:
            observed_value, expected_value = float(observed[field]), float(expected[field])
            scale = max(abs(observed_value), abs(expected_value), 1e-300)
            relative_difference = abs(observed_value - expected_value) / scale
            maximum_relative_difference = max(maximum_relative_difference, relative_difference)
            if not math.isclose(observed_value, expected_value, rel_tol=1e-10, abs_tol=1e-18):
                raise ValueError(
                    f"{scenario_id} numeric field {field} differs: {observed_value} vs {expected_value}"
                )
    result = {
        "decision": "oxide_network_reference_match",
        "scenario_count": len(candidate_rows),
        "gate_count": len(candidate_gates),
        "maximum_relative_numeric_difference": maximum_relative_difference,
        "calibrated": False,
    }
    (candidate / "reference_verification.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare an Al-oxide network rerun with archived machine evidence")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.candidate, args.reference), indent=2))


if __name__ == "__main__":
    main()
