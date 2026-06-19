from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from .contact_metrics import (
    contact_force_components,
    direct_contact_force_fraction,
    fabric_tensor_2d,
    virial_stress_tensor_2d,
)
from .core import contact_gini, contact_participation, pearson
from .sintering import blended_neck_ratio, get_sintering_law, sintering_neck_ratio


@dataclass(frozen=True)
class Particle:
    pid: int
    x_um: float
    y_um: float
    r_um: float
    material: str = "unknown"


@dataclass(frozen=True)
class Contact:
    i: int
    j: int
    nx: float
    ny: float
    gap_um: float
    overlap_um: float
    normal_force: float
    source: str = "inferred"
    force_x: float | None = None
    force_y: float | None = None


@dataclass(frozen=True)
class ArchBridge:
    particle_ids: tuple[int, ...]
    contact_count: int
    strength: float
    direction_angle_degrees: float
    buckling_angle_degrees: float


def read_particles(path: Path, *, length_unit: str = "um") -> list[Particle]:
    scale = unit_to_um(length_unit)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    particles: list[Particle] = []
    for index, row in enumerate(rows, start=1):
        pid = int(float(row.get("particle_id") or row.get("id") or index))
        if "x_um" in row:
            x_um = float(row["x_um"])
            y_um = float(row["y_um"])
            r_um = float(row.get("r_um") or row.get("radius_um"))
        else:
            x_um = float(row["x"]) * scale
            y_um = float(row["y"]) * scale
            r_um = float(row.get("r") or row.get("radius")) * scale
        material = row.get("material") or row.get("shape") or row.get("type") or "unknown"
        particles.append(Particle(pid, x_um, y_um, r_um, material))
    return particles


def read_contacts(
    path: Path,
    particles: list[Particle],
    *,
    length_unit: str = "um",
    default_source: str = "direct",
) -> list[Contact]:
    scale = unit_to_um(length_unit)
    by_id = {particle.pid: particle for particle in particles}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    contacts: list[Contact] = []
    for row in rows:
        i = int(row_float(row, "i", "particle_i", "id_i", "id1", "particle1"))
        j = int(row_float(row, "j", "particle_j", "id_j", "id2", "particle2"))
        a = by_id.get(i)
        b = by_id.get(j)
        if not a or not b:
            continue
        branch_x = b.x_um - a.x_um
        branch_y = b.y_um - a.y_um
        dist = math.hypot(branch_x, branch_y)
        if dist == 0:
            continue
        nx = row_optional_float(row, "nx", "normal_x")
        ny = row_optional_float(row, "ny", "normal_y")
        if nx is None or ny is None:
            nx, ny = branch_x / dist, branch_y / dist
        gap = row_optional_float(row, "gap_um")
        if gap is None:
            gap_raw = row_optional_float(row, "gap")
            gap = gap_raw * scale if gap_raw is not None else dist - (a.r_um + b.r_um)
        overlap = row_optional_float(row, "overlap_um")
        if overlap is None:
            overlap_raw = row_optional_float(row, "overlap")
            overlap = overlap_raw * scale if overlap_raw is not None else max(0.0, -gap)
        fx = row_optional_float(row, "force_x", "force_x_n", "fx", "f_x")
        fy = row_optional_float(row, "force_y", "force_y_n", "fy", "f_y")
        normal_force = row_optional_float(row, "normal_force", "normal_force_n", "force_n", "fn")
        if normal_force is None:
            if fx is not None and fy is not None:
                normal_force = abs(fx * nx + fy * ny)
            else:
                normal_force = 0.0
        source = row.get("source") or default_source
        contacts.append(Contact(i, j, nx, ny, gap, overlap, normal_force, source, fx, fy))
    return contacts


def infer_contacts(
    particles: list[Particle],
    *,
    gap_tolerance_um: float = 0.0,
    normal_stiffness: float = 1.0,
    force_exponent: float = 1.5,
    min_contact_force: float = 0.0,
) -> list[Contact]:
    contacts: list[Contact] = []
    for idx, a in enumerate(particles):
        for b in particles[idx + 1 :]:
            dx = b.x_um - a.x_um
            dy = b.y_um - a.y_um
            dist = math.hypot(dx, dy)
            if dist == 0:
                continue
            gap = dist - (a.r_um + b.r_um)
            if gap > gap_tolerance_um:
                continue
            overlap = max(0.0, -gap)
            force = (
                normal_stiffness * overlap**force_exponent
                if overlap > 0
                else min_contact_force
            )
            if force <= 0 and min_contact_force <= 0:
                force = 1e-12
            contacts.append(Contact(a.pid, b.pid, dx / dist, dy / dist, gap, overlap, force))
    return contacts


