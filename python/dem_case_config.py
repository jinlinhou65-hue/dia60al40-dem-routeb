from __future__ import annotations

from dataclasses import dataclass


W_UM = 400.0
TARGET_AL_AREA_FRACTION = 0.40
TARGET_DIAMOND_AREA_FRACTION = 0.60
INSERT_RHO_TOTAL = 0.38
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
    "A": DiamondCase("A", "dual diamond 40/70 um actual, scaled to 12/21 um DEM", 40.0, 70.0, 12.0, 21.0, 8, 8),
    "B": DiamondCase("B", "dual diamond 60/100 um actual, scaled to 18/30 um DEM", 60.0, 100.0, 18.0, 30.0, 8, 8),
    "C": DiamondCase("C", "dual diamond 80/130 um actual, scaled to 24/39 um DEM", 80.0, 130.0, 24.0, 39.0, 8, 8),
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
