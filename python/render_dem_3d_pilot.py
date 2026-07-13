from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


UM_TO_CM = 1.0e-4
TOKEN_PATTERN = re.compile(r"@@([A-Z0-9_]+)@@")


def sphere_volume_um3(radius_um: float) -> float:
    return 4.0 * math.pi * radius_um**3 / 3.0


def _fmt(value: float) -> str:
    return f"{value:.12g}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive(parameters: dict[str, Any]) -> dict[str, float | int]:
    geometry = parameters["geometry"]
    particles = parameters["particles"]
    loading = parameters["loading"]
    al = particles["al"]
    ds = particles["diamond_small"]
    dl = particles["diamond_large"]
    al_volume = int(al["count"]) * sphere_volume_um3(float(al["radius_um"]))
    diamond_volume = (
        int(ds["count"]) * sphere_volume_um3(float(ds["radius_um"]))
        + int(dl["count"]) * sphere_volume_um3(float(dl["radius_um"]))
    )
    solid_volume = al_volume + diamond_volume
    width = float(geometry["width_um"])
    thickness = float(geometry["thickness_um"])
    initial_height = float(geometry["initial_height_um"])
    final_height = float(geometry["final_height_um"])
    load_steps = round(
        (initial_height - final_height)
        * UM_TO_CM
        / (float(loading["top_velocity_cm_s"]) * float(loading["time_step_s"]))
    )
    return {
        "al_volume_um3": al_volume,
        "diamond_volume_um3": diamond_volume,
        "solid_volume_um3": solid_volume,
        "al_volume_fraction": al_volume / solid_volume,
        "diamond_volume_fraction": diamond_volume / solid_volume,
        "initial_geometric_density": solid_volume / (width * initial_height * thickness),
        "final_geometric_density": solid_volume / (width * final_height * thickness),
        "load_steps": load_steps,
        "total_count": int(al["count"]) + int(ds["count"]) + int(dl["count"]),
    }


def validate(parameters: dict[str, Any], derived: dict[str, float | int]) -> None:
    if parameters.get("schema_version") != 1:
        raise ValueError("unsupported true-3D pilot parameter schema")
    geometry = parameters["geometry"]
    particles = parameters["particles"]
    loading = parameters["loading"]
    acceptance = parameters["acceptance"]
    if geometry["front_back_boundary"] != "fixed_mesh_walls_nonperiodic":
        raise ValueError("front/back boundaries must be fixed, nonperiodic mesh walls")
    if float(geometry["thickness_um"]) <= 2.0 * float(particles["diamond_large"]["radius_um"]):
        raise ValueError("true-3D thickness must exceed the largest particle diameter")
    if int(derived["load_steps"]) != int(loading["load_steps"]):
        raise ValueError("load_steps does not match punch travel, velocity, and timestep")
    total_steps = (
        3
        + int(loading["initial_settle_steps"])
        + int(loading["load_steps"])
        + int(loading["final_settle_steps"])
    )
    if total_steps != int(loading["expected_total_steps"]):
        raise ValueError("expected_total_steps is inconsistent")
    if int(derived["total_count"]) != int(acceptance["particle_count_exact"]):
        raise ValueError("particle count does not match acceptance contract")
    targets = particles["target_volume_fraction"]
    if abs(float(derived["al_volume_fraction"]) - float(targets["al"])) > 0.002:
        raise ValueError("Al volume fraction misses the frozen target")
    if abs(float(derived["diamond_volume_fraction"]) - float(targets["diamond"])) > 0.002:
        raise ValueError("diamond volume fraction misses the frozen target")


