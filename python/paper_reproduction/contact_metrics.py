from __future__ import annotations

import math


def virial_stress_tensor_2d(
    particles,
    contacts,
    *,
    width_um: float | None,
    height_um: float | None,
) -> dict[str, float]:
    by_id = {particle.pid: particle for particle in particles}
    area = representative_area_um2(particles, width_um, height_um)
    xx = yy = xy = 0.0
    for contact in contacts:
        a = by_id.get(contact.i)
        b = by_id.get(contact.j)
        if not a or not b:
            continue
        branch_x = b.x_um - a.x_um
        branch_y = b.y_um - a.y_um
        force_x, force_y = contact_force_components(contact)
        xx += force_x * branch_x
        yy += force_y * branch_y
        xy += 0.5 * (force_x * branch_y + force_y * branch_x)
    if area <= 0.0:
        area = 1.0
    xx /= area
    yy /= area
    xy /= area
    mean_pressure = 0.5 * (xx + yy)
    von_mises = math.sqrt(max(0.0, xx * xx - xx * yy + yy * yy + 3.0 * xy * xy))
    return {
        "virial_stress_xx": xx,
        "virial_stress_yy": yy,
        "virial_stress_xy": xy,
        "virial_mean_pressure": mean_pressure,
        "virial_von_mises": von_mises,
    }


def fabric_tensor_2d(contacts) -> dict[str, float]:
    if not contacts:
        return {
            "fabric_tensor_xx": 0.0,
            "fabric_tensor_yy": 0.0,
            "fabric_tensor_xy": 0.0,
            "fabric_anisotropy": 0.0,
        }
    xx = mean([contact.nx * contact.nx for contact in contacts]) or 0.0
    yy = mean([contact.ny * contact.ny for contact in contacts]) or 0.0
    xy = mean([contact.nx * contact.ny for contact in contacts]) or 0.0
    anisotropy = math.sqrt((xx - yy) ** 2 + 4.0 * xy * xy)
    return {
        "fabric_tensor_xx": xx,
        "fabric_tensor_yy": yy,
        "fabric_tensor_xy": xy,
        "fabric_anisotropy": anisotropy,
    }


def contact_force_components(contact) -> tuple[float, float]:
    if contact.force_x is not None and contact.force_y is not None:
        return contact.force_x, contact.force_y
    return contact.normal_force * contact.nx, contact.normal_force * contact.ny


def direct_contact_force_fraction(contacts) -> float:
    if not contacts:
        return 0.0
    direct = sum(1 for contact in contacts if contact.source != "inferred")
    return direct / len(contacts)


def representative_area_um2(
    particles,
    width_um: float | None,
    height_um: float | None,
) -> float:
    if not particles:
        return 1.0
    if width_um is None:
        width_um = max(p.x_um + p.r_um for p in particles) - min(p.x_um - p.r_um for p in particles)
    if height_um is None:
        height_um = max(p.y_um + p.r_um for p in particles) - min(p.y_um - p.r_um for p in particles)
    return max(width_um * height_um, 1.0)


def mean(values: list[float]) -> float | None:
    clean = [value for value in values if value is not None and math.isfinite(value)]
    return sum(clean) / len(clean) if clean else None
