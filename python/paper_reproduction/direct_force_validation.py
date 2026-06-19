from __future__ import annotations

import math


DIRECT_FORCE_REVIEW_NOTE = (
    "Complete LIGGGHTS direct pair-force data are present, but this reduced "
    "demo has not been calibrated to Zhang's monotonic force-chain trends."
)


def uses_complete_direct_contact_forces(rows: list[dict[str, object]]) -> bool:
    if not rows:
        return False
    for row in rows:
        if row.get("contact_source") != "direct":
            return False
        try:
            fraction = float(row.get("direct_contact_force_fraction", "nan"))
        except (TypeError, ValueError):
            return False
        if not math.isfinite(fraction) or abs(fraction - 1.0) > 1e-12:
            return False
    return True


def mark_direct_force_review(
    check: dict[str, object],
    *,
    direct_force_mode: bool,
) -> dict[str, object]:
    if direct_force_mode and check["status"] == "mismatch":
        check["status"] = "review"
        check["expected"] = f"{check['expected']}; direct-force calibration pending"
        check["note"] = DIRECT_FORCE_REVIEW_NOTE
    return check


def csv_int(value: object) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0
