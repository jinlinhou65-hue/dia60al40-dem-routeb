from __future__ import annotations

import csv
import json
import math
from collections import Counter, deque
from pathlib import Path
from typing import Any


DIRECT_CONTACT_SOURCE = "liggghts_pair_gran_local"


def load_parameter_set(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported electrothermal parameter schema")
    for name in ("Al", "Diamond"):
        material = data["materials"][name]
        for key in (
            "electrical_resistivity_ohm_m",
            "thermal_conductivity_w_mk",
            "young_modulus_pa",
        ):
            if float(material[key]) <= 0:
                raise ValueError(f"{name}.{key} must be positive")
        if not 0 <= float(material["poisson_ratio"]) < 0.5:
            raise ValueError(f"{name}.poisson_ratio is outside the elastic range")
    return data


def read_particles(path: Path) -> tuple[dict[int, dict[str, Any]], float]:
    with path.open(newline="", encoding="utf-8") as handle:
        raw = list(csv.DictReader(handle))
    if not raw:
        raise ValueError("particle CSV is empty")
    heights = {float(row["current_height_um"]) for row in raw}
    if len(heights) != 1:
        raise ValueError("particle CSV contains inconsistent current_height_um values")
    particles: dict[int, dict[str, Any]] = {}
    for row in raw:
        particle_id = int(row["particle_id"])
        material = row["material"]
        if material not in {"Al", "Diamond"}:
            raise ValueError(f"unsupported material {material!r}")
        particles[particle_id] = {
            "particle_id": particle_id,
            "material": material,
            "x_um": float(row["x_um"]),
            "y_um": float(row["y_um"]),
            "radius_um": float(row["r_um"]),
        }
    return particles, heights.pop()


def read_contacts(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        raw = list(csv.DictReader(handle))
    contacts: list[dict[str, Any]] = []
    for row in raw:
        if row.get("source") != DIRECT_CONTACT_SOURCE or row.get("force_unit") != "dyne":
            raise ValueError("contacts must be direct LIGGGHTS pair/gran/local rows in dyne")
        force_n = float(row["normal_force"]) * 1.0e-5
        if not math.isfinite(force_n) or force_n <= 0:
            raise ValueError("contact normal force must be finite and positive")
        contacts.append(
            {
                "stage_id": row["stage_id"],
                "i": int(row["i"]),
                "j": int(row["j"]),
                "x_um": float(row["contact_point_x_um"]),
                "y_um": float(row["contact_point_y_um"]),
                "normal_force_n": force_n,
            }
        )
    if not contacts:
        raise ValueError("contact CSV is empty")
    return contacts


def _pair_name(first: str, second: str) -> str:
    if first == second:
        return f"{first}-{second}"
    return "Al-Diamond"


def build_contact_physics(
    particles: dict[int, dict[str, Any]],
    contacts: list[dict[str, Any]],
    parameters: dict[str, Any],
    *,
    al_al_multiplier: float,
) -> list[dict[str, Any]]:
    if al_al_multiplier < 1:
        raise ValueError("Al-Al resistance multiplier must be at least one")
    materials = parameters["materials"]
    h_interface = float(parameters["contact_model"]["al_diamond_boundary_conductance_w_m2k"])
    warning_fraction = float(parameters["contact_model"]["hertz_contact_radius_warning_fraction"])
    rows: list[dict[str, Any]] = []
    for contact in contacts:
        first = particles[contact["i"]]
        second = particles[contact["j"]]
        mat1 = materials[first["material"]]
        mat2 = materials[second["material"]]
        radius1_m = first["radius_um"] * 1.0e-6
        radius2_m = second["radius_um"] * 1.0e-6
        reduced_radius_m = 1.0 / (1.0 / radius1_m + 1.0 / radius2_m)
        reduced_modulus_pa = 1.0 / (
            (1.0 - float(mat1["poisson_ratio"]) ** 2) / float(mat1["young_modulus_pa"])
            + (1.0 - float(mat2["poisson_ratio"]) ** 2) / float(mat2["young_modulus_pa"])
        )
        contact_radius_m = (
            3.0 * float(contact["normal_force_n"]) * reduced_radius_m / (4.0 * reduced_modulus_pa)
        ) ** (1.0 / 3.0)
        radius_fraction = contact_radius_m / min(radius1_m, radius2_m)
        pair = _pair_name(first["material"], second["material"])
        electrical_resistance_ohm = (
            float(mat1["electrical_resistivity_ohm_m"])
            + float(mat2["electrical_resistivity_ohm_m"])
        ) / (4.0 * contact_radius_m)
        if pair == "Al-Al":
            electrical_resistance_ohm *= al_al_multiplier
        thermal_resistance_k_w = (
            1.0 / float(mat1["thermal_conductivity_w_mk"])
            + 1.0 / float(mat2["thermal_conductivity_w_mk"])
        ) / (4.0 * contact_radius_m)
        interface_resistance_k_w = 0.0
        if pair == "Al-Diamond":
            interface_resistance_k_w = 1.0 / (
                h_interface * math.pi * contact_radius_m * contact_radius_m
            )
            thermal_resistance_k_w += interface_resistance_k_w
        rows.append(
            {
                **contact,
                "material_i": first["material"],
                "material_j": second["material"],
                "contact_type": pair,
                "reduced_radius_um": reduced_radius_m * 1.0e6,
                "reduced_modulus_gpa": reduced_modulus_pa / 1.0e9,
                "contact_radius_um": contact_radius_m * 1.0e6,
                "contact_radius_fraction": radius_fraction,
                "hertz_warning": radius_fraction > warning_fraction,
                "electrical_resistance_ohm": electrical_resistance_ohm,
                "electrical_conductance_s": 1.0 / electrical_resistance_ohm,
                "thermal_constriction_resistance_k_w": thermal_resistance_k_w
                - interface_resistance_k_w,
                "thermal_interface_resistance_k_w": interface_resistance_k_w,
                "thermal_resistance_k_w": thermal_resistance_k_w,
                "thermal_conductance_w_k": 1.0 / thermal_resistance_k_w,
                "al_al_resistance_multiplier": al_al_multiplier if pair == "Al-Al" else 1.0,
            }
        )
    return rows


def _reachable(starts: set[int], adjacency: dict[int, set[int]]) -> set[int]:
    seen = set(starts)
    queue = deque(starts)
    while queue:
        node = queue.popleft()
        for neighbor in adjacency.get(node, set()):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def analyze_topology(
    particles: dict[int, dict[str, Any]],
    height_um: float,
    contact_rows: list[dict[str, Any]],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    tolerance_um = 1.0e-6
    bottom = {
        pid for pid, p in particles.items() if p["y_um"] - p["radius_um"] <= tolerance_um
    }
    top = {
        pid
        for pid, p in particles.items()
        if p["y_um"] + p["radius_um"] >= height_um - tolerance_um
    }
    max_conductance = max(float(row["electrical_conductance_s"]) for row in contact_rows)
    cutoff_ratio = float(parameters["contact_model"]["electrical_active_relative_cutoff"])
    cutoff = cutoff_ratio * max_conductance
    adjacency: dict[int, set[int]] = {pid: set() for pid in particles}
    active_rows = [row for row in contact_rows if float(row["electrical_conductance_s"]) >= cutoff]
    for row in active_rows:
        adjacency[row["i"]].add(row["j"])
        adjacency[row["j"]].add(row["i"])
    reachable = _reachable(bottom, adjacency)
    warning_count = sum(bool(row["hertz_warning"]) for row in contact_rows)
    return {
        "particle_count": len(particles),
        "contact_count": len(contact_rows),
        "contact_type_counts": dict(Counter(str(row["contact_type"]) for row in contact_rows)),
        "bottom_electrode_particle_ids": sorted(bottom),
        "top_electrode_particle_ids": sorted(top),
        "electrical_active_relative_cutoff": cutoff_ratio,
        "electrical_active_conductance_cutoff_s": cutoff,
        "electrical_active_contact_count": len(active_rows),
        "electrical_active_contact_type_counts": dict(
            Counter(str(row["contact_type"]) for row in active_rows)
        ),
        "electrical_percolates_bottom_to_top": bool(reachable & top),
        "bottom_reachable_particle_count": len(reachable),
        "hertz_warning_count": warning_count,
        "hertz_warning_fraction": warning_count / len(contact_rows),
        "max_contact_radius_fraction": max(float(row["contact_radius_fraction"]) for row in contact_rows),
    }


def gaussian_property_grid(
    scenario_rows: list[dict[str, Any]],
    reference_rows: list[dict[str, Any]],
    parameters: dict[str, Any],
) -> list[dict[str, float]]:
    mapping = parameters["continuum_mapping"]
    width_um = float(mapping["width_um"])
    height_um = float(parameters["domain_height_um"])
    nx, ny = int(mapping["nx"]), int(mapping["ny"])
    kernel_um = float(mapping["kernel_um"])
    al_ref = [float(row["electrical_conductance_s"]) for row in reference_rows if row["contact_type"] == "Al-Al"]
    thermal_ref_values = [float(row["thermal_conductance_w_k"]) for row in reference_rows]
    if not al_ref:
        raise ValueError("reference contact set contains no Al-Al contacts")
    electrical_scale = sorted(al_ref)[len(al_ref) // 2]
    thermal_scale = sorted(thermal_ref_values)[len(thermal_ref_values) // 2]

    def raw_fields(rows: list[dict[str, Any]]) -> tuple[list[tuple[float, float, float, float]], float, float]:
        values: list[tuple[float, float, float, float]] = []
        e_max = t_max = 0.0
        two_kernel_sq = 2.0 * kernel_um * kernel_um
        for iy in range(ny):
            y_um = height_um * iy / (ny - 1)
            for ix in range(nx):
                x_um = width_um * ix / (nx - 1)
                raw_e = raw_t = 0.0
                for row in rows:
                    distance_sq = (x_um - float(row["x_um"])) ** 2 + (y_um - float(row["y_um"])) ** 2
                    kernel = math.exp(-distance_sq / two_kernel_sq)
                    raw_e += float(row["electrical_conductance_s"]) / electrical_scale * kernel
                    raw_t += float(row["thermal_conductance_w_k"]) / thermal_scale * kernel
                values.append((x_um, y_um, raw_e, raw_t))
                e_max, t_max = max(e_max, raw_e), max(t_max, raw_t)
        return values, e_max, t_max

    _, reference_e_max, reference_t_max = raw_fields(reference_rows)
    scenario_values, _, _ = raw_fields(scenario_rows)
    sigma_floor = float(mapping["sigma_floor_s_m"])
    sigma_peak = float(mapping["sigma_peak_s_m"])
    k_floor = float(mapping["k_floor_w_mk"])
    k_peak = float(mapping["k_peak_w_mk"])
    grid: list[dict[str, float]] = []
    for x_um, y_um, raw_e, raw_t in scenario_values:
        electrical_factor = min(1.0, max(0.0, raw_e / reference_e_max))
        thermal_factor = min(1.0, max(0.0, raw_t / reference_t_max))
        grid.append(
            {
                "x_um": x_um,
                "y_um": y_um,
                "contact_factor": electrical_factor,
                "electrical_contact_factor": electrical_factor,
                "thermal_contact_factor": thermal_factor,
                "sigma_s_m": sigma_floor + (sigma_peak - sigma_floor) * electrical_factor,
                "k_w_mk": k_floor + (k_peak - k_floor) * thermal_factor,
            }
        )
    return grid


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty CSV")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
