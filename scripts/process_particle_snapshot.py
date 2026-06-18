"""Process one particle snapshot into contact, stress, arch, and electrothermal outputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from paper_reproduction import (
    arch_bridges,
    coupling_summary,
    infer_contacts,
    read_particles,
    run_electrothermal_network,
    summarize_contact_network,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--particles", required=True, help="CSV particle snapshot or DEM-FEM handoff table")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--length-unit", choices=["um", "micron", "cm", "m"], default="um")
    parser.add_argument("--width-um", type=float, default=None)
    parser.add_argument("--height-um", type=float, default=None)
    parser.add_argument("--gap-tolerance-um", type=float, default=0.0)
    parser.add_argument("--normal-stiffness", type=float, default=1.0)
    parser.add_argument("--force-exponent", type=float, default=1.5)
    parser.add_argument("--min-contact-force", type=float, default=0.0)
    parser.add_argument("--top-voltage", type=float, default=1.0)
    parser.add_argument("--bottom-voltage", type=float, default=0.0)
    parser.add_argument("--electrode-fraction", type=float, default=0.08)
    parser.add_argument("--conductance-force-scale", type=float, default=1e-3)
    parser.add_argument("--min-conductance", type=float, default=1e-9)
    parser.add_argument("--initial-temperature-k", type=float, default=293.15)
    parser.add_argument("--heat-to-temperature", type=float, default=25.0)
    args = parser.parse_args()

    particles = read_particles(Path(args.particles), length_unit=args.length_unit)
    contacts = infer_contacts(
        particles,
        gap_tolerance_um=args.gap_tolerance_um,
        normal_stiffness=args.normal_stiffness,
        force_exponent=args.force_exponent,
        min_contact_force=args.min_contact_force,
    )
    metrics = summarize_contact_network(
        particles,
        contacts,
        width_um=args.width_um,
        height_um=args.height_um,
    )
    particle_fields, contact_fields = run_electrothermal_network(
        particles,
        contacts,
        top_voltage=args.top_voltage,
        bottom_voltage=args.bottom_voltage,
        electrode_fraction=args.electrode_fraction,
        conductance_force_scale=args.conductance_force_scale,
        min_conductance=args.min_conductance,
        initial_temperature_k=args.initial_temperature_k,
        heat_to_temperature=args.heat_to_temperature,
    )
    summary = {
        "input": str(args.particles),
        "metrics": metrics,
        "coupling": coupling_summary(contact_fields, particle_fields),
    }

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir / "contacts_inferred.csv", [asdict(contact) for contact in contacts])
    write_csv(outdir / "arch_bridges.csv", [asdict(arch) for arch in arch_bridges(particles, contacts)])
    write_csv(outdir / "electrothermal_contacts.csv", contact_fields)
    write_csv(outdir / "electrothermal_particles.csv", merge_particle_fields(particles, particle_fields))
    (outdir / "snapshot_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def merge_particle_fields(particles, fields):
    by_id = {int(row["particle_id"]): row for row in fields}
    rows = []
    for particle in particles:
        rows.append(
            {
                "particle_id": particle.pid,
                "x_um": particle.x_um,
                "y_um": particle.y_um,
                "r_um": particle.r_um,
                "material": particle.material,
                **by_id.get(particle.pid, {}),
            }
        )
    return rows


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


if __name__ == "__main__":
    main()