def summarize_contact_network(
    particles: list[Particle],
    contacts: list[Contact],
    *,
    width_um: float | None = None,
    height_um: float | None = None,
) -> dict[str, float | int | None]:
    forces = [contact.normal_force for contact in contacts]
    stress_values = local_stress_yy(particles, contacts)
    virial = virial_stress_tensor_2d(particles, contacts, width_um=width_um, height_um=height_um)
    fabric = fabric_tensor_2d(contacts)
    arches = arch_bridges(particles, contacts)
    density = relative_density_2d(particles, width_um, height_um)
    return {
        "particle_count": len(particles),
        "contact_count": len(contacts),
        "direct_contact_force_fraction": direct_contact_force_fraction(contacts),
        "mean_coordination": 2.0 * len(contacts) / len(particles) if particles else 0.0,
        "relative_density_2d": density,
        "contact_gini": contact_gini(forces),
        "contact_participation": contact_participation(forces),
        "force_chain_strength_inhomogeneity_d1": contact_gini(forces),
        "local_stress_inhomogeneity_d2": normalized_inhomogeneity(stress_values),
        "arch_count": len(arches),
        "arch_mean_strength": mean([arch.strength for arch in arches]),
        "arch_mean_direction_angle_degrees": mean([arch.direction_angle_degrees for arch in arches]),
        "arch_mean_buckling_angle_degrees": mean([arch.buckling_angle_degrees for arch in arches]),
        **virial,
        **fabric,
    }


def arch_bridges(
    particles: list[Particle],
    contacts: list[Contact],
    *,
    threshold_factor: float = 0.5,
) -> list[ArchBridge]:
    if not contacts:
        return []
    by_id = {particle.pid: particle for particle in particles}
    mean_force = mean([contact.normal_force for contact in contacts]) or 0.0
    strong = [contact for contact in contacts if contact.normal_force >= threshold_factor * mean_force]
    adjacency: dict[int, list[Contact]] = {}
    for contact in strong:
        adjacency.setdefault(contact.i, []).append(contact)
        adjacency.setdefault(contact.j, []).append(contact)
    seen: set[int] = set()
    arches: list[ArchBridge] = []
    for start in sorted(adjacency):
        if start in seen:
            continue
        stack = [start]
        component: set[int] = set()
        component_contacts: list[Contact] = []
        seen.add(start)
        while stack:
            current = stack.pop()
            component.add(current)
            for contact in adjacency.get(current, []):
                component_contacts.append(contact)
                other = contact.j if contact.i == current else contact.i
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        unique_contacts = list({(min(c.i, c.j), max(c.i, c.j)): c for c in component_contacts}.values())
        if len(component) >= 3 and len(unique_contacts) >= 2:
            arches.append(build_arch(component, unique_contacts, by_id))
    return arches


def build_arch(
    component: set[int],
    contacts: list[Contact],
    by_id: dict[int, Particle],
) -> ArchBridge:
    xs = [by_id[pid].x_um for pid in component if pid in by_id]
    ys = [by_id[pid].y_um for pid in component if pid in by_id]
    dx = max(xs) - min(xs) if xs else 0.0
    dy = max(ys) - min(ys) if ys else 0.0
    direction = math.degrees(math.atan2(abs(dy), abs(dx))) if dx or dy else 0.0
    normal_angles = [math.degrees(math.atan2(contact.ny, contact.nx)) for contact in contacts]
    buckling = angle_spread(normal_angles)
    return ArchBridge(
        tuple(sorted(component)),
        len(contacts),
        sum(contact.normal_force for contact in contacts),
        direction,
        buckling,
    )


