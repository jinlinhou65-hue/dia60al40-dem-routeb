from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path


W_UM = 400.0
TARGET_AL_AREA_FRACTION = 0.40
TARGET_DIAMOND_AREA_FRACTION = 0.60
AL_RADIUS_UM = 13.0
DT_SECONDS = 2.0e-10
TOP_VEL_CM_S = 1.0
INITIAL_SETTLE_STEPS = 1_250_000
STAGE_SETTLE_STEPS = 1_250_000
FINAL_SETTLE_STEPS = 2_500_000

RHO_STAGES = [
    ("stage0_preload", 0.5668),
    ("stage1_rho065", 0.6500),
    ("stage2_rho072", 0.7200),
    ("stage3_rho080", 0.8000),
    ("stage4_rho088", 0.8800),
    ("stage5_rho095", 0.9500),
]


@dataclass(frozen=True)
class DiamondCase:
    case_id: str
    description: str
    ds_actual_um: float
    dl_actual_um: float
    ds_dem_um: float
    dl_dem_um: float
    ds_count: int
    dl_count: int


DIAMOND_CASES = {
    # A is kept for optional comparison. The user-requested workflow default is C/D/E.
    "A": DiamondCase("A", "dual diamond 40/70 um actual, scaled to 12/21 um DEM", 40.0, 70.0, 12.0, 21.0, 8, 8),
    "B": DiamondCase("B", "dual diamond 60/100 um actual, scaled to 18/30 um DEM", 60.0, 100.0, 18.0, 30.0, 8, 8),
    "C": DiamondCase("C", "dual diamond 80/130 um actual, scaled to 24/39 um DEM", 80.0, 130.0, 24.0, 39.0, 8, 8),
    # Single-size counts keep the total diamond area close to case B. For every
    # case, Al count is then back-calculated from the fixed 13 um Al radius so
    # Al/Diamond area stays near 40/60 without changing powder particle size.
    "D": DiamondCase("D", "single diamond 100 um actual, scaled to 30 um DEM", 0.0, 100.0, 0.0, 30.0, 0, 11),
    "E": DiamondCase("E", "single diamond 60 um actual, scaled to 18 um DEM", 60.0, 0.0, 18.0, 0.0, 30, 0),
}

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


def circle_area_um2(radius_um: float) -> float:
    return math.pi * radius_um * radius_um


def octagon_area_um2(radius_um: float) -> float:
    # COMSOL handoff draws diamond as regular octagons with radius = circumradius.
    return 2.0 * math.sqrt(2.0) * radius_um * radius_um


def total_solid_area_um2(case: DiamondCase) -> float:
    return al_area_um2(case) + diamond_area_um2(case)


def al_count(case: DiamondCase) -> int:
    # Hold Al particle radius fixed, then choose the count that best gives 40%
    # Al area for the selected diamond-size recipe.
    target_al_area = diamond_area_um2(case) * TARGET_AL_AREA_FRACTION / TARGET_DIAMOND_AREA_FRACTION
    return max(1, int(round(target_al_area / circle_area_um2(AL_RADIUS_UM))))


def al_area_um2(case: DiamondCase) -> float:
    return al_count(case) * circle_area_um2(AL_RADIUS_UM)


def diamond_area_um2(case: DiamondCase) -> float:
    return case.ds_count * octagon_area_um2(case.ds_dem_um) + case.dl_count * octagon_area_um2(case.dl_dem_um)


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


def stage_plan(case: DiamondCase, e_al_stages: list[float]) -> list[dict[str, float | str]]:
    area_um2 = total_solid_area_um2(case)
    h0_um = initial_height_um(case)
    plan: list[dict[str, float | str]] = []
    previous_displacement = 0.0
    for i, ((stage_id, rho), e_gpa) in enumerate(zip(RHO_STAGES, e_al_stages)):
        height = area_um2 / (W_UM * rho)
        displacement = h0_um - height
        if displacement < previous_displacement - 1.0e-9:
            raise SystemExit(f"[FAIL] {case.case_id} {stage_id} displacement is non-monotonic")
        incremental_um = displacement - previous_displacement
        run_steps = max(1, int(round(incremental_um * 1.0e-4 / (TOP_VEL_CM_S * DT_SECONDS))))
        plan.append(
            {
                "idx": i,
                "stage_id": stage_id,
                "rho": rho,
                "requested_rho": rho,
                "height_um": height,
                "displacement_um": displacement,
                "incremental_um": incremental_um,
                "run_steps": run_steps,
                "e_gpa": e_gpa,
            }
        )
        previous_displacement = displacement
    return plan


def initial_height_um(case: DiamondCase) -> float:
    # The die height is chosen per particle-size recipe so every sweep starts
    # from the same stage0 loose density, then compacts along the same rho path.
    return total_solid_area_um2(case) / (W_UM * RHO_STAGES[0][1])


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


