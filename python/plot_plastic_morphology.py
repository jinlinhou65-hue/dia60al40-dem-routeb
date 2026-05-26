from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from dem_stage_metadata import UM_PER_CM, particle_shape, read_liggghts_dump, stages_from_model_parameters


W_UM = 400.0
Point = tuple[float, float]


def import_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

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
    return plt, Polygon, Rectangle


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


def polygon_area(poly: list[Point]) -> float:
    if len(poly) < 3:
        return 0.0
    acc = 0.0
    for i, (x0, y0) in enumerate(poly):
        x1, y1 = poly[(i + 1) % len(poly)]
        acc += x0 * y1 - x1 * y0
    return abs(acc) * 0.5


def add_contact(metric: dict[str, float], overlap_um: float, nx: float, ny: float) -> None:
    if overlap_um <= 0.0:
        return
    metric["contact_count"] += 1.0
    metric["overlap_sum_um"] += overlap_um
    metric["max_overlap_um"] = max(metric["max_overlap_um"], overlap_um)
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
            nx, ny = (1.0, 0.0) if dist <= 1e-12 else (dx / dist, dy / dist)
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
    severity = metric["overlap_sum_um"] / max(r, 1e-9)
    if material(row) == "Al":
        gain = 0.36
        cap = 0.62
    else:
        gain = 0.045
        cap = 0.14
    flatten = min(cap, gain * severity)
    minor = max(0.35 * r, r * (1.0 - flatten))
    major = min(1.9 * r, r * r / minor)
    # The contact normal is the compression direction; visible elongation is
    # perpendicular to it. This keeps the pseudo-plastic sketch mechanically sane.
    angle = principal_direction(metric) + 0.5 * math.pi
    return major, minor, angle, flatten


def die_polygon(height_um: float) -> list[Point]:
    return [(0.0, 0.0), (W_UM, 0.0), (W_UM, height_um), (0.0, height_um)]


def clip_halfplane(poly: list[Point], a: float, b: float, c: float, eps: float = 1e-9) -> list[Point]:
    # Keep a*x + b*y + c <= 0.
    if not poly:
        return []

    def value(p: Point) -> float:
        return a * p[0] + b * p[1] + c

    def intersect(p0: Point, p1: Point, v0: float, v1: float) -> Point:
        denom = v0 - v1
        if abs(denom) <= 1e-14:
            return p1
        t = v0 / denom
        return (p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1]))

    out: list[Point] = []
    prev = poly[-1]
    prev_v = value(prev)
    prev_inside = prev_v <= eps
    for cur in poly:
        cur_v = value(cur)
        cur_inside = cur_v <= eps
        if cur_inside:
            if not prev_inside:
                out.append(intersect(prev, cur, prev_v, cur_v))
            out.append(cur)
        elif prev_inside:
            out.append(intersect(prev, cur, prev_v, cur_v))
        prev = cur
        prev_v = cur_v
        prev_inside = cur_inside
    return out


def clip_to_die(poly: list[Point], height_um: float) -> list[Point]:
    poly = clip_halfplane(poly, -1.0, 0.0, 0.0)
    poly = clip_halfplane(poly, 1.0, 0.0, -W_UM)
    poly = clip_halfplane(poly, 0.0, -1.0, 0.0)
    poly = clip_halfplane(poly, 0.0, 1.0, -height_um)
    return poly


def clip_outside_diamond(poly: list[Point], al_row: dict[str, str], dia_row: dict[str, str]) -> list[Point]:
    ax, ay, _ = particle_state(al_row)
    dx, dy, dr = particle_state(dia_row)
    nx = ax - dx
    ny = ay - dy
    norm = math.hypot(nx, ny)
    if norm <= 1e-12:
        return poly
    nx /= norm
    ny /= norm
    # The diamond phase is rendered as an octagon, not as its full
    # circumcircle. Use the octagon inradius as the Al exclusion boundary so
    # the morphology plot does not invent extra diamond-blocked pore volume.
    effective_r = dr * math.cos(math.radians(22.5))
    tx = dx + nx * effective_r
    ty = dy + ny * effective_r
    # Keep the side of the tangent plane away from the diamond center. This is a
    # boundary constraint, not a post-plot crop, so Al wraps around diamond space.
    return clip_halfplane(poly, -nx, -ny, nx * tx + ny * ty)


def clip_al_voronoi(poly: list[Point], rows: list[dict[str, str]], row_index: int) -> list[Point]:
    xi, yi, _ = particle_state(rows[row_index])
    for j, other in enumerate(rows):
        if j == row_index or material(other) != "Al":
            continue
        xj, yj, _ = particle_state(other)
        nx = xj - xi
        ny = yj - yi
        if math.hypot(nx, ny) <= 1e-12:
            continue
        mx = 0.5 * (xi + xj)
        my = 0.5 * (yi + yj)
        poly = clip_halfplane(poly, nx, ny, -(nx * mx + ny * my))
        if len(poly) < 3:
            return []
    return poly


def al_constraint_cell(rows: list[dict[str, str]], row_index: int, height_um: float) -> list[Point]:
    poly = die_polygon(height_um)
    poly = clip_al_voronoi(poly, rows, row_index)
    if len(poly) < 3:
        return []
    row = rows[row_index]
    for other in rows:
        if material(other) == "Diamond":
            poly = clip_outside_diamond(poly, row, other)
            if len(poly) < 3:
                return []
    return clip_to_die(poly, height_um)