def run_electrothermal_network(
    particles: list[Particle],
    contacts: list[Contact],
    *,
    top_voltage: float = 1.0,
    bottom_voltage: float = 0.0,
    electrode_fraction: float = 0.08,
    conductance_force_scale: float = 1e-3,
    min_conductance: float = 1e-9,
    initial_temperature_k: float = 293.15,
    heat_to_temperature: float = 25.0,
    sintering_time_s: float = 1.0,
    sintering_law: str = "blended",
    sintering_rate_scale: float = 1.0,
) -> tuple[list[dict[str, float | int | str]], list[dict[str, float | int]]]:
    potentials = solve_potentials(
        particles,
        contacts,
        top_voltage=top_voltage,
        bottom_voltage=bottom_voltage,
        electrode_fraction=electrode_fraction,
        conductance_force_scale=conductance_force_scale,
        min_conductance=min_conductance,
    )
    particle_heat = {particle.pid: 0.0 for particle in particles}
    contact_rows: list[dict[str, float | int]] = []
    for contact in contacts:
        conductance = min_conductance + conductance_force_scale * contact.normal_force
        dv = potentials[contact.i] - potentials[contact.j]
        current = conductance * dv
        joule = current * current / conductance if conductance > 0 else 0.0
        particle_heat[contact.i] += joule / 2.0
        particle_heat[contact.j] += joule / 2.0
        contact_rows.append(
            {
                "i": contact.i,
                "j": contact.j,
                "normal_force": contact.normal_force,
                "conductance": conductance,
                "current": current,
                "abs_current": abs(current),
                "joule_heat": joule,
            }
        )
    particle_rows: list[dict[str, float | int | str]] = []
    for particle in particles:
        heat = particle_heat[particle.pid]
        temperature = initial_temperature_k + heat_to_temperature * heat
        if sintering_law == "blended":
            neck_ratio, mechanism, exponent = blended_neck_ratio(
                temperature_k=temperature,
                time_s=sintering_time_s,
                particle_radius_um=particle.r_um,
                reference_temperature_k=initial_temperature_k,
                rate_scale=sintering_rate_scale,
            )
            isothermal_neck, _, _ = blended_neck_ratio(
                temperature_k=initial_temperature_k,
                time_s=sintering_time_s,
                particle_radius_um=particle.r_um,
                reference_temperature_k=initial_temperature_k,
                rate_scale=sintering_rate_scale,
            )
        else:
            selected = get_sintering_law(sintering_law)
            neck_ratio = sintering_neck_ratio(
                temperature_k=temperature,
                time_s=sintering_time_s,
                particle_radius_um=particle.r_um,
                law=sintering_law,
                reference_temperature_k=initial_temperature_k,
                rate_scale=sintering_rate_scale,
            )
            isothermal_neck = sintering_neck_ratio(
                temperature_k=initial_temperature_k,
                time_s=sintering_time_s,
                particle_radius_um=particle.r_um,
                law=sintering_law,
                reference_temperature_k=initial_temperature_k,
                rate_scale=sintering_rate_scale,
            )
            mechanism = selected.name
            exponent = selected.growth_exponent
        thermal_gain = max(0.0, neck_ratio - isothermal_neck)
        particle_rows.append(
            {
                "particle_id": particle.pid,
                "potential": potentials[particle.pid],
                "heat_source": heat,
                "temperature_k": temperature,
                "dominant_diffusion_mechanism": mechanism,
                "neck_growth_exponent": exponent,
                "neck_ratio_diffusion": neck_ratio,
                "neck_ratio_thermal_gain": thermal_gain,
                "neck_ratio_proxy": neck_ratio,
            }
        )
    return particle_rows, contact_rows


def solve_potentials(
    particles: list[Particle],
    contacts: list[Contact],
    *,
    top_voltage: float,
    bottom_voltage: float,
    electrode_fraction: float,
    conductance_force_scale: float,
    min_conductance: float,
    iterations: int = 2000,
    tolerance: float = 1e-10,
) -> dict[int, float]:
    fixed = electrode_potentials(particles, top_voltage, bottom_voltage, electrode_fraction)
    adjacency: dict[int, list[tuple[int, float]]] = {particle.pid: [] for particle in particles}
    for contact in contacts:
        conductance = min_conductance + conductance_force_scale * contact.normal_force
        adjacency.setdefault(contact.i, []).append((contact.j, conductance))
        adjacency.setdefault(contact.j, []).append((contact.i, conductance))
    ymin = min((particle.y_um for particle in particles), default=0.0)
    ymax = max((particle.y_um for particle in particles), default=1.0)
    height = max(ymax - ymin, 1e-12)
    potentials = {
        particle.pid: fixed.get(
            particle.pid,
            bottom_voltage + (top_voltage - bottom_voltage) * (particle.y_um - ymin) / height,
        )
        for particle in particles
    }
    for _ in range(iterations):
        max_delta = 0.0
        for particle in particles:
            if particle.pid in fixed:
                continue
            neighbors = adjacency.get(particle.pid, [])
            weight = sum(conductance for _, conductance in neighbors)
            if weight <= 0:
                continue
            updated = sum(conductance * potentials[neighbor] for neighbor, conductance in neighbors) / weight
            max_delta = max(max_delta, abs(updated - potentials[particle.pid]))
            potentials[particle.pid] = updated
        if max_delta < tolerance:
            break
    return potentials


