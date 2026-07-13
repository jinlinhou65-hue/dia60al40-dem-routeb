from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
from collections import Counter, deque
from pathlib import Path
from typing import Any

from dem_3d_percolation_plot import plot_network
from electrothermal_contact_model import build_contact_physics, load_parameter_set


DIRECT_SOURCE = "liggghts_pair_gran_local"
PARTICLE_FIELDS = {"particle_id", "material", "x_um", "y_um", "z_um", "r_um"}
CONTACT_FIELDS = {
    "i",
    "j",
    "nx",
    "ny",
    "nz",
    "force_x",
    "force_y",
    "force_z",
    "normal_force",
    "contact_point_x_um",
    "contact_point_y_um",
    "contact_point_z_um",
    "source",
    "force_unit",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite(row: dict[str, str], field: str) -> float:
    value = float(row[field])
    if not math.isfinite(value):
        raise ValueError(f"{field} must be finite")
    return value


def _require_fields(path: Path, fieldnames: list[str] | None, required: set[str]) -> None:
    missing = sorted(required - set(fieldnames or []))
    if missing:
        raise ValueError(f"{path} lacks required fields: {missing}")


def read_particles(path: Path) -> dict[int, dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        _require_fields(path, reader.fieldnames, PARTICLE_FIELDS)
        rows = list(reader)
    particles: dict[int, dict[str, Any]] = {}
    for row in rows:
        pid = int(float(row["particle_id"]))
        if pid in particles:
            raise ValueError(f"duplicate particle id {pid}")
        material = row["material"]
        if material not in {"Al", "Diamond"}:
            raise ValueError(f"unsupported material {material!r}")
        radius = _finite(row, "r_um")
        if radius <= 0:
            raise ValueError("particle radius must be positive")
        particles[pid] = {
            "particle_id": pid,
            "material": material,
            "x_um": _finite(row, "x_um"),
            "y_um": _finite(row, "y_um"),
            "z_um": _finite(row, "z_um"),
            "radius_um": radius,
        }
    if not particles:
        raise ValueError("particle handoff is empty")
    return particles


def read_direct_contacts(path: Path, particles: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        _require_fields(path, reader.fieldnames, CONTACT_FIELDS)
        raw = list(reader)
    contacts: list[dict[str, Any]] = []
    seen_pairs: set[tuple[int, int]] = set()
    for row in raw:
        if row["source"] != DIRECT_SOURCE or row["force_unit"] != "dyne":
            raise ValueError("every graph edge must be a direct LIGGGHTS contact in dyne")
        i, j = int(float(row["i"])), int(float(row["j"]))
        if i not in particles or j not in particles or i == j:
            raise ValueError(f"contact ({i}, {j}) has invalid particle ids")
        pair = (min(i, j), max(i, j))
        if pair in seen_pairs:
            raise ValueError(f"duplicate direct contact pair {pair}")
        seen_pairs.add(pair)
        normal_force_dyne = _finite(row, "normal_force")
        if normal_force_dyne <= 0:
            raise ValueError("normal force must be positive")
        normal = tuple(_finite(row, name) for name in ("nx", "ny", "nz"))
        if not math.isclose(math.sqrt(sum(value * value for value in normal)), 1.0, rel_tol=2e-3):
            raise ValueError(f"contact ({i}, {j}) normal is not unit length")
        contacts.append(
            {
                "stage_id": row.get("stage_id", "pilot_final"),
                "i": i,
                "j": j,
                "x_um": _finite(row, "contact_point_x_um"),
                "y_um": _finite(row, "contact_point_y_um"),
                "z_um": _finite(row, "contact_point_z_um"),
                "normal_force_n": normal_force_dyne * 1.0e-5,
                "source": DIRECT_SOURCE,
            }
        )
    if not contacts:
        raise ValueError("direct contact CSV is empty")
    return contacts


def raw_item_count(path: Path, label: str) -> int:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    marker = f"ITEM: NUMBER OF {label}"
    for index, line in enumerate(lines):
        if line.strip() == marker and index + 1 < len(lines):
            return int(lines[index + 1].strip())
    raise ValueError(f"{path} lacks {marker}")


def electrode_nodes(
    particles: dict[int, dict[str, Any]], final_height_um: float, tolerance_um: float
) -> tuple[set[int], set[int]]:
    bottom = {
        pid
        for pid, particle in particles.items()
        if float(particle["y_um"]) - float(particle["radius_um"]) <= tolerance_um
    }
    top = {
        pid
        for pid, particle in particles.items()
        if float(particle["y_um"]) + float(particle["radius_um"])
        >= final_height_um - tolerance_um
    }
    return bottom, top


def graph_for_threshold(
    particle_ids: set[int], rows: list[dict[str, Any]], cutoff_s: float
) -> tuple[dict[int, dict[int, tuple[float, int]]], list[int]]:
    adjacency: dict[int, dict[int, tuple[float, int]]] = {pid: {} for pid in particle_ids}
    active_indices: list[int] = []
    for index, row in enumerate(rows):
        conductance = float(row["electrical_conductance_s"])
        if conductance < cutoff_s:
            continue
        i, j = int(row["i"]), int(row["j"])
        resistance = float(row["electrical_resistance_ohm"])
        adjacency[i][j] = (resistance, index)
        adjacency[j][i] = (resistance, index)
        active_indices.append(index)
    return adjacency, active_indices


def reachable(starts: set[int], adjacency: dict[int, dict[int, tuple[float, int]]]) -> set[int]:
    seen = set(starts)
    queue = deque(starts)
    while queue:
        node = queue.popleft()
        for neighbor in adjacency[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def component_sizes(adjacency: dict[int, dict[int, tuple[float, int]]]) -> list[int]:
    unseen = set(adjacency)
    sizes: list[int] = []
    while unseen:
        start = min(unseen)
        component = reachable({start}, adjacency)
        sizes.append(len(component))
        unseen -= component
    return sorted(sizes, reverse=True)


def shortest_resistance_path(
    starts: set[int], targets: set[int], adjacency: dict[int, dict[int, tuple[float, int]]]
) -> tuple[list[int], list[int], float] | None:
    distances = {node: math.inf for node in adjacency}
    previous: dict[int, tuple[int, int]] = {}
    heap: list[tuple[float, int]] = []
    for node in starts:
        distances[node] = 0.0
        heapq.heappush(heap, (0.0, node))
    selected: int | None = None
    while heap:
        distance, node = heapq.heappop(heap)
        if distance != distances[node]:
            continue
        if node in targets:
            selected = node
            break
        for neighbor, (resistance, edge_index) in adjacency[node].items():
            candidate = distance + resistance
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                previous[neighbor] = (node, edge_index)
                heapq.heappush(heap, (candidate, neighbor))
    if selected is None:
        return None
    nodes = [selected]
    edges: list[int] = []
    while nodes[-1] not in starts:
        parent, edge_index = previous[nodes[-1]]
        nodes.append(parent)
        edges.append(edge_index)
    nodes.reverse()
    edges.reverse()
    return nodes, edges, distances[selected]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def analyze(
    particle_csv: Path,
    contact_csv: Path,
    raw_dump: Path,
    raw_local: Path,
    pilot_parameter_path: Path,
    electrothermal_parameter_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    pilot = json.loads(pilot_parameter_path.read_text(encoding="utf-8"))
    electrical = load_parameter_set(electrothermal_parameter_path)
    particles = read_particles(particle_csv)
    contacts = read_direct_contacts(contact_csv, particles)
    raw_particle_count = raw_item_count(raw_dump, "ATOMS")
    raw_contact_count = raw_item_count(raw_local, "ENTRIES")
    al_multiplier = float(pilot["electrical_analysis"]["al_al_resistance_multiplier"])
    physics_rows = build_contact_physics(
        particles, contacts, electrical, al_al_multiplier=al_multiplier
    )
    for physics, contact in zip(physics_rows, contacts):
        physics["z_um"] = contact["z_um"]
        physics["source"] = contact["source"]
    particle_z = [float(row["z_um"]) for row in particles.values()]
    contact_z = [float(row["z_um"]) for row in contacts]
    particle_z_span = max(particle_z) - min(particle_z)
    contact_z_span = max(contact_z) - min(contact_z)
    final_height = float(pilot["geometry"]["final_height_um"])
    electrode_tolerance = float(
        pilot["electrical_analysis"]["electrode_surface_tolerance_um"]
    )
    bottom, top = electrode_nodes(particles, final_height, electrode_tolerance)
    if not bottom or not top:
        raise ValueError("both geometric electrode sets must contain at least one particle")
    max_conductance = max(float(row["electrical_conductance_s"]) for row in physics_rows)
    threshold_rows: list[dict[str, Any]] = []
    threshold_graphs: dict[float, tuple[dict[int, dict[int, tuple[float, int]]], list[int]]] = {}
    threshold_paths: dict[float, tuple[list[int], list[int], float] | None] = {}
    for ratio_value in pilot["electrical_analysis"]["active_conductance_relative_thresholds"]:
        ratio = float(ratio_value)
        cutoff = ratio * max_conductance
        adjacency, active_indices = graph_for_threshold(set(particles), physics_rows, cutoff)
        bottom_reachable = reachable(bottom, adjacency)
        path_result = shortest_resistance_path(bottom, top, adjacency)
        components = component_sizes(adjacency)
        threshold_graphs[ratio] = (adjacency, active_indices)
        threshold_paths[ratio] = path_result
        threshold_rows.append(
            {
                "relative_threshold": ratio,
                "conductance_cutoff_s": cutoff,
                "active_edge_count": len(active_indices),
                "component_count": len(components),
                "largest_component_particle_count": components[0],
                "bottom_reachable_particle_count": len(bottom_reachable),
                "percolates_bottom_to_top": path_result is not None,
                "shortest_path_resistance_ohm": path_result[2] if path_result else "",
                "shortest_path_node_count": len(path_result[0]) if path_result else 0,
            }
        )
    percolating_ratios = [
        float(row["relative_threshold"])
        for row in threshold_rows
        if bool(row["percolates_bottom_to_top"])
    ]
    if len(percolating_ratios) == len(threshold_rows):
        scientific_outcome = "percolating_all_thresholds"
    elif not percolating_ratios:
        scientific_outcome = "nonpercolating_all_thresholds"
    else:
        scientific_outcome = "threshold_sensitive_percolation"
    selected_ratio = max(percolating_ratios) if percolating_ratios else max(
        float(row["relative_threshold"]) for row in threshold_rows
    )
    selected_adjacency, selected_active = threshold_graphs[selected_ratio]
    selected_path = threshold_paths[selected_ratio]
    path_nodes = selected_path[0] if selected_path else []
    path_edge_indices = selected_path[1] if selected_path else []
    path_node_rows = [
        {
            "order": order,
            "particle_id": pid,
            "material": particles[pid]["material"],
            "x_um": particles[pid]["x_um"],
            "y_um": particles[pid]["y_um"],
            "z_um": particles[pid]["z_um"],
        }
        for order, pid in enumerate(path_nodes)
    ]
    path_edge_rows = []
    for order, index in enumerate(path_edge_indices):
        row = physics_rows[index]
        path_edge_rows.append(
            {
                "order": order,
                "i": row["i"],
                "j": row["j"],
                "contact_type": row["contact_type"],
                "normal_force_n": row["normal_force_n"],
                "contact_radius_um": row["contact_radius_um"],
                "electrical_resistance_ohm": row["electrical_resistance_ohm"],
                "electrical_conductance_s": row["electrical_conductance_s"],
                "is_bottleneck": False,
            }
        )
    if path_edge_rows:
        max(path_edge_rows, key=lambda row: float(row["electrical_resistance_ohm"]))[
            "is_bottleneck"
        ] = True
    gates = [
        ("particle_z_span", "> 0 um", particle_z_span, particle_z_span > 0.0),
        ("contact_point_z_span", "> 0 um", contact_z_span, contact_z_span > 0.0),
        ("direct_contact_completeness", "= 1", 1.0, True),
        ("raw_particle_count_match", "exported = raw", len(particles), len(particles) == raw_particle_count),
        ("raw_contact_count_match", "exported = raw", len(contacts), len(contacts) == raw_contact_count),
        ("electrode_sets_nonempty", "bottom > 0 and top > 0", f"{len(bottom)}/{len(top)}", bool(bottom and top)),
        ("thresholds_recorded", "= 3", len(threshold_rows), len(threshold_rows) == 3),
    ]
    gate_rows = [
        {
            "gate_id": gate_id,
            "metric": gate_id,
            "threshold": threshold,
            "value": value,
            "status": "pass" if passed else "fail",
            "evidence_path": "percolation_summary.json",
            "interpretation": "hard data-contract gate",
        }
        for gate_id, threshold, value, passed in gates
    ]
    hard_gate_pass = all(row["status"] == "pass" for row in gate_rows)
    summary = {
        "decision": scientific_outcome if hard_gate_pass else "data_contract_fail",
        "scientific_outcome": scientific_outcome,
        "source_classification": pilot["source_classification"],
        "resistance_model": pilot["electrical_analysis"]["resistance_model"],
        "oxide_calibrated": False,
        "particle_count": len(particles),
        "direct_contact_count": len(contacts),
        "raw_particle_count": raw_particle_count,
        "raw_contact_count": raw_contact_count,
        "particle_z_span_um": particle_z_span,
        "contact_point_z_span_um": contact_z_span,
        "bottom_electrode_particle_ids": sorted(bottom),
        "top_electrode_particle_ids": sorted(top),
        "contact_type_counts": dict(Counter(str(row["contact_type"]) for row in physics_rows)),
        "max_electrical_conductance_s": max_conductance,
        "threshold_results": threshold_rows,
        "selected_path_threshold": selected_ratio,
        "selected_path_total_resistance_ohm": selected_path[2] if selected_path else None,
        "selected_path_bottleneck": next(
            (row for row in path_edge_rows if bool(row["is_bottleneck"])), None
        ),
        "hard_gate_pass": hard_gate_pass,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "percolation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    write_csv(output_dir / "threshold_results.csv", threshold_rows, list(threshold_rows[0]))
    write_csv(output_dir / "gate_table.csv", gate_rows, list(gate_rows[0]))
    write_csv(
        output_dir / "path_nodes.csv",
        path_node_rows,
        ["order", "particle_id", "material", "x_um", "y_um", "z_um"],
    )
    write_csv(
        output_dir / "path_edges.csv",
        path_edge_rows,
        [
            "order",
            "i",
            "j",
            "contact_type",
            "normal_force_n",
            "contact_radius_um",
            "electrical_resistance_ohm",
            "electrical_conductance_s",
            "is_bottleneck",
        ],
    )
    physics_fields = [
        "i",
        "j",
        "material_i",
        "material_j",
        "contact_type",
        "x_um",
        "y_um",
        "z_um",
        "normal_force_n",
        "contact_radius_um",
        "electrical_resistance_ohm",
        "electrical_conductance_s",
        "source",
    ]
    write_csv(
        output_dir / "contact_physics.csv",
        [{field: row[field] for field in physics_fields} for row in physics_rows],
        physics_fields,
    )
    plot_network(
        output_dir / "network_3d.png",
        particles,
        physics_rows,
        selected_active,
        path_edge_indices,
        bottom,
        top,
    )
    manifest = {
        "schema_version": 1,
        "decision": summary["decision"],
        "inputs": {
            path.name: sha256_file(path)
            for path in (
                particle_csv,
                contact_csv,
                raw_dump,
                raw_local,
                pilot_parameter_path,
                electrothermal_parameter_path,
            )
        },
        "outputs": {
            path.name: sha256_file(path)
            for path in sorted(output_dir.iterdir())
            if path.is_file() and path.name != "evidence_manifest.json"
        },
    }
    (output_dir / "evidence_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    if not hard_gate_pass:
        raise ValueError("one or more true-3D data-contract gates failed")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze true-3D direct-contact electrical percolation")
    parser.add_argument("--particles", type=Path, required=True)
    parser.add_argument("--contacts", type=Path, required=True)
    parser.add_argument("--raw-dump", type=Path, required=True)
    parser.add_argument("--raw-local", type=Path, required=True)
    parser.add_argument("--pilot-parameters", type=Path, required=True)
    parser.add_argument("--electrothermal-parameters", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(
        args.particles,
        args.contacts,
        args.raw_dump,
        args.raw_local,
        args.pilot_parameters,
        args.electrothermal_parameters,
        args.output_dir,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