def scale_polygon(poly: list[Point], center: Point, scale: float) -> list[Point]:
    cx, cy = center
    return [(cx + (x - cx) * scale, cy + (y - cy) * scale) for x, y in poly]


def transformed_polygon(
    x: float,
    y: float,
    major: float,
    minor: float,
    angle: float,
    vertices: int,
    base_rotation: float = 0.0,
) -> list[Point]:
    ca = math.cos(angle)
    sa = math.sin(angle)
    pts: list[Point] = []
    for k in range(vertices):
        t = base_rotation + 2.0 * math.pi * k / vertices
        lx = major * math.cos(t)
        ly = minor * math.sin(t)
        pts.append((x + lx * ca - ly * sa, y + lx * sa + ly * ca))
    return pts


def diamond_polygon(row: dict[str, str], major: float, minor: float, angle: float, height_um: float) -> list[Point]:
    x, y, _ = particle_state(row)
    poly = transformed_polygon(x, y, major, minor, angle, vertices=8, base_rotation=math.radians(22.5))
    return clip_to_die(poly, height_um)


def nominal_projected_area(row: dict[str, str]) -> float:
    _, _, r = particle_state(row)
    if material(row) == "Al":
        return math.pi * r * r
    return 2.0 * math.sqrt(2.0) * r * r


def al_render_polygon(
    rows: list[dict[str, str]],
    row_index: int,
    height_um: float,
) -> tuple[list[Point], float, float, float]:
    row = rows[row_index]
    x, y, _ = particle_state(row)
    cell = al_constraint_cell(rows, row_index, height_um)
    cell_area = polygon_area(cell)
    target_area = nominal_projected_area(row)
    if cell_area <= 1e-9:
        return [], cell_area, 0.0, 0.0

    # Scale the constrained cell to the particle's nominal Al area. This avoids
    # both false material loss from visual clipping and false material creation
    # from filling the whole cell in loose stages.
    scale = min(0.995, math.sqrt(target_area / cell_area))
    poly = scale_polygon(cell, (x, y), scale)
    rendered_area = polygon_area(poly)
    return poly, cell_area, rendered_area, scale


def plot_stage(
    root: Path,
    stage_id: str,
    stage_meta: tuple[str, float, float, float, float],
    outdir: Path,
    metric_rows: list[dict[str, str]],
) -> None:
    plt, Polygon, Rectangle = import_matplotlib()
    dump = latest_stage_dump(root, stage_id)
    rows = read_liggghts_dump(dump)
    _, target_rho, height_um, _, _ = stage_meta
    metrics = contact_metrics(rows, height_um)

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=180)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-25, 425)
    ax.set_ylim(-25, max(230, height_um + 35))
    ax.add_patch(Rectangle((0, 0), W_UM, height_um, fill=False, linewidth=1.3, edgecolor="#444444"))

    pending_diamonds: list[tuple[list[Point], dict[str, str]]] = []
    for i, row in enumerate(rows):
        pid = str(row.get("id", i + 1))
        x, y, r = particle_state(row)
        met = metrics[pid]
        major, minor, angle, flatten = deformation(row, met)
        shape = particle_shape(row)
        mat = material(row)
        nominal_area = nominal_projected_area(row)
        cell_area = 0.0
        area_scale = 1.0

        if mat == "Al":
            poly, cell_area, rendered_area, area_scale = al_render_polygon(rows, i, height_um)
            if len(poly) >= 3 and rendered_area > 1e-8:
                ax.add_patch(
                    Polygon(poly, closed=True, facecolor="#d7e9ff", edgecolor="#235789", linewidth=0.7, alpha=0.96)
                )
        else:
            poly = diamond_polygon(row, major, minor, angle, height_um)
            rendered_area = polygon_area(poly)
            pending_diamonds.append((poly, row))

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
                "nominal_area_um2": f"{nominal_area:.9g}",
                "cell_area_um2": f"{cell_area:.9g}",
                "rendered_area_um2": f"{rendered_area:.9g}",
                "area_scale": f"{area_scale:.9g}",
                "polygon_vertices": f"{len(poly)}",
            }
        )

    for poly, _ in pending_diamonds:
        if len(poly) >= 3 and polygon_area(poly) > 1e-8:
            ax.add_patch(Polygon(poly, closed=True, facecolor="#333333", edgecolor="#111111", linewidth=0.75, alpha=0.97))

    ax.set_xlabel("x (um)")
    ax.set_ylabel("y (um)")
    ax.set_title(f"Constrained polygonal morphology: {stage_id}, target rho={target_rho:.3f}")
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
        "nominal_area_um2",
        "cell_area_um2",
        "rendered_area_um2",
        "area_scale",
        "polygon_vertices",
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
    for stage_meta in stages_from_model_parameters(root):
        plot_stage(root, stage_meta[0], stage_meta, outdir, metric_rows)
    write_metrics(Path(args.metrics), metric_rows)
    print(f"[OK] wrote constrained polygonal morphology plots to {outdir}")
    print(f"[OK] wrote {args.metrics}")


if __name__ == "__main__":
    main()