def token_values(parameters: dict[str, Any], derived: dict[str, float | int]) -> dict[str, str]:
    g = parameters["geometry"]
    p = parameters["particles"]
    m = parameters["mechanics"]
    loading = parameters["loading"]
    al, ds, dl = p["al"], p["diamond_small"], p["diamond_large"]
    seeds = p["seeds"]
    width, height = float(g["width_um"]), float(g["initial_height_um"])
    thickness = float(g["thickness_um"])

    def cm(value_um: float) -> float:
        return value_um * UM_TO_CM

    def insertion_bounds(radius_um: float) -> tuple[float, float, float, float, float, float]:
        return (
            cm(radius_um),
            cm(width - radius_um),
            cm(radius_um),
            cm(height - radius_um),
            cm(-thickness / 2.0 + radius_um),
            cm(thickness / 2.0 - radius_um),
        )

    values: dict[str, str] = {
        "WIDTH_UM": _fmt(width),
        "THICKNESS_UM": _fmt(thickness),
        "INITIAL_HEIGHT_UM": _fmt(height),
        "FINAL_HEIGHT_UM": _fmt(float(g["final_height_um"])),
        "WIDTH_CM": _fmt(cm(width)),
        "THICKNESS_CM": _fmt(cm(thickness)),
        "INITIAL_HEIGHT_CM": _fmt(cm(height)),
        "FINAL_HEIGHT_CM": _fmt(cm(float(g["final_height_um"]))),
        "SIM_Z_MIN_CM": _fmt(cm(-thickness / 2.0)),
        "SIM_Z_MAX_CM": _fmt(cm(thickness / 2.0)),
        "TOP_VELOCITY_CM_S": _fmt(float(loading["top_velocity_cm_s"])),
        "TIME_STEP_S": _fmt(float(loading["time_step_s"])),
        "INITIAL_SETTLE_STEPS": str(int(loading["initial_settle_steps"])),
        "LOAD_STEPS": str(int(loading["load_steps"])),
        "FINAL_SETTLE_STEPS": str(int(loading["final_settle_steps"])),
        "GRAVITY_CM_S2": _fmt(float(m["gravity_cm_s2"])),
        "AL_DENSITY": _fmt(float(al["density_g_cm3"])),
        "DIAMOND_DENSITY": _fmt(float(ds["density_g_cm3"])),
        "AL_RADIUS_CM": _fmt(cm(float(al["radius_um"]))),
        "DS_RADIUS_CM": _fmt(cm(float(ds["radius_um"]))),
        "DL_RADIUS_CM": _fmt(cm(float(dl["radius_um"]))),
        "AL_COUNT": str(int(al["count"])),
        "DS_COUNT": str(int(ds["count"])),
        "DL_COUNT": str(int(dl["count"])),
        "TOTAL_COUNT": str(int(derived["total_count"])),
        "CUMULATIVE_DL_COUNT": str(int(dl["count"])),
        "CUMULATIVE_DS_COUNT": str(int(dl["count"]) + int(ds["count"])),
        "CUMULATIVE_AL_COUNT": str(int(derived["total_count"])),
        "SOLID_VOLUME_UM3": _fmt(float(derived["solid_volume_um3"])),
        "AL_VOLUME_FRACTION": _fmt(float(derived["al_volume_fraction"])),
        "DIAMOND_VOLUME_FRACTION": _fmt(float(derived["diamond_volume_fraction"])),
        "FINAL_GEOMETRIC_DENSITY": _fmt(float(derived["final_geometric_density"])),
    }
    for key, value in seeds.items():
        values[f"{key.upper()}_SEED"] = str(int(value))
    for key, value in m["young_modulus_gpa"].items():
        values[f"E_{key.upper()}_CGS"] = _fmt(float(value) * 1.0e10)
    for key, value in m["poisson_ratio"].items():
        values[f"NU_{key.upper()}"] = _fmt(float(value))
    for key, value in m["coefficient_restitution"].items():
        values[f"COR_{key.upper()}"] = _fmt(float(value))
    for key, value in m["coefficient_friction"].items():
        values[f"MU_{key.upper()}"] = _fmt(float(value))
    for prefix, particle in (("AL", al), ("DS", ds), ("DL", dl)):
        bounds = insertion_bounds(float(particle["radius_um"]))
        for suffix, value in zip(
            ("X_MIN_CM", "X_MAX_CM", "Y_MIN_CM", "Y_MAX_CM", "Z_MIN_CM", "Z_MAX_CM"),
            bounds,
        ):
            values[f"{prefix}_{suffix}"] = _fmt(value)
    return values


def render(template_path: Path, parameter_path: Path, output_path: Path, summary_path: Path) -> dict[str, Any]:
    parameters = json.loads(parameter_path.read_text(encoding="utf-8"))
    derived = derive(parameters)
    validate(parameters, derived)
    template = template_path.read_text(encoding="utf-8")
    values = token_values(parameters, derived)
    missing = sorted(set(TOKEN_PATTERN.findall(template)) - set(values))
    if missing:
        raise ValueError(f"unmapped template tokens: {missing}")
    rendered = TOKEN_PATTERN.sub(lambda match: values[match.group(1)], template)
    if TOKEN_PATTERN.search(rendered):
        raise ValueError("rendered deck still contains template tokens")
    if re.search(r"\bfix\s+zlock\b|\bset\s+group\s+all\s+z\s+0", rendered):
        raise ValueError("true-3D deck contains a forbidden z lock or z reset")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8", newline="\n")
    summary = {
        "pilot_id": parameters["pilot_id"],
        "decision": "rendered_true_3d_pilot",
        "source_classification": parameters["source_classification"],
        "derived": derived,
        "parameter_sha256": _sha256(parameter_path),
        "template_sha256": _sha256(template_path),
        "rendered_deck_sha256": _sha256(output_path),
        "solver": parameters["solver"],
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the frozen Stage 04 true-3D DEM pilot")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    result = render(args.template, args.parameters, args.output, args.summary)
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
