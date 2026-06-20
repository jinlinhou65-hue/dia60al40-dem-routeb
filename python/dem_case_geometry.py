from __future__ import annotations

import math

try:
    from .dem_case_config import (
        INSERT_RHO_TOTAL,
        RHO_STAGES,
        TARGET_AL_AREA_FRACTION,
        TARGET_DIAMOND_AREA_FRACTION,
        W_UM,
        DiamondCase,
    )
except ImportError:
    from dem_case_config import (
        INSERT_RHO_TOTAL,
        RHO_STAGES,
        TARGET_AL_AREA_FRACTION,
        TARGET_DIAMOND_AREA_FRACTION,
        W_UM,
        DiamondCase,
    )


def circle_area_um2(radius_um: float) -> float:
    return math.pi * radius_um * radius_um


def octagon_area_um2(radius_um: float) -> float:
    return 2.0 * math.sqrt(2.0) * radius_um * radius_um


def total_solid_area_um2(case: DiamondCase) -> float:
    return al_area_um2(case) + diamond_area_um2(case)


def al_count(case: DiamondCase) -> int:
    target_al_area = diamond_area_um2(case) * TARGET_AL_AREA_FRACTION / TARGET_DIAMOND_AREA_FRACTION
    return max(1, int(round(target_al_area / circle_area_um2(case.al_dem_um))))


def al_area_um2(case: DiamondCase) -> float:
    return al_count(case) * circle_area_um2(case.al_dem_um)


def diamond_area_um2(case: DiamondCase) -> float:
    return case.ds_count * octagon_area_um2(case.ds_dem_um) + case.dl_count * octagon_area_um2(case.dl_dem_um)


def smoothstep(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return 3.0 * x * x - 2.0 * x * x * x


def stage_moduli(e0_gpa: float, emax_gpa: float) -> list[float]:
    rho0 = RHO_STAGES[0][1]
    rho95 = RHO_STAGES[-1][1]
    span = rho95 - rho0
    return [
        e0_gpa + (emax_gpa - e0_gpa) * smoothstep((rho - rho0) / span if span > 0.0 else 1.0)
        for _, rho in RHO_STAGES
    ]


def stage_plan(
    case: DiamondCase,
    e_al_stages: list[float],
    *,
    top_vel_cm_s: float,
    dt_seconds: float,
) -> list[dict[str, float | str]]:
    area_um2 = total_solid_area_um2(case)
    h0_um = initial_die_height_um(case)
    plan: list[dict[str, float | str]] = []
    previous_displacement = 0.0
    for i, ((stage_id, rho), e_gpa) in enumerate(zip(RHO_STAGES, e_al_stages)):
        height = area_um2 / (W_UM * rho)
        displacement = h0_um - height
        if displacement < previous_displacement - 1.0e-9:
            raise SystemExit(f"[FAIL] {case.case_id} {stage_id} displacement is non-monotonic")
        incremental_um = displacement - previous_displacement
        run_steps = max(1, int(round(incremental_um * 1.0e-4 / (top_vel_cm_s * dt_seconds))))
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


def stage0_height_um(case: DiamondCase) -> float:
    return total_solid_area_um2(case) / (W_UM * RHO_STAGES[0][1])


def initial_die_height_um(case: DiamondCase) -> float:
    insertion_height = total_solid_area_um2(case) / (W_UM * INSERT_RHO_TOTAL)
    return max(stage0_height_um(case), insertion_height)