def replace_diamond_templates(text: str, case: DiamondCase) -> str:
    h_cm = initial_height_um(case) * 1.0e-4
    al_cm = AL_RADIUS_UM * 1.0e-4
    ds_cm = max(case.ds_dem_um, 1.0) * 1.0e-4
    dl_cm = max(case.dl_dem_um, 1.0) * 1.0e-4
    text = re.sub(
        r"fix\s+ptsAl\s+all\s+particletemplate/sphere\s+\d+\s+atom_type\s+1\s+density\s+constant\s+2\.70\s+radius\s+constant\s+[-+0-9.eE]+",
        f"fix             ptsAl all particletemplate/sphere 15485863 atom_type 1 density constant 2.70 radius constant {al_cm:.6g}",
        text,
        count=1,
    )
    text = re.sub(
        r"fix\s+ptsDS\s+all\s+particletemplate/sphere\s+\d+\s+atom_type\s+2\s+density\s+constant\s+3\.52\s+radius\s+constant\s+[-+0-9.eE]+",
        f"fix             ptsDS all particletemplate/sphere 15485867 atom_type 2 density constant 3.52 radius constant {ds_cm:.6g}",
        text,
        count=1,
    )
    text = re.sub(
        r"fix\s+ptsDL\s+all\s+particletemplate/sphere\s+\d+\s+atom_type\s+2\s+density\s+constant\s+3\.52\s+radius\s+constant\s+[-+0-9.eE]+",
        f"fix             ptsDL all particletemplate/sphere 49979693 atom_type 2 density constant 3.52 radius constant {dl_cm:.6g}",
        text,
        count=1,
    )
    text = re.sub(r"variable\s+Hcm\s+equal\s+[-+0-9.eE]+", f"variable        Hcm equal {h_cm:.9g}", text, count=1)
    text = re.sub(
        r"region\s+simreg\s+block\s+-0\.002\s+0\.042\s+-0\.004\s+[-+0-9.eE]+\s+-0\.0045\s+0\.0045\s+units\s+box",
        f"region          simreg block -0.002 0.042 -0.004 {h_cm + 0.002:.9g} -0.0045 0.0045 units box",
        text,
        count=1,
    )
    return text


def insertion_step(fix_id: str, seed: int, pdd: str, target_count: int) -> list[str]:
    return [
        (
            f"fix             {fix_id} all insert/pack seed {seed} distributiontemplate {pdd} "
            f"maxattempt 200000 insert_every once overlapcheck yes all_in no "
            f"particles_in_region {target_count} region particles_in_region ntry_mc 200000"
        ),
        "run             1",
        "set             group all z 0.0",
        "velocity        all set NULL NULL 0.0",
        f"unfix           {fix_id}",
    ]


def insertion_block(case: DiamondCase) -> str:
    y_max = max(0.0013, initial_height_um(case) * 1.0e-4 - 0.0013)
    lines = [
        "# Sequential insertion targets are cumulative. The diamond counts are",
        f"# generated from diamond_size_case={case.case_id}: DS={case.ds_count}, DL={case.dl_count}, Al={al_count(case)}.",
        (
            "region          particles_in_region block 0.0013 0.0387 0.0013 "
            f"{y_max:.9g} -0.000001 0.000001 units box"
        ),
    ]
    cumulative = 0
    if case.dl_count == 0 and case.ds_count > 0:
        # Single-small-diamond mixtures are crowded by particle count. Insert Al
        # first so the 34-matrix-particle requirement is protected, then fill the
        # remaining void space with the smaller diamond particles.
        cumulative += al_count(case)
        lines.extend(insertion_step("insAl", SEED_KEYS["insAl"], "pddAl", cumulative))
        cumulative += case.ds_count
        lines.extend(insertion_step("insDS", SEED_KEYS["insDS"], "pddDS", cumulative))
        return "\n".join(lines)
    if case.dl_count > 0:
        cumulative += case.dl_count
        lines.extend(insertion_step("insDL", SEED_KEYS["insDL"], "pddDL", cumulative))
    if case.ds_count > 0:
        cumulative += case.ds_count
        lines.extend(insertion_step("insDS", SEED_KEYS["insDS"], "pddDS", cumulative))
    cumulative += al_count(case)
    lines.extend(insertion_step("insAl", SEED_KEYS["insAl"], "pddAl", cumulative))
    return "\n".join(lines)


def replace_insertion_block(text: str, case: DiamondCase) -> str:
    start = text.find("# Sequential insertion targets are cumulative")
    end = text.find("thermo_style", start)
    if start < 0 or end < 0:
        raise SystemExit("[FAIL] could not locate insertion block")
    return text[:start] + insertion_block(case) + "\n\n" + text[end:]


