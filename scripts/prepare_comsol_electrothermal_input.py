from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


DIRECT_CONTACT_SOURCE = "liggghts_pair_gran_local"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_particles(path: Path) -> tuple[list[dict[str, str]], float]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("particle CSV is empty")
    heights = {float(row["current_height_um"]) for row in rows}
    if len(heights) != 1:
        raise ValueError("particle CSV contains inconsistent current_height_um values")
    return rows, heights.pop()


def read_direct_contacts(path: Path) -> list[dict[str, float | str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("contact CSV is empty")

    parsed: list[dict[str, float | str]] = []
    for row in rows:
        source = row.get("source", "")
        force_unit = row.get("force_unit", "")
        if source != DIRECT_CONTACT_SOURCE:
            raise ValueError(f"contact source must be {DIRECT_CONTACT_SOURCE!r}, got {source!r}")
        if force_unit != "dyne":
            raise ValueError(f"contact force_unit must be 'dyne', got {force_unit!r}")
        force_n = float(row["normal_force"]) * 1.0e-5
        if not math.isfinite(force_n) or force_n <= 0:
            raise ValueError("normal_force must be finite and positive")
        parsed.append(
            {
                "stage_id": row["stage_id"],
                "i": int(row["i"]),
                "j": int(row["j"]),
                "x_um": float(row["contact_point_x_um"]),
                "y_um": float(row["contact_point_y_um"]),
                "normal_force_n": force_n,
                "source": source,
            }
        )
    return parsed


def build_contact_grid(
    contacts: list[dict[str, float | str]],
    *,
    width_um: float,
    height_um: float,
    nx: int,
    ny: int,
    kernel_um: float,
    sigma_floor_s_m: float,
    sigma_peak_s_m: float,
    k_floor_w_mk: float,
    k_peak_w_mk: float,
) -> tuple[list[dict[str, float]], list[dict[str, float | int | str]], dict[str, float]]:
    if nx < 3 or ny < 3:
        raise ValueError("nx and ny must both be at least 3")
    if width_um <= 0 or height_um <= 0 or kernel_um <= 0:
        raise ValueError("domain and kernel dimensions must be positive")
    if sigma_peak_s_m <= sigma_floor_s_m or k_peak_w_mk <= k_floor_w_mk:
        raise ValueError("peak material properties must exceed floor values")

    median_force_n = statistics.median(float(row["normal_force_n"]) for row in contacts)
    weighted: list[dict[str, float | int | str]] = []
    for row in contacts:
        weight = math.sqrt(float(row["normal_force_n"]) / median_force_n)
        weighted.append({**row, "raw_weight": weight})

    dx = width_um / (nx - 1)
    dy = height_um / (ny - 1)
    raw_grid: list[tuple[float, float, float]] = []
    two_kernel_sq = 2.0 * kernel_um * kernel_um
    for iy in range(ny):
        y_um = iy * dy
        for ix in range(nx):
            x_um = ix * dx
            raw = 0.0
            for contact in weighted:
                rx = x_um - float(contact["x_um"])
                ry = y_um - float(contact["y_um"])
                raw += float(contact["raw_weight"]) * math.exp(-(rx * rx + ry * ry) / two_kernel_sq)
            raw_grid.append((x_um, y_um, raw))

    raw_max = max(value for _, _, value in raw_grid)
    if raw_max <= 0:
        raise ValueError("contact kernel field has no positive values")

    for contact in weighted:
        contact["normalized_amplitude"] = float(contact["raw_weight"]) / raw_max

    grid: list[dict[str, float]] = []
    for x_um, y_um, raw in raw_grid:
        contact_factor = min(1.0, max(0.0, raw / raw_max))
        grid.append(
            {
                "x_um": x_um,
                "y_um": y_um,
                "contact_factor": contact_factor,
                "sigma_s_m": sigma_floor_s_m
                + (sigma_peak_s_m - sigma_floor_s_m) * contact_factor,
                "k_w_mk": k_floor_w_mk + (k_peak_w_mk - k_floor_w_mk) * contact_factor,
            }
        )

    stats = {
        "median_normal_force_n": median_force_n,
        "max_kernel_sum": raw_max,
        "grid_dx_um": dx,
        "grid_dy_um": dy,
    }
    return grid, weighted, stats


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def prepare_inputs(
    particle_csv: Path,
    contact_csv: Path,
    output_dir: Path,
    *,
    width_um: float = 400.0,
    nx: int = 81,
    ny: int = 43,
    kernel_um: float = 12.0,
    sigma_floor_s_m: float = 1.0e3,
    sigma_peak_s_m: float = 1.0e5,
    k_floor_w_mk: float = 20.0,
    k_peak_w_mk: float = 100.0,
) -> dict[str, object]:
    particles, height_um = read_particles(particle_csv)
    contacts = read_direct_contacts(contact_csv)
    stage_ids = {str(row["stage_id"]) for row in contacts}
    if len(stage_ids) != 1:
        raise ValueError("contact CSV must contain exactly one stage_id")
    for contact in contacts:
        if not 0.0 <= float(contact["x_um"]) <= width_um:
            raise ValueError("contact x coordinate lies outside the model domain")
        if not 0.0 <= float(contact["y_um"]) <= height_um:
            raise ValueError("contact y coordinate lies outside the model domain")
    grid, weighted_contacts, grid_stats = build_contact_grid(
        contacts,
        width_um=width_um,
        height_um=height_um,
        nx=nx,
        ny=ny,
        kernel_um=kernel_um,
        sigma_floor_s_m=sigma_floor_s_m,
        sigma_peak_s_m=sigma_peak_s_m,
        k_floor_w_mk=k_floor_w_mk,
        k_peak_w_mk=k_peak_w_mk,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    grid_path = output_dir / "stage5_contact_property_grid.csv"
    comsol_path = output_dir / "stage5_comsol_interpolation.txt"
    source_path = output_dir / "stage5_contact_sources.csv"
    manifest_path = output_dir / "input_manifest.json"
    write_csv(
        grid_path,
        grid,
        ["x_um", "y_um", "contact_factor", "sigma_s_m", "k_w_mk"],
    )
    write_csv(
        source_path,
        weighted_contacts,
        [
            "stage_id",
            "i",
            "j",
            "x_um",
            "y_um",
            "normal_force_n",
            "source",
            "raw_weight",
            "normalized_amplitude",
        ],
    )
    with comsol_path.open("w", encoding="ascii") as handle:
        handle.write("% x_um y_um sigma_s_m k_w_mk\n")
        for row in grid:
            handle.write(
                f"{row['x_um']:.12g} {row['y_um']:.12g} "
                f"{row['sigma_s_m']:.12g} {row['k_w_mk']:.12g}\n"
            )

    manifest: dict[str, object] = {
        "model_class": "homogenized_contact_network_electrothermal_mvp",
        "fidelity": "mesoscale_smoke_model_not_particle_resolved",
        "stage_id": stage_ids.pop(),
        "domain": {"width_um": width_um, "height_um": height_um, "nx": nx, "ny": ny},
        "contact_mapping": {
            "source_required": DIRECT_CONTACT_SOURCE,
            "contact_count": len(contacts),
            "force_input_unit": "dyne",
            "force_internal_unit": "N",
            "weight_law": "sqrt(normal_force_N / median_normal_force_N)",
            "kernel": "isotropic_gaussian",
            "kernel_um": kernel_um,
            **grid_stats,
        },
        "material_field": {
            "sigma_floor_s_m": sigma_floor_s_m,
            "sigma_peak_s_m": sigma_peak_s_m,
            "k_floor_w_mk": k_floor_w_mk,
            "k_peak_w_mk": k_peak_w_mk,
            "calibration_status": "numerical_smoke_values_not_experimentally_calibrated",
        },
        "particles": {"count": len(particles)},
        "source_files": {
            "particles": {"path": str(particle_csv), "sha256": file_sha256(particle_csv)},
            "contacts": {"path": str(contact_csv), "sha256": file_sha256(contact_csv)},
        },
        "generated_files": {
            "property_grid": grid_path.name,
            "comsol_interpolation": comsol_path.name,
            "contact_sources": source_path.name,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a direct-contact property grid for COMSOL")
    parser.add_argument("particle_csv", type=Path)
    parser.add_argument("contact_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--width-um", type=float, default=400.0)
    parser.add_argument("--nx", type=int, default=81)
    parser.add_argument("--ny", type=int, default=43)
    parser.add_argument("--kernel-um", type=float, default=12.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = prepare_inputs(
        args.particle_csv,
        args.contact_csv,
        args.output_dir,
        width_um=args.width_um,
        nx=args.nx,
        ny=args.ny,
        kernel_um=args.kernel_um,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