def electrode_potentials(
    particles: list[Particle],
    top_voltage: float,
    bottom_voltage: float,
    electrode_fraction: float,
) -> dict[int, float]:
    if not particles:
        return {}
    ymin = min(particle.y_um for particle in particles)
    ymax = max(particle.y_um for particle in particles)
    height = max(ymax - ymin, 1e-12)
    bottom_cut = ymin + electrode_fraction * height
    top_cut = ymax - electrode_fraction * height
    fixed = {particle.pid: bottom_voltage for particle in particles if particle.y_um <= bottom_cut}
    fixed.update({particle.pid: top_voltage for particle in particles if particle.y_um >= top_cut})
    if len(set(fixed.values())) < 2 and len(particles) >= 2:
        fixed[min(particles, key=lambda item: item.y_um).pid] = bottom_voltage
        fixed[max(particles, key=lambda item: item.y_um).pid] = top_voltage
    return fixed


def coupling_summary(
    contact_rows: list[dict[str, float | int]],
    particle_rows: list[dict[str, float | int]],
) -> dict[str, float | None]:
    forces = [float(row["normal_force"]) for row in contact_rows]
    currents = [float(row["abs_current"]) for row in contact_rows]
    joule = [float(row["joule_heat"]) for row in contact_rows]
    heat = [float(row["heat_source"]) for row in particle_rows]
    if all("neck_ratio_thermal_gain" in row for row in particle_rows):
        neck_field = "neck_ratio_thermal_gain"
    elif all("neck_ratio_diffusion" in row for row in particle_rows):
        neck_field = "neck_ratio_diffusion"
    else:
        neck_field = "neck_ratio_proxy"
    neck = [float(row[neck_field]) for row in particle_rows]
    return {
        "normal_force_vs_abs_current": pearson(forces, currents),
        "normal_force_vs_joule_heat": pearson(forces, joule),
        "particle_heat_vs_neck_ratio": pearson(heat, neck),
    }


def local_stress_yy(particles: list[Particle], contacts: list[Contact]) -> list[float]:
    values = {particle.pid: 0.0 for particle in particles}
    by_id = {particle.pid: particle for particle in particles}
    for contact in contacts:
        a = by_id.get(contact.i)
        b = by_id.get(contact.j)
        if not a or not b:
            continue
        branch_y = b.y_um - a.y_um
        _, force_y = contact_force_components(contact)
        contribution = abs(force_y * branch_y)
        values[contact.i] += contribution / 2.0
        values[contact.j] += contribution / 2.0
    return list(values.values())


def relative_density_2d(
    particles: list[Particle],
    width_um: float | None,
    height_um: float | None,
) -> float | None:
    if not particles:
        return None
    if width_um is None:
        width_um = max(p.x_um + p.r_um for p in particles) - min(p.x_um - p.r_um for p in particles)
    if height_um is None:
        height_um = max(p.y_um + p.r_um for p in particles) - min(p.y_um - p.r_um for p in particles)
    area = width_um * height_um
    if area <= 0:
        return None
    solid = sum(math.pi * particle.r_um * particle.r_um for particle in particles)
    return solid / area


def normalized_inhomogeneity(values: list[float]) -> float:
    clean = [value for value in values if math.isfinite(value)]
    if not clean:
        return 0.0
    avg = mean(clean)
    if avg == 0:
        return 0.0
    variance = sum((value - avg) ** 2 for value in clean) / len(clean)
    return math.sqrt(variance) / abs(avg)


def angle_spread(angles: list[float]) -> float:
    if not angles:
        return 0.0
    radians = [math.radians(angle) for angle in angles]
    sin_avg = mean([math.sin(angle) for angle in radians])
    cos_avg = mean([math.cos(angle) for angle in radians])
    resultant = min(1.0, max(0.0, math.hypot(sin_avg, cos_avg)))
    return math.degrees(math.sqrt(max(0.0, -2.0 * math.log(max(resultant, 1e-12)))))


def mean(values: list[float]) -> float | None:
    clean = [value for value in values if value is not None and math.isfinite(value)]
    return sum(clean) / len(clean) if clean else None


def unit_to_um(unit: str) -> float:
    return {"um": 1.0, "micron": 1.0, "cm": 10000.0, "m": 1e6}[unit]


def row_optional_float(row: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return float(value)
    return None


def row_float(row: dict[str, str], *keys: str) -> float:
    value = row_optional_float(row, *keys)
    if value is None:
        raise ValueError(f"missing numeric column; tried {keys}")
    return value