def model_parameter_block(
    args: argparse.Namespace,
    case: DiamondCase,
    e_al_stages: list[float],
    plan: list[dict[str, float | str]],
) -> str:
    safe_description = case.description.replace(",", ";")
    lines = ['print           "parameter,value,unit" file DEM/model_parameters.csv screen no']
    lines.extend(
        [
            f'print           "diamond_size_case,{case.case_id},1" append DEM/model_parameters.csv screen no',
            f'print           "diamond_size_description,{safe_description},text" append DEM/model_parameters.csv screen no',
            f'print           "Al_count,{al_count(case)},1" append DEM/model_parameters.csv screen no',
            f'print           "diamond_count_DS,{case.ds_count},1" append DEM/model_parameters.csv screen no',
            f'print           "diamond_count_DL,{case.dl_count},1" append DEM/model_parameters.csv screen no',
            f'print           "Al_dem_radius_um,{AL_RADIUS_UM:.9g},um" append DEM/model_parameters.csv screen no',
            f'print           "diamond_actual_radius_DS_um,{case.ds_actual_um:.6g},um" append DEM/model_parameters.csv screen no',
            f'print           "diamond_actual_radius_DL_um,{case.dl_actual_um:.6g},um" append DEM/model_parameters.csv screen no',
            f'print           "diamond_dem_radius_DS_um,{case.ds_dem_um:.6g},um" append DEM/model_parameters.csv screen no',
            f'print           "diamond_dem_radius_DL_um,{case.dl_dem_um:.6g},um" append DEM/model_parameters.csv screen no',
            f'print           "target_Al_area_fraction,{TARGET_AL_AREA_FRACTION:.9g},1" append DEM/model_parameters.csv screen no',
            f'print           "target_diamond_area_fraction,{TARGET_DIAMOND_AREA_FRACTION:.9g},1" append DEM/model_parameters.csv screen no',
            f'print           "initial_die_height_um,{initial_height_um(case):.9g},um" append DEM/model_parameters.csv screen no',
            f'print           "Al_area_um2,{al_area_um2(case):.9g},um2" append DEM/model_parameters.csv screen no',
            f'print           "diamond_area_um2,{diamond_area_um2(case):.9g},um2" append DEM/model_parameters.csv screen no',
            f'print           "Al_area_fraction,{al_area_um2(case) / total_solid_area_um2(case):.9g},1" append DEM/model_parameters.csv screen no',
            f'print           "diamond_area_fraction,{diamond_area_um2(case) / total_solid_area_um2(case):.9g},1" append DEM/model_parameters.csv screen no',
            f'print           "solid_area_total_um2,{total_solid_area_um2(case):.9g},um2" append DEM/model_parameters.csv screen no',
        ]
    )
    for stage, e_gpa in zip(plan, e_al_stages):
        stage_id = str(stage["stage_id"])
        lines.append(f'print           "E_Al_{stage_id},{e_gpa:.6g},GPa" append DEM/model_parameters.csv screen no')
        lines.append(
            f'print           "rho_requested_{stage_id},{float(stage["requested_rho"]):.6g},1" append DEM/model_parameters.csv screen no'
        )
        lines.append(f'print           "rho_total_{stage_id},{float(stage["rho"]):.6g},1" append DEM/model_parameters.csv screen no')
        lines.append(
            f'print           "height_um_{stage_id},{float(stage["height_um"]):.9g},um" append DEM/model_parameters.csv screen no'
        )
        lines.append(
            f'print           "top_displacement_um_{stage_id},{float(stage["displacement_um"]):.9g},um" append DEM/model_parameters.csv screen no'
        )
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


def replace_model_parameters(
    text: str,
    args: argparse.Namespace,
    case: DiamondCase,
    e_al_stages: list[float],
    plan: list[dict[str, float | str]],
) -> str:
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
    return text[:i0] + model_parameter_block(args, case, e_al_stages, plan) + text[i1:]


