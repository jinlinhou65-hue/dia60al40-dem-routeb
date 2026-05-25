from __future__ import annotations

import argparse
import re
from pathlib import Path


RHO_STAGES = [
    ("stage0_preload", 0.5668),
    ("stage1_rho065", 0.6500),
    ("stage2_rho072", 0.7200),
    ("stage3_rho080", 0.8000),
    ("stage4_rho088", 0.8800),
    ("stage5_rho095", 0.9500),
]

SEED_KEYS = {
    "ptsAl": 15485863,
    "ptsDS": 15485867,
    "ptsDL": 49979693,
    "pddAl": 32452843,
    "pddDS": 32452867,
    "pddDL": 67867967,
    "insDL": 49979687,
    "insDS": 67867979,
    "insAl": 86028121,
}

# Fixed prime table keeps every workflow run reproducible while still sampling
# different random mixed-powder packings. LIGGGHTS insertion has historically
# been picky about seeds, so use known-prime values instead of arithmetic offsets.
SEED_TABLE = [
    {
        "ptsAl": 15485863,
        "ptsDS": 15485867,
        "ptsDL": 49979693,
        "pddAl": 32452843,
        "pddDS": 32452867,
        "pddDL": 67867967,
        "insDL": 49979687,
        "insDS": 67867979,
        "insAl": 86028121,
    },
    {
        "ptsAl": 32452867,
        "ptsDS": 49979693,
        "ptsDL": 67867979,
        "pddAl": 86028121,
        "pddDS": 15485863,
        "pddDL": 15485867,
        "insDL": 32452843,
        "insDS": 67867967,
        "insAl": 49979687,
    },
    {
        "ptsAl": 67867967,
        "ptsDS": 32452843,
        "ptsDL": 86028121,
        "pddAl": 49979687,
        "pddDS": 49979693,
        "pddDL": 15485863,
        "insDL": 15485867,
        "insDS": 32452867,
        "insAl": 67867979,
    },
    {
        "ptsAl": 86028121,
        "ptsDS": 67867967,
        "ptsDL": 32452843,
        "pddAl": 15485867,
        "pddDS": 49979687,
        "pddDL": 32452867,
        "insDL": 67867979,
        "insDS": 15485863,
        "insAl": 49979693,
    },
    {
        "ptsAl": 49979687,
        "ptsDS": 86028121,
        "ptsDL": 15485867,
        "pddAl": 67867979,
        "pddDS": 32452843,
        "pddDL": 49979693,
        "insDL": 15485863,
        "insDS": 49979687,
        "insAl": 32452867,
    },
]


