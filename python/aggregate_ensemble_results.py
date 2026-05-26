from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def import_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.linewidth": 1.0,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    return plt


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_parameters(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return {row["parameter"]: row["value"] for row in rows if "parameter" in row and "value" in row}


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def collect_runs(root: Path) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for curve in sorted(root.rglob("pressure_density_curve.csv")):
        dem_dir = curve.parent
        summary_path = dem_dir / "pressure_density_summary.csv"
        params_path = dem_dir / "model_parameters.csv"
        if not summary_path.exists() or not params_path.exists():
            continue
        curve_rows = read_csv(curve)
        summary_rows = read_csv(summary_path)
        params = read_parameters(params_path)
        p95 = math.nan
        for row in summary_rows:
            if "p_target_mpa" in row:
                p95 = float(row["p_target_mpa"])
                break
            if row.get("metric") == "p_at_target_mpa":
                p95 = float(row["value"])
                break
        runs.append(
            {
                "artifact": dem_dir.parent.name,
                "diamond_size_case": params.get("diamond_size_case", "?"),
                "al_radius_um": float(params.get("Al_dem_radius_um", "nan")),
                "diamond_ds_radius_um": float(params.get("diamond_dem_radius_DS_um", "nan")),
                "diamond_dl_radius_um": float(params.get("diamond_dem_radius_DL_um", "nan")),
                "diamond_count_ds": int(float(params.get("diamond_count_DS", "0"))),
                "diamond_count_dl": int(float(params.get("diamond_count_DL", "0"))),
                "al_area_fraction": float(params.get("Al_area_fraction", "nan")),
                "diamond_area_fraction": float(params.get("diamond_area_fraction", "nan")),
                "seed_index": int(float(params.get("DEM_seed_index", "0"))),
                "e_al_emax_gpa": float(params.get("E_Al_smoothstep_Emax", "nan")),
                "mu_scale": float(params.get("mu_scale", "nan")),
                "p95_mpa": p95,
                "curve": curve_rows,
            }
        )
    return runs


def write_ensemble_csv(path: Path, runs: list[dict[str, object]]) -> None:
    p95s = [float(run["p95_mpa"]) for run in runs if not math.isnan(float(run["p95_mpa"]))]
    if not p95s:
        raise SystemExit("[FAIL] no finite p95_mpa values found in ensemble summaries")
    fieldnames = [
        "n_runs",
        "p95_mean_mpa",
        "p95_stdev_mpa",
        "p95_min_mpa",
        "p95_max_mpa",
        "p95_range_mpa",
        "p95_cv",
    ]
    row = {
        "n_runs": len(p95s),
        "p95_mean_mpa": f"{mean(p95s):.9g}",
        "p95_stdev_mpa": f"{stdev(p95s):.9g}",
        "p95_min_mpa": f"{min(p95s):.9g}" if p95s else "nan",
        "p95_max_mpa": f"{max(p95s):.9g}" if p95s else "nan",
        "p95_range_mpa": f"{(max(p95s) - min(p95s)):.9g}" if p95s else "nan",
        "p95_cv": f"{(stdev(p95s) / mean(p95s)):.9g}" if p95s and mean(p95s) else "nan",
    }
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


def write_case_summary_csv(path: Path, runs: list[dict[str, object]]) -> None:
    groups: dict[str, list[dict[str, object]]] = {}
    for run in runs:
        groups.setdefault(str(run["diamond_size_case"]), []).append(run)
    fieldnames = [
        "diamond_size_case",
        "n_runs",
        "p95_mean_mpa",
        "p95_stdev_mpa",
        "p95_min_mpa",
        "p95_max_mpa",
        "al_radius_um",
        "diamond_ds_radius_um",
        "diamond_dl_radius_um",
        "diamond_count_ds",
        "diamond_count_dl",
        "al_area_fraction",
        "diamond_area_fraction",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for case_id in sorted(groups):
            case_runs = groups[case_id]
            p95s = [float(run["p95_mpa"]) for run in case_runs if not math.isnan(float(run["p95_mpa"]))]
            first = case_runs[0]
            writer.writerow(
                {
                    "diamond_size_case": case_id,
                    "n_runs": len(p95s),
                    "p95_mean_mpa": f"{mean(p95s):.9g}",
                    "p95_stdev_mpa": f"{stdev(p95s):.9g}",
                    "p95_min_mpa": f"{min(p95s):.9g}",
                    "p95_max_mpa": f"{max(p95s):.9g}",
                    "al_radius_um": first["al_radius_um"],
                    "diamond_ds_radius_um": first["diamond_ds_radius_um"],
                    "diamond_dl_radius_um": first["diamond_dl_radius_um"],
                    "diamond_count_ds": first["diamond_count_ds"],
                    "diamond_count_dl": first["diamond_count_dl"],
                    "al_area_fraction": first["al_area_fraction"],
                    "diamond_area_fraction": first["diamond_area_fraction"],
                }
            )


def write_run_csv(path: Path, runs: list[dict[str, object]]) -> None:
    fieldnames = [
        "artifact",
        "diamond_size_case",
        "seed_index",
        "e_al_emax_gpa",
        "mu_scale",
        "al_radius_um",
        "diamond_ds_radius_um",
        "diamond_dl_radius_um",
        "diamond_count_ds",
        "diamond_count_dl",
        "al_area_fraction",
        "diamond_area_fraction",
        "p95_mpa",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for run in sorted(
            runs,
            key=lambda r: (
                str(r["diamond_size_case"]),
                float(r["e_al_emax_gpa"]),
                float(r["mu_scale"]),
                int(r["seed_index"]),
            ),
        ):
            writer.writerow({name: run[name] for name in fieldnames})


def plot_ensemble(path: Path, runs: list[dict[str, object]]) -> None:
    plt = import_matplotlib()
    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=180)
    for run in sorted(runs, key=lambda r: (str(r["diamond_size_case"]), int(r["seed_index"]))):
        curve = run["curve"]
        xs = [float(row.get("actual_rho_total", row.get("rho_total_measured", "nan"))) for row in curve]  # type: ignore[index]
        ys = [float(row["pressure_mpa"]) for row in curve]  # type: ignore[index]
        ax.plot(
            xs,
            ys,
            marker="o",
            linewidth=1.2,
            markersize=3.5,
            label=f"{run['diamond_size_case']} seed {run['seed_index']}",
        )
    ax.axvline(0.95, color="#444444", linestyle="--", linewidth=0.9)
    ax.axhline(200.0, color="#aa3333", linestyle=":", linewidth=1.0)
    ax.set_xlabel("total relative density")
    ax.set_ylabel("top punch pressure (MPa)")
    ax.set_title("DEM pressure-density ensemble")
    ax.tick_params(direction="in", top=True, right=True)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_case_p95(path: Path, runs: list[dict[str, object]]) -> None:
    plt = import_matplotlib()
    groups: dict[str, list[float]] = {}
    for run in runs:
        value = float(run["p95_mpa"])
        if not math.isnan(value):
            groups.setdefault(str(run["diamond_size_case"]), []).append(value)
    labels = sorted(groups)
    means = [mean(groups[label]) for label in labels]
    errors = [stdev(groups[label]) for label in labels]
    fig, ax = plt.subplots(figsize=(5.6, 3.8), dpi=180)
    ax.bar(labels, means, yerr=errors, capsize=4, color="#4C78A8", edgecolor="#222222", linewidth=0.8)
    ax.axhline(200.0, color="#aa3333", linestyle=":", linewidth=1.0)
    ax.set_xlabel("diamond size case")
    ax.set_ylabel("P at rho=0.95 (MPa)")
    ax.set_title("Size-case sensitivity at 60/40 area fraction")
    ax.tick_params(direction="in", top=True, right=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="ensemble_inputs")
    parser.add_argument("--outdir", default="ensemble_summary")
    args = parser.parse_args()

    root = Path(args.root)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    runs = collect_runs(root)
    if not runs:
        raise SystemExit(f"[FAIL] no pressure_density_curve.csv files found under {root}")

    write_run_csv(outdir / "ensemble_runs.csv", runs)
    write_ensemble_csv(outdir / "ensemble_pressure_summary.csv", runs)
    write_case_summary_csv(outdir / "ensemble_pressure_summary_by_size_case.csv", runs)
    plot_ensemble(outdir / "ensemble_pressure_density.png", runs)
    plot_case_p95(outdir / "p95_by_diamond_size_case.png", runs)
    print(f"[OK] aggregated {len(runs)} DEM run(s) into {outdir}")


if __name__ == "__main__":
    main()
