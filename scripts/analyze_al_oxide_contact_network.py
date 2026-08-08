from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
from al_oxide_contact_network_plot import plot_hotspots, plot_sensitivity
DIRECT_SOURCE = "liggghts_pair_gran_local"
def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_canonical_lf(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def verify_input_contract(
    parameters: dict[str, Any], particles_path: Path, contacts_path: Path, physics_path: Path
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    contract = parameters["input_contract"]
    paths = {
        "pilot_final_particles.csv": particles_path,
        "pilot_final_direct_contacts.csv": contacts_path,
        "contact_physics.csv": physics_path,
    }
    for name, path in paths.items():
        observed_raw = sha256_file(path)
        observed_canonical = sha256_canonical_lf(path)
        expected_raw = contract["files"][name]
        expected_canonical = contract["canonical_lf_files"][name]
        if observed_raw != expected_raw and observed_canonical != expected_canonical:
            raise ValueError(
                f"SHA-256 mismatch for {name}: raw={observed_raw}, "
                f"canonical_lf={observed_canonical}; expected raw={expected_raw}, "
                f"canonical_lf={expected_canonical}"
            )
    particles = read_csv(particles_path)
    contacts = read_csv(contacts_path)
    physics = read_csv(physics_path)
    if len(particles) != int(contract["particle_count"]):
        raise ValueError("particle count does not match preregistration")
    if len(contacts) != int(contract["direct_contact_count"]):
        raise ValueError("direct-contact count does not match preregistration")
    if any(row.get("source") != DIRECT_SOURCE for row in contacts):
        raise ValueError("all source contacts must be direct LIGGGHTS contacts")
    if any(row.get("source") != DIRECT_SOURCE for row in physics):
        raise ValueError("all contact-physics rows must preserve direct-contact provenance")
    al_edges = [row for row in physics if row["contact_type"] == "Al-Al"]
    if len(al_edges) != int(contract["al_al_edge_count"]):
        raise ValueError("Al-Al edge count does not match preregistration")
    if any(row["material_i"] != "Al" or row["material_j"] != "Al" for row in al_edges):
        raise ValueError("Al-Al edge labels are inconsistent")
    return particles, contacts, al_edges


def transmitting_nodes(
    nodes: set[int], edges: list[dict[str, Any]], bottom: set[int], top: set[int]
) -> set[int]:
    adjacency = {node: set() for node in nodes}
    for edge in edges:
        i, j = int(edge["i"]), int(edge["j"])
        adjacency[i].add(j)
        adjacency[j].add(i)
    unseen = set(nodes)
    keep: set[int] = set()
    while unseen:
        start = min(unseen)
        component = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    queue.append(neighbor)
        unseen -= component
        if component & bottom and component & top:
            keep |= component
    return keep


def shortest_path(
    edges: list[dict[str, Any]], bottom: set[int], top: set[int]
) -> tuple[list[int], set[int], float]:
    adjacency: dict[int, list[tuple[int, float, int]]] = {}
    for index, edge in enumerate(edges):
        i, j = int(edge["i"]), int(edge["j"])
        resistance = float(edge["resistance_ohm"])
        adjacency.setdefault(i, []).append((j, resistance, index))
        adjacency.setdefault(j, []).append((i, resistance, index))
    distance = {node: math.inf for node in adjacency}
    previous: dict[int, tuple[int, int]] = {}
    heap: list[tuple[float, int]] = []
    for node in bottom & set(adjacency):
        distance[node] = 0.0
        heapq.heappush(heap, (0.0, node))
    selected = None
    while heap:
        value, node = heapq.heappop(heap)
        if value != distance[node]:
            continue
        if node in top:
            selected = node
            break
        for neighbor, resistance, edge_index in adjacency[node]:
            candidate = value + resistance
            if candidate < distance[neighbor]:
                distance[neighbor] = candidate
                previous[neighbor] = (node, edge_index)
                heapq.heappush(heap, (candidate, neighbor))
    if selected is None:
        raise ValueError("the frozen Al-Al graph does not connect both electrodes")
    nodes = [selected]
    edge_indices: set[int] = set()
    while nodes[-1] not in bottom:
        parent, edge_index = previous[nodes[-1]]
        nodes.append(parent)
        edge_indices.add(edge_index)
    nodes.reverse()
    return nodes, edge_indices, distance[selected]


def solve_network(
    edges: list[dict[str, Any]], bottom: set[int], top: set[int], voltage_v: float
) -> dict[str, Any]:
    if bottom & top:
        raise ValueError("bottom and top electrode sets must be disjoint")
    nodes = {int(edge[key]) for edge in edges for key in ("i", "j")}
    transport = transmitting_nodes(nodes, edges, bottom, top)
    if not transport:
        raise ValueError("no component connects bottom and top electrodes")
    transport_edges = [
        edge for edge in edges if int(edge["i"]) in transport and int(edge["j"]) in transport
    ]
    boundaries = (bottom | top) & transport
    internal = sorted(transport - boundaries)
    index = {node: position for position, node in enumerate(internal)}
    conductances = np.array([1.0 / float(edge["resistance_ohm"]) for edge in transport_edges])
    scale = float(np.max(conductances))
    matrix = np.zeros((len(internal), len(internal)), dtype=float)
    rhs = np.zeros(len(internal), dtype=float)
    boundary_voltage = {node: 0.0 for node in bottom & transport}
    boundary_voltage.update({node: voltage_v for node in top & transport})
    for edge, conductance in zip(transport_edges, conductances / scale):
        i, j = int(edge["i"]), int(edge["j"])
        for node, neighbor in ((i, j), (j, i)):
            if node not in index:
                continue
            row = index[node]
            matrix[row, row] += conductance
            if neighbor in index:
                matrix[row, index[neighbor]] -= conductance
            else:
                rhs[row] += conductance * boundary_voltage[neighbor]
    solved = np.linalg.solve(matrix, rhs) if internal else np.empty(0)
    potentials = dict(boundary_voltage)
    potentials.update({node: float(solved[index[node]]) for node in internal})
    edge_results: list[dict[str, Any]] = []
    kcl = {node: 0.0 for node in internal}
    source_current = 0.0
    total_power = 0.0
    for edge in edges:
        i, j = int(edge["i"]), int(edge["j"])
        included = i in transport and j in transport
        if included:
            conductance = 1.0 / float(edge["resistance_ohm"])
            delta_v = potentials[i] - potentials[j]
            current_i_to_j = conductance * delta_v
            power = conductance * delta_v * delta_v
            if i in kcl:
                kcl[i] += current_i_to_j
            if j in kcl:
                kcl[j] -= current_i_to_j
            if i in top:
                source_current += current_i_to_j
            if j in top:
                source_current -= current_i_to_j
            total_power += power
        else:
            delta_v = current_i_to_j = power = 0.0
        edge_results.append(
            {
                **edge,
                "included_in_transport": included,
                "delta_v_fixed_voltage": delta_v,
                "abs_current_a_fixed_voltage": abs(current_i_to_j),
                "joule_power_w_fixed_voltage": power,
            }
        )
    if source_current <= 0 or total_power <= 0:
        raise ValueError("network solution produced non-positive current or power")
    equivalent_resistance = voltage_v / source_current
    current_scale = 1.0 / source_current
    for row in edge_results:
        row["delta_v_fixed_current"] = row["delta_v_fixed_voltage"] * current_scale
        row["abs_current_a_fixed_current"] = row["abs_current_a_fixed_voltage"] * current_scale
        row["joule_power_w_fixed_current"] = row["joule_power_w_fixed_voltage"] * current_scale**2
    kcl_residual = max((abs(value) for value in kcl.values()), default=0.0) / source_current
    power_error = abs(voltage_v * source_current - total_power) / total_power
    return {
        "transport_node_count": len(transport),
        "transport_edge_count": len(transport_edges),
        "potentials": potentials,
        "edge_results": edge_results,
        "source_current_a_fixed_voltage": source_current,
        "equivalent_resistance_ohm": equivalent_resistance,
        "total_power_w_fixed_voltage": total_power,
        "total_power_w_fixed_current": equivalent_resistance,
        "relative_kcl_residual": kcl_residual,
        "relative_power_balance_error": power_error,
    }


def build_scenarios(parameters: dict[str, Any], base_edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frozen = parameters["frozen_quantities"]
    scenarios: list[dict[str, Any]] = [{"scenario_id": "clean", "model": "clean"}]
    for thickness in frozen["particle_film_thickness_m"]:
        for resistivity in frozen["film_effective_resistivity_ohm_m"]:
            scenarios.append(
                {
                    "scenario_id": f"intact_d{thickness:.0e}_rho{resistivity:.0e}",
                    "model": "intact_oxide",
                    "particle_film_thickness_m": float(thickness),
                    "film_resistivity_ohm_m": float(resistivity),
                }
            )
    primary = parameters["models"]["partial_rupture_primary"]
    for fraction in frozen["metallic_bridge_area_fraction"]:
        scenarios.append(
            {
                "scenario_id": f"partial_f{fraction:.0e}",
                "model": "partial_rupture",
                "particle_film_thickness_m": float(primary["central_film_thickness_m"]),
                "film_resistivity_ohm_m": float(primary["central_film_resistivity_ohm_m"]),
                "metallic_bridge_fraction": float(fraction),
            }
        )
    for scenario in scenarios:
        scenario_edges = []
        for base in base_edges:
            clean = float(base["clean_resistance_ohm"])
            radius_m = float(base["contact_radius_um"]) * 1e-6
            film_resistance = math.inf
            if scenario["model"] == "clean":
                resistance = clean
            else:
                thickness = 2.0 * float(scenario["particle_film_thickness_m"])
                area = math.pi * radius_m**2
                film_resistance = float(scenario["film_resistivity_ohm_m"]) * thickness / area
                if scenario["model"] == "intact_oxide":
                    resistance = clean + film_resistance
                else:
                    fraction = float(scenario["metallic_bridge_fraction"])
                    conductance = math.sqrt(fraction) / clean + (1.0 - fraction) / film_resistance
                    resistance = 1.0 / conductance
            scenario_edges.append(
                {**base, "film_resistance_ohm": film_resistance, "resistance_ohm": resistance}
            )
        scenario["edges"] = scenario_edges
    return scenarios


def analyze(parameters_path: Path, archive_dir: Path, output_dir: Path) -> dict[str, Any]:
    parameters = json.loads(parameters_path.read_text(encoding="utf-8"))
    particles_path = archive_dir / "pilot_final_particles.csv"
    contacts_path = archive_dir / "pilot_final_direct_contacts.csv"
    physics_path = archive_dir / "analysis" / "contact_physics.csv"
    summary_path = archive_dir / "analysis" / "percolation_summary.json"
    particles, _, al_rows = verify_input_contract(parameters, particles_path, contacts_path, physics_path)
    archived_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    bottom = set(map(int, archived_summary["bottom_electrode_particle_ids"]))
    top = set(map(int, archived_summary["top_electrode_particle_ids"]))
    rho_al = float(parameters["frozen_quantities"]["al_resistivity_ohm_m"])
    base_edges = []
    for index, row in enumerate(al_rows):
        radius_um = float(row["contact_radius_um"])
        clean = float(row["electrical_resistance_ohm"])
        expected_clean = rho_al / (2.0 * radius_um * 1e-6)
        if not math.isclose(clean, expected_clean, rel_tol=1e-12):
            raise ValueError("archived clean resistance is inconsistent with preregistered rho/(2a)")
        base_edges.append(
            {
                "edge_id": index,
                "i": int(row["i"]),
                "j": int(row["j"]),
                "x_um": float(row["x_um"]),
                "y_um": float(row["y_um"]),
                "z_um": float(row["z_um"]),
                "normal_force_n": float(row["normal_force_n"]),
                "contact_radius_um": radius_um,
                "clean_resistance_ohm": clean,
                "source": row["source"],
            }
        )
    scenarios = build_scenarios(parameters, base_edges)
    voltage = float(parameters["frozen_quantities"]["fixed_voltage_v"])
    edge_output: list[dict[str, Any]] = []
    scenario_output: list[dict[str, Any]] = []
    for scenario in scenarios:
        result = solve_network(scenario.pop("edges"), bottom, top, voltage)
        path_nodes, path_indices, path_resistance = shortest_path(result["edge_results"], bottom, top)
        thickness = scenario.get("particle_film_thickness_m")
        has_remaining_film = bool(thickness) and not (
            scenario["model"] == "partial_rupture"
            and float(scenario["metallic_bridge_fraction"]) == 1.0
        )
        lower_field, upper_field = parameters["frozen_quantities"]["dielectric_breakdown_field_v_m"]
        ranked = sorted(result["edge_results"], key=lambda row: row["joule_power_w_fixed_voltage"], reverse=True)
        rank_by_edge = {int(row["edge_id"]): rank for rank, row in enumerate(ranked, start=1)}
        lower_exceed = upper_exceed = 0
        for edge in result["edge_results"]:
            field = (
                abs(float(edge["delta_v_fixed_voltage"])) / (2.0 * float(thickness))
                if has_remaining_film
                else math.nan
            )
            if has_remaining_film:
                lower_exceed += field >= float(lower_field)
                upper_exceed += field >= float(upper_field)
            edge_output.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "model": scenario["model"],
                    **edge,
                    "electric_field_v_m": field,
                    "exceeds_4e8_v_m": bool(has_remaining_film and field >= float(lower_field)),
                    "exceeds_5e8_v_m": bool(has_remaining_film and field >= float(upper_field)),
                    "is_shortest_path_edge": int(edge["edge_id"]) in path_indices,
                    "joule_rank": rank_by_edge[int(edge["edge_id"])],
                }
            )
        scenario_output.append(
            {
                **scenario,
                **{key: value for key, value in result.items() if key not in {"potentials", "edge_results"}},
                "shortest_path_resistance_ohm": path_resistance,
                "shortest_path_nodes": "->".join(map(str, path_nodes)),
                "shortest_path_node_count": len(path_nodes),
                "field_ge_4e8_edge_count": lower_exceed,
                "field_ge_5e8_edge_count": upper_exceed,
                "top_5_joule_edge_ids": ";".join(str(row["edge_id"]) for row in ranked[:5]),
            }
        )
    gates = parameters["acceptance_gates"]
    intact = [row for row in scenario_output if row["model"] == "intact_oxide"]
    partial = [row for row in scenario_output if row["model"] == "partial_rupture"]
    gate_values = [
        ("input_contract", "hashes and 96/115/50", "matched", True),
        ("scenario_count", "=18", len(scenario_output), len(scenario_output) == 18),
        ("kcl_residual", f"<={gates['relative_kcl_residual_max']}", max(row["relative_kcl_residual"] for row in scenario_output), max(row["relative_kcl_residual"] for row in scenario_output) <= float(gates["relative_kcl_residual_max"])),
        ("power_balance", f"<={gates['relative_power_balance_error_max']}", max(row["relative_power_balance_error"] for row in scenario_output), max(row["relative_power_balance_error"] for row in scenario_output) <= float(gates["relative_power_balance_error_max"])),
        ("intact_not_below_clean", "all edge R>=clean", min(row["resistance_ohm"] / row["clean_resistance_ohm"] for row in edge_output if row["model"] == "intact_oxide"), all(row["resistance_ohm"] >= row["clean_resistance_ohm"] for row in edge_output if row["model"] == "intact_oxide")),
        ("fixed_voltage_monotonic", "nondecreasing with f_m", "checked", all(partial[i]["total_power_w_fixed_voltage"] <= partial[i + 1]["total_power_w_fixed_voltage"] for i in range(len(partial) - 1))),
        ("fixed_current_monotonic", "nonincreasing with f_m", "checked", all(partial[i]["total_power_w_fixed_current"] >= partial[i + 1]["total_power_w_fixed_current"] for i in range(len(partial) - 1))),
        ("network_not_shortest_path", "Req<=shortest path R", max(row["equivalent_resistance_ohm"] / row["shortest_path_resistance_ohm"] for row in scenario_output), all(row["equivalent_resistance_ohm"] <= row["shortest_path_resistance_ohm"] for row in scenario_output)),
    ]
    gate_rows = [
        {"gate_id": gate_id, "metric": gate_id, "threshold": threshold, "value": value, "status": "pass" if passed else "fail", "evidence_path": "network_summary.json", "interpretation": "preregistered numerical gate"}
        for gate_id, threshold, value, passed in gate_values
    ]
    decision = "bounded_oxide_network_sensitivity_pass" if all(row["status"] == "pass" for row in gate_rows) else "oxide_network_gate_fail"
    clean = next(row for row in scenario_output if row["model"] == "clean")
    summary = {
        "schema_version": 1,
        "decision": decision,
        "calibrated": False,
        "archive_run": int(parameters["input_contract"]["archive_run"]),
        "particle_count": len(particles),
        "direct_contact_count": int(parameters["input_contract"]["direct_contact_count"]),
        "al_al_edge_count": len(base_edges),
        "scenario_count": len(scenario_output),
        "clean_network_equivalent_resistance_ohm": clean["equivalent_resistance_ohm"],
        "clean_shortest_path_resistance_ohm": clean["shortest_path_resistance_ohm"],
        "intact_network_resistance_range_ohm": [min(row["equivalent_resistance_ohm"] for row in intact), max(row["equivalent_resistance_ohm"] for row in intact)],
        "partial_network_resistance_range_ohm": [min(row["equivalent_resistance_ohm"] for row in partial), max(row["equivalent_resistance_ohm"] for row in partial)],
        "max_relative_kcl_residual": max(row["relative_kcl_residual"] for row in scenario_output),
        "max_relative_power_balance_error": max(row["relative_power_balance_error"] for row in scenario_output),
        "all_gate_pass": all(row["status"] == "pass" for row in gate_rows),
        "claim_boundary": "bounded archived-network sensitivity; metallic bridge fraction and absolute temperature are not calibrated",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    scenario_fields: list[str] = []
    for row in scenario_output:
        for field in row:
            if field not in scenario_fields:
                scenario_fields.append(field)
    for row in scenario_output:
        for field in scenario_fields:
            row.setdefault(field, "")
    write_csv(output_dir / "scenarios.csv", scenario_output, scenario_fields)
    edge_fields = list(edge_output[0])
    write_csv(output_dir / "edge_results.csv", edge_output, edge_fields)
    write_csv(output_dir / "gate_table.csv", gate_rows, list(gate_rows[0]))
    (output_dir / "network_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    plot_sensitivity(output_dir / "oxide_network_sensitivity.png", scenario_output)
    plot_hotspots(output_dir / "oxide_network_hotspots_3d.png", particles, scenario_output, edge_output, bottom, top)
    generated_names = (
        "network_summary.json",
        "scenarios.csv",
        "edge_results.csv",
        "gate_table.csv",
        "oxide_network_sensitivity.png",
        "oxide_network_hotspots_3d.png",
    )
    manifest = {
        "schema_version": 1,
        "decision": decision,
        "implementation": {
            "analyze_al_oxide_contact_network.py": sha256_file(Path(__file__)),
            "al_oxide_contact_network_plot.py": sha256_file(
                Path(__file__).with_name("al_oxide_contact_network_plot.py")
            ),
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "inputs": {path.name: sha256_file(path) for path in (parameters_path, particles_path, contacts_path, physics_path, summary_path)},
        "outputs": {name: sha256_file(output_dir / name) for name in generated_names},
    }
    (output_dir / "evidence_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    if decision != "bounded_oxide_network_sensitivity_pass":
        raise ValueError("one or more preregistered oxide-network gates failed")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve preregistered Al-oxide resistor networks on the archived 3D graph")
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.parameters, args.archive_dir, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
