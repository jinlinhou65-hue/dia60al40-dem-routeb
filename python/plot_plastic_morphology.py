from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from matplotlib.transforms import Affine2D

from dem_stage_metadata import STAGE_BY_ID, UM_PER_CM, particle_shape, read_liggghts_dump


W_UM = 400.0


def import_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Ellipse, RegularPolygon, Rectangle

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.linewidth": 1.0,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    return plt, Ellipse, RegularPolygon, Rectangle


def latest_stage_dump(root: Path, stage_id: str) -> Path:
    matches = sorted(root.glob(f"{stage_id}_*.dump"))
    if not matches:
        raise SystemExit(f"[FAIL] no dump found for {stage_id}")
    return matches[-1]


def material(row: dict[str, str]) -> str:
    return "Al" if int(float(row["type"])) == 1 else "Diamond"


def particle_state(row: dict[str, str]) -> tuple[float, float, float]:
    return (
        float(row["x"]) * UM_PER_CM,
        float(row["y"]) * UM_PER_CM,
        float(row["radius"]) * UM_PER_CM,
    )


def add_contact(metric: dict[str, float], overlap_um: float, nx: float, ny: float) -> None:
    if overlap_um <= 0.0:
        return
    metric["contact_count"] += 1.0
    metric["overlap_sum_um"] += overlap_um
    metric["max_overlap_um"] = max(metric["max_overlap_um"], overlap_um)
    # Contact compression acts along the normal direction. Use a weighted
    # second moment so multiple contacts naturally choose a dominant flattening
    # direction without needing a brittle if/else for every contact topology.
    metric["mxx"] += overlap_um * nx * nx
    metric["mxy"] += overlap_um * nx * ny
    metric["myy"] += overlap_um * ny * ny