def smoothstep(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return 3.0 * x * x - 2.0 * x * x * x


def stage_moduli(e0_gpa: float, emax_gpa: float) -> list[float]:
    rho0 = RHO_STAGES[0][1]
    rho95 = RHO_STAGES[-1][1]
    span = rho95 - rho0
    values: list[float] = []
    for _, rho in RHO_STAGES:
        x = (rho - rho0) / span if span > 0.0 else 1.0
        values.append(e0_gpa + (emax_gpa - e0_gpa) * smoothstep(x))
    return values


def gpa_to_cgs(value_gpa: float) -> str:
    # LIGGGHTS cgs unit: 1 GPa = 1e10 dyne/cm^2.
    return f"{value_gpa * 1.0e10:.9g}"


def replace_moduli(
    text: str,
    e_al_stages: list[float],
    e_diamond_gpa: float,
    e_tool_gpa: float,
    e_wall_gpa: float,
) -> str:
    lines = text.splitlines()
    stage_index = 0
    out: list[str] = []
    for line in lines:
        if line.startswith("fix             mprop all property/global youngsModulus peratomtype"):
            if stage_index >= len(e_al_stages):
                raise SystemExit("[FAIL] more mprop stage lines than expected")
            out.append(
                "fix             mprop all property/global youngsModulus peratomtype "
                f"{gpa_to_cgs(e_al_stages[stage_index])} "
                f"{gpa_to_cgs(e_diamond_gpa)} "
                f"{gpa_to_cgs(e_tool_gpa)} "
                f"{gpa_to_cgs(e_wall_gpa)}"
            )
            stage_index += 1
        else:
            out.append(line)
    if stage_index != len(e_al_stages):
        raise SystemExit(f"[FAIL] expected {len(e_al_stages)} mprop stage lines, replaced {stage_index}")
    return "\n".join(out) + "\n"


def friction_block(args: argparse.Namespace) -> str:
    aa = args.mu_al_al * args.mu_scale
    ad = args.mu_al_diamond * args.mu_scale
    at = args.mu_al_tool * args.mu_scale
    aw = args.mu_al_wall * args.mu_scale
    dd = args.mu_diamond_diamond * args.mu_scale
    dt = args.mu_diamond_tool * args.mu_scale
    dw = args.mu_diamond_wall * args.mu_scale
    tt = args.mu_tool_tool * args.mu_scale
    tw = args.mu_tool_wall * args.mu_scale
    ww = args.mu_wall_wall * args.mu_scale
    return (
        "fix             cof all property/global coefficientFriction peratomtypepair 4 &\n"
        f"                {aa:.6g} {ad:.6g} {at:.6g} {aw:.6g} &\n"
        f"                {ad:.6g} {dd:.6g} {dt:.6g} {dw:.6g} &\n"
        f"                {at:.6g} {dt:.6g} {tt:.6g} {tw:.6g} &\n"
        f"                {aw:.6g} {dw:.6g} {tw:.6g} {ww:.6g}"
    )


def replace_friction(text: str, args: argparse.Namespace) -> str:
    pattern = re.compile(
        r"fix\s+cof\s+all\s+property/global\s+coefficientFriction\s+peratomtypepair\s+4\s+&\n"
        r"\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+&\n"
        r"\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+&\n"
        r"\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+&\n"
        r"\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+"
    )
    text, count = pattern.subn(friction_block(args), text, count=1)
    if count != 1:
        raise SystemExit("[FAIL] could not replace coefficientFriction block")
    return text


def replace_stage_prints(text: str, e_al_stages: list[float]) -> str:
    # Keep the output schema stable, but replace the literal al_modulus_gpa
    # value embedded in each stage row.
    for (stage_id, _), e_gpa in zip(RHO_STAGES, e_al_stages):
        pattern = re.compile(rf'print\s+"({stage_id},[^"]*?,)([-+0-9.eE]+)(,[$]{{topForceYDyn}})')
        text, count = pattern.subn(lambda m: f'print           "{m.group(1)}{e_gpa:.6g}{m.group(3)}', text, count=1)
        if count != 1:
            raise SystemExit(f"[FAIL] could not replace al_modulus_gpa print for {stage_id}")
    return text


def model_parameter_block(args: argparse.Namespace, e_al_stages: list[float]) -> str:
    lines = ['print           "parameter,value,unit" file DEM/model_parameters.csv screen no']
    for (stage_id, rho), e_gpa in zip(RHO_STAGES, e_al_stages):
        lines.append(f'print           "E_Al_{stage_id},{e_gpa:.6g},GPa" append DEM/model_parameters.csv screen no')
        lines.append(f'print           "rho_total_{stage_id},{rho:.6g},1" append DEM/model_parameters.csv screen no')
    lines.extend(
        [
            f'print           "DEM_seed_index,{args.seed_index},1" append DEM/model_parameters.csv screen no',
            f'print           "DEM_seed_table_slot,{args.seed_index % len(SEED_TABLE)},1" append DEM/model_parameters.csv screen no',
            f'print           "E_Al_smoothstep_E0,{args.e_al_e0_gpa:.6g},GPa" append DEM/model_parameters.csv screen no',
            f'print           "E_Al_smoothstep_Emax,{args.e_al_emax_gpa:.6g},GPa" append DEM/model_parameters.csv screen no',
            f'print           "E_Diamond,{args.e_diamond_gpa:.6g},GPa" append DEM/model_parameters.csv screen no',
            f'print           "E_Tool,{args.e_tool_gpa:.6g},GPa" append DEM/model_parameters.csv screen no',
            f'print           "E_Wall,{args.e_wall_gpa:.6g},GPa" append DEM/model_parameters.csv screen no',
            f'print           "mu_scale,{args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Al_Al,{args.mu_al_al * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Al_Diamond,{args.mu_al_diamond * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Al_Tool,{args.mu_al_tool * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Al_Wall,{args.mu_al_wall * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Diamond_Diamond,{args.mu_diamond_diamond * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Diamond_Tool,{args.mu_diamond_tool * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Diamond_Wall,{args.mu_diamond_wall * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Tool_Tool,{args.mu_tool_tool * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Tool_Wall,{args.mu_tool_wall * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            f'print           "mu_Wall_Wall,{args.mu_wall_wall * args.mu_scale:.6g},1" append DEM/model_parameters.csv screen no',
            'print           "smoothstep_E_Al,E0_plus_Emax_minus_E0_times_3x2_minus_2x3,description" append DEM/model_parameters.csv screen no',
        ]
    )
    return "\n".join(lines)


def replace_model_parameters(text: str, args: argparse.Namespace, e_al_stages: list[float]) -> str:
    start = 'print           "parameter,value,unit" file DEM/model_parameters.csv screen no'
    i0 = text.find(start)
    if i0 < 0:
        raise SystemExit("[FAIL] could not locate model_parameters print block")
    match = re.search(
        r'print\s+"smoothstep_E_Al,[^"]*,description"\s+append\s+DEM/model_parameters\.csv\s+screen\s+no',
        text[i0:],
    )
    if not match:
        raise SystemExit("[FAIL] could not locate model_parameters smoothstep terminator")
    i1 = i0 + match.end()
    return text[:i0] + model_parameter_block(args, e_al_stages) + text[i1:]


def replace_seeds(text: str, seed_index: int) -> str:
    seed_map = SEED_TABLE[seed_index % len(SEED_TABLE)]
    for key, base_seed in SEED_KEYS.items():
        new_seed = seed_map[key]
        text, count = re.subn(rf"(\b{key}\b[^\n]*?)\b{base_seed}\b", rf"\g<1>{new_seed}", text, count=1)
        if count != 1:
            raise SystemExit(f"[FAIL] could not replace seed for {key}")
    return text


def render(args: argparse.Namespace) -> None:
    source = Path(args.input)
    output = Path(args.output)
    e_al_stages = stage_moduli(args.e_al_e0_gpa, args.e_al_emax_gpa)

    text = source.read_text(encoding="utf-8")
    text = replace_moduli(text, e_al_stages, args.e_diamond_gpa, args.e_tool_gpa, args.e_wall_gpa)
    text = replace_friction(text, args)
    text = replace_stage_prints(text, e_al_stages)
    text = replace_model_parameters(text, args, e_al_stages)
    text = replace_seeds(text, args.seed_index)

    output.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] rendered {output}")
    print("[PARAM] E_Al_stages_GPa=" + ",".join(f"{v:.6g}" for v in e_al_stages))
    print(f"[PARAM] seed_index={args.seed_index} seed_table_slot={args.seed_index % len(SEED_TABLE)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="liggghts/in.dia60al40_dem_staged.liggghts")
    parser.add_argument("--output", default="liggghts/in.dia60al40_dem_staged.rendered.liggghts")
    parser.add_argument("--e-al-e0-gpa", type=float, default=5.0)
    parser.add_argument("--e-al-emax-gpa", type=float, default=12.0)
    parser.add_argument("--e-diamond-gpa", type=float, default=300.0)
    parser.add_argument("--e-tool-gpa", type=float, default=600.0)
    parser.add_argument("--e-wall-gpa", type=float, default=200.0)
    parser.add_argument("--mu-al-al", type=float, default=0.30)
    parser.add_argument("--mu-al-diamond", type=float, default=0.30)
    parser.add_argument("--mu-al-tool", type=float, default=0.08)
    parser.add_argument("--mu-al-wall", type=float, default=0.08)
    parser.add_argument("--mu-diamond-diamond", type=float, default=0.10)
    parser.add_argument("--mu-diamond-tool", type=float, default=0.08)
    parser.add_argument("--mu-diamond-wall", type=float, default=0.08)
    parser.add_argument("--mu-tool-tool", type=float, default=0.08)
    parser.add_argument("--mu-tool-wall", type=float, default=0.08)
    parser.add_argument("--mu-wall-wall", type=float, default=0.08)
    parser.add_argument("--mu-scale", type=float, default=1.0)
    parser.add_argument("--seed-index", type=int, default=0)
    render(parser.parse_args())


if __name__ == "__main__":
    main()