def stage_block(
    stage: dict[str, float | str],
    case: DiamondCase,
    e_diamond_gpa: float,
    e_tool_gpa: float,
    e_wall_gpa: float,
) -> str:
    idx = int(stage["idx"])
    stage_id = str(stage["stage_id"])
    dump_id = f"st{idx}"
    lines: list[str] = []
    if idx == 0:
        lines.append(f"# Stage 0: preload reference for diamond_size_case={case.case_id}.")
    else:
        lines.append(
            f"# Stage {idx}: rho_total ~{float(stage['rho']):.2f}. "
            f"Additional travel to {float(stage['displacement_um']):.6f} um."
        )
        lines.append("unfix           mprop")
        lines.append(
            "fix             mprop all property/global youngsModulus peratomtype "
            f"{gpa_to_cgs(float(stage['e_gpa']))} {gpa_to_cgs(e_diamond_gpa)} "
            f"{gpa_to_cgs(e_tool_gpa)} {gpa_to_cgs(e_wall_gpa)}"
        )
    settle_steps = FINAL_SETTLE_STEPS if idx == len(RHO_STAGES) - 1 else STAGE_SETTLE_STEPS
    lines.extend(
        [
            "fix             topMove all move/mesh mesh top linear 0.0 -${topVel} 0.0",
            f"run             {int(stage['run_steps'])}",
            "unfix           topMove",
            f"run             {settle_steps}",
            (
                f'print           "{stage_id},{float(stage["rho"]):.4f},{float(stage["height_um"]):.6f},'
                f'{float(stage["displacement_um"]):.6f},{float(stage["e_gpa"]):.6g},'
                '${topForceYDyn},${topForceAbsDyn},${topPressureMPa},'
                '${bottomForceYDyn},${bottomPressureMPa},${leftForceXDyn},${rightForceXDyn}" '
                "append DEM/pressure_density_curve_raw.csv screen no"
            ),
            f"dump            {dump_id} all custom 1 DEM/{stage_id}_*.dump id type x y z vx vy vz radius",
            "run             0",
            f"undump          {dump_id}",
            f"write_restart   DEM/{stage_id}.restart",
        ]
    )
    return "\n".join(lines)


def replace_stage_schedule(
    text: str,
    args: argparse.Namespace,
    case: DiamondCase,
    plan: list[dict[str, float | str]],
) -> str:
    start = text.find("# Initial settling before any punch motion.")
    end = text.find("undump          dmp", start)
    if start < 0 or end < 0:
        raise SystemExit("[FAIL] could not locate staged loading block")
    blocks = [
        "# Initial settling before any punch motion.",
        f"run             {INITIAL_SETTLE_STEPS}",
        "",
    ]
    for stage in plan:
        blocks.append(stage_block(stage, case, args.e_diamond_gpa, args.e_tool_gpa, args.e_wall_gpa))
        blocks.append("")
    return text[:start] + "\n".join(blocks) + text[end:]


def replace_seeds(text: str, seed_index: int) -> str:
    seed_map = SEED_TABLE[seed_index % len(SEED_TABLE)]
    for key, base_seed in SEED_KEYS.items():
        new_seed = seed_map[key]
        text, count = re.subn(rf"(\b{key}\b[^\n]*?)\b{base_seed}\b", rf"\g<1>{new_seed}", text, count=1)
        if count != 1 and key.startswith("ins"):
            # Single-size cases skip one of the diamond insertion fixes.
            continue
        if count != 1:
            raise SystemExit(f"[FAIL] could not replace seed for {key}")
    return text


def render(args: argparse.Namespace) -> None:
    source = Path(args.input)
    output = Path(args.output)
    case = DIAMOND_CASES[args.diamond_size_case.upper()]
    e_al_stages = stage_moduli(args.e_al_e0_gpa, args.e_al_emax_gpa)
    plan = stage_plan(case, e_al_stages)

    text = source.read_text(encoding="utf-8")
    text = replace_diamond_templates(text, case)
    text = replace_insertion_block(text, case)
    text = replace_moduli(text, e_al_stages, args.e_diamond_gpa, args.e_tool_gpa, args.e_wall_gpa)
    text = replace_friction(text, args)
    text = replace_model_parameters(text, args, case, e_al_stages, plan)
    text = replace_stage_schedule(text, args, case, plan)
    text = replace_seeds(text, args.seed_index)

    output.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] rendered {output}")
    print(f"[PARAM] diamond_size_case={case.case_id} {case.description}")
    print(f"[PARAM] initial_die_height_um={initial_height_um(case):.6g}")
    print(f"[PARAM] counts Al={al_count(case)} DS={case.ds_count} DL={case.dl_count} Al_radius_um={AL_RADIUS_UM:.6g}")
    print(
        "[PARAM] area_fraction Al="
        f"{al_area_um2(case) / total_solid_area_um2(case):.6g} Diamond="
        f"{diamond_area_um2(case) / total_solid_area_um2(case):.6g}"
    )
    print("[PARAM] E_Al_stages_GPa=" + ",".join(f"{v:.6g}" for v in e_al_stages))
    print(f"[PARAM] seed_index={args.seed_index} seed_table_slot={args.seed_index % len(SEED_TABLE)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="liggghts/in.dia60al40_dem_staged.liggghts")
    parser.add_argument("--output", default="liggghts/in.dia60al40_dem_staged.rendered.liggghts")
    parser.add_argument("--diamond-size-case", choices=sorted(DIAMOND_CASES), default="B")
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