def contact_metrics(rows: list[dict[str, str]], height_um: float) -> dict[str, dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {}
    for i, row in enumerate(rows):
        pid = str(row.get("id", i + 1))
        metrics[pid] = {
            "contact_count": 0.0,
            "overlap_sum_um": 0.0,
            "max_overlap_um": 0.0,
            "mxx": 0.0,
            "mxy": 0.0,
            "myy": 0.0,
        }

    for i, a in enumerate(rows):
        ax, ay, ar = particle_state(a)
        aid = str(a.get("id", i + 1))
        for j, b in enumerate(rows[i + 1 :], start=i + 1):
            bx, by, br = particle_state(b)
            bid = str(b.get("id", j + 1))
            dx = bx - ax
            dy = by - ay
            dist = math.hypot(dx, dy)
            if dist <= 1e-12:
                nx, ny = 1.0, 0.0
            else:
                nx, ny = dx / dist, dy / dist
            overlap = ar + br - dist
            if overlap > 0.0:
                add_contact(metrics[aid], overlap, nx, ny)
                add_contact(metrics[bid], overlap, -nx, -ny)

    for i, row in enumerate(rows):
        pid = str(row.get("id", i + 1))
        x, y, r = particle_state(row)
        add_contact(metrics[pid], r - x, -1.0, 0.0)
        add_contact(metrics[pid], x + r - W_UM, 1.0, 0.0)
        add_contact(metrics[pid], r - y, 0.0, -1.0)
        add_contact(metrics[pid], y + r - height_um, 0.0, 1.0)

    return metrics


def principal_direction(metric: dict[str, float]) -> float:
    mxx = metric["mxx"]
    mxy = metric["mxy"]
    myy = metric["myy"]
    if abs(mxx) + abs(mxy) + abs(myy) <= 1e-12:
        return 0.0
    return 0.5 * math.atan2(2.0 * mxy, mxx - myy)


def deformation(row: dict[str, str], metric: dict[str, float]) -> tuple[float, float, float, float]:
    _, _, r = particle_state(row)
    mat = material(row)
    severity = metric["overlap_sum_um"] / max(r, 1e-9)
    if mat == "Al":
        gain = 0.36
        cap = 0.62
    else:
        # Diamond is still allowed to show contact-compression deformation, but
        # its much higher stiffness keeps the visible flattening modest.
        gain = 0.045
        cap = 0.14
    flatten = min(cap, gain * severity)
    minor = max(0.35 * r, r * (1.0 - flatten))
    major = min(1.9 * r, r * r / minor)
    angle = principal_direction(metric)
    return major, minor, angle, flatten


def plot_stage(root: Path, stage_id: str, outdir: Path, metric_rows: list[dict[str, str]]) -> None:
    plt, Ellipse, RegularPolygon, Rectangle = import_matplotlib()
    dump = latest_stage_dump(root, stage_id)
    rows = read_liggghts_dump(dump)
    _, target_rho, height_um, _, _ = STAGE_BY_ID[stage_id]
    metrics = contact_metrics(rows, height_um)

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=180)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-25, 425)
    ax.set_ylim(-25, 230)
    ax.add_patch(Rectangle((0, 0), W_UM, height_um, fill=False, linewidth=1.2, edgecolor="#444444"))

    for i, row in enumerate(rows):
        pid = str(row.get("id", i + 1))
        x, y, r = particle_state(row)
        met = metrics[pid]
        major, minor, angle, flatten = deformation(row, met)
        shape = particle_shape(row)
        mat = material(row)
        if mat == "Al":
            patch = Ellipse(
                (x, y),
                width=2.0 * major,
                height=2.0 * minor,
                angle=math.degrees(angle),
                facecolor="#d7e9ff",
                edgecolor="#235789",
                linewidth=0.7,
                alpha=0.96,
            )
        else:
            patch = RegularPolygon(
                (0.0, 0.0),
                numVertices=8,
                radius=1.0,
                orientation=math.radians(22.5),
                facecolor="#333333",
                edgecolor="#111111",
                linewidth=0.7,
                alpha=0.96,
            )
            transform = (
                Affine2D()
                .scale(major, minor)
                .rotate(angle)
                .translate(x, y)
                + ax.transData
            )
            patch.set_transform(transform)
        ax.add_patch(patch)
        metric_rows.append(
            {
                "stage_id": stage_id,
                "particle_id": pid,
                "type": shape,
                "material": mat,
                "x_um": f"{x:.9g}",
                "y_um": f"{y:.9g}",
                "r_nominal_um": f"{r:.9g}",
                "major_axis_um": f"{major:.9g}",
                "minor_axis_um": f"{minor:.9g}",
                "orientation_rad": f"{angle:.9g}",
                "flattening": f"{flatten:.9g}",
                "contact_count": f"{met['contact_count']:.0f}",
                "overlap_sum_um": f"{met['overlap_sum_um']:.9g}",
                "max_overlap_um": f"{met['max_overlap_um']:.9g}",
            }
        )

    ax.set_xlabel("x (um)")
    ax.set_ylabel("y (um)")
    ax.set_title(f"Pseudo-plastic morphology: {stage_id}, target rho={target_rho:.3f}")
    ax.tick_params(direction="in", top=True, right=True)
    fig.tight_layout()
    fig.savefig(outdir / f"plastic_morphology_{stage_id}.png")
    plt.close(fig)


def write_metrics(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "stage_id",
        "particle_id",
        "type",
        "material",
        "x_um",
        "y_um",
        "r_nominal_um",
        "major_axis_um",
        "minor_axis_um",
        "orientation_rad",
        "flattening",
        "contact_count",
        "overlap_sum_um",
        "max_overlap_um",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="liggghts/DEM")
    parser.add_argument("--outdir", default="liggghts/DEM/plots")
    parser.add_argument("--metrics", default="liggghts/DEM/plastic_morphology_metrics.csv")
    args = parser.parse_args()

    root = Path(args.root)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    metric_rows: list[dict[str, str]] = []
    for stage_id in STAGE_BY_ID:
        plot_stage(root, stage_id, outdir, metric_rows)
    write_metrics(Path(args.metrics), metric_rows)
    print(f"[OK] wrote pseudo-plastic morphology plots to {outdir}")
    print(f"[OK] wrote {args.metrics}")


if __name__ == "__main__":
    main()
