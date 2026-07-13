from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return next(csv.reader(handle))


def column_span(path: Path, column: str) -> float | None:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        if column not in (rows.fieldnames or []):
            return None
        values = [float(row[column]) for row in rows]
    return max(values) - min(values) if values else 0.0


def audit(deck_path: Path, particle_csv: Path, contact_csv: Path) -> dict[str, Any]:
    deck = deck_path.read_text(encoding="utf-8", errors="replace")
    particle_header = csv_header(particle_csv)
    contact_header = csv_header(contact_csv)
    set_z_zero_count = len(re.findall(r"^set\s+group\s+all\s+z\s+0(?:\.0+)?\s*$", deck, re.MULTILINE))
    zlock = bool(re.search(r"^fix\s+zlock\s+all\s+setforce\s+NULL\s+NULL\s+0(?:\.0+)?\s*$", deck, re.MULTILINE))
    dumps_particle_z = bool(
        re.search(r"^dump\s+\S+\s+all\s+custom\s+.*\bid\s+type\s+x\s+y\s+z\b", deck, re.MULTILINE)
    )
    computes_contact_point = bool(
        re.search(
            r"^compute\s+pairContacts\s+all\s+pair/gran/local\s+id\s+force\s+force_normal\s+delta\s+contactPoint\s*$",
            deck,
            re.MULTILINE,
        )
    )
    dumps_thirteen_contact_components = bool(
        re.search(r"c_pairContacts\[13\]", deck)
    )
    particle_z_span = column_span(particle_csv, "z_um")
    contact_z_span = column_span(contact_csv, "contact_point_z_um")
    strict_quasi_2d = zlock and set_z_zero_count >= 1
    source_has_3d_schema = "z_um" in particle_header and "contact_point_z_um" in contact_header
    source_has_nonzero_depth = (
        source_has_3d_schema
        and particle_z_span is not None
        and particle_z_span > 0.0
        and contact_z_span is not None
        and contact_z_span > 0.0
    )
    result = {
        "decision": "true_3d_pilot_required",
        "deck_classification": "strict_quasi_2d" if strict_quasi_2d else "not_proven_quasi_2d",
        "raw_output_capability": {
            "particle_dump_requests_z": dumps_particle_z,
            "contact_compute_requests_contact_point": computes_contact_point,
            "contact_dump_requests_13_components": dumps_thirteen_contact_components,
        },
        "dimensional_constraints": {
            "zlock_setforce_present": zlock,
            "set_all_z_zero_count": set_z_zero_count,
        },
        "archived_stage04_source": {
            "particle_columns": particle_header,
            "contact_columns": contact_header,
            "has_3d_schema": source_has_3d_schema,
            "particle_z_span_um": particle_z_span,
            "contact_point_z_span_um": contact_z_span,
            "has_nonzero_depth_evidence": source_has_nonzero_depth,
        },
        "source_hashes": {
            "liggghts_deck": file_sha256(deck_path),
            "particle_csv": file_sha256(particle_csv),
            "contact_csv": file_sha256(contact_csv),
        },
        "interpretation": (
            "The solver deck can write z and the thirteenth contact component, but it explicitly "
            "zeros particle z force and positions. The archived Stage 04 CSVs also omit z. No "
            "three-dimensional electrical-percolation claim can be recovered from these files."
        ),
        "next_action": (
            "Keep z in future handoff/contact exports and run a preregistered true-3D lightweight "
            "DEM pilot before oxide-resistance calibration or Stage 06 coupling."
        ),
    }
    if not (dumps_particle_z and computes_contact_point and dumps_thirteen_contact_components):
        raise ValueError("the current deck does not expose all raw z-capable output fields")
    if not strict_quasi_2d:
        raise ValueError("the current deck was expected to be a strict quasi-2D baseline")
    if source_has_nonzero_depth:
        raise ValueError("archived Stage 04 source unexpectedly contains nonzero 3D evidence")
    return result


def write_report(path: Path, result: dict[str, Any]) -> None:
    raw = result["raw_output_capability"]
    constraints = result["dimensional_constraints"]
    archived = result["archived_stage04_source"]
    lines = [
        "# Stage 04 Three-Dimensional Readiness Audit",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Particle dump requests z | `{raw['particle_dump_requests_z']}` |",
        f"| Contact dump requests 13 components | `{raw['contact_dump_requests_13_components']}` |",
        f"| z-force lock present | `{constraints['zlock_setforce_present']}` |",
        f"| Explicit set-all-z-zero count | `{constraints['set_all_z_zero_count']}` |",
        f"| Archived Stage 04 source has z schema | `{archived['has_3d_schema']}` |",
        f"| Archived source has nonzero depth | `{archived['has_nonzero_depth_evidence']}` |",
        "",
        "## Interpretation",
        "",
        result["interpretation"],
        "",
        "## Next Action",
        "",
        result["next_action"],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit whether current DEM evidence supports 3D percolation")
    parser.add_argument("deck", type=Path)
    parser.add_argument("particle_csv", type=Path)
    parser.add_argument("contact_csv", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("output_report", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = audit(args.deck, args.particle_csv, args.contact_csv)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    write_report(args.output_report, result)
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
