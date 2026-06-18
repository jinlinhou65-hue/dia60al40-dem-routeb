from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FitResult:
    model: str
    slope: float
    intercept: float
    r2: float
    sample_count: int
    parameters: dict[str, float]


def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("linear_fit requires at least two paired samples")
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    ssxx = sum((x - xbar) ** 2 for x in xs)
    if ssxx == 0:
        raise ValueError("linear_fit x values must not all be equal")
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / ssxx
    intercept = ybar - slope * xbar
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
    return slope, intercept, r2


def contact_gini(values: list[float]) -> float:
    clean = sorted(abs(value) for value in values if math.isfinite(value))
    if not clean or sum(clean) == 0:
        return 0.0
    n = len(clean)
    weighted = sum((idx + 1) * value for idx, value in enumerate(clean))
    return (2.0 * weighted) / (n * sum(clean)) - (n + 1.0) / n


def contact_participation(values: list[float]) -> float:
    clean = [abs(value) for value in values if math.isfinite(value)]
    total = sum(clean)
    if not clean or total == 0:
        return 0.0
    return total * total / (len(clean) * sum(value * value for value in clean))


def pearson(xs: list[float], ys: list[float]) -> float | None:
    pairs = [(x, y) for x, y in zip(xs, ys) if math.isfinite(x) and math.isfinite(y)]
    if len(pairs) < 2:
        return None
    xvals = [x for x, _ in pairs]
    yvals = [y for _, y in pairs]
    xbar = sum(xvals) / len(xvals)
    ybar = sum(yvals) / len(yvals)
    num = sum((x - xbar) * (y - ybar) for x, y in pairs)
    denx = sum((x - xbar) ** 2 for x in xvals)
    deny = sum((y - ybar) ** 2 for y in yvals)
    if denx <= 0 or deny <= 0:
        return None
    return num / math.sqrt(denx * deny)


def compaction_fits(
    pressures_mpa: list[float],
    densities: list[float],
    *,
    dm: float | None = None,
) -> list[FitResult]:
    results: list[FitResult] = []
    for fitter in (fit_heckel, fit_kawakita, fit_huang):
        try:
            result = fitter(pressures_mpa, densities, dm=dm)
        except ValueError:
            continue
        results.append(result)
    return results


def fit_heckel(
    pressures_mpa: list[float],
    densities: list[float],
    *,
    dm: float | None = None,
) -> FitResult:
    del dm
    pairs = [
        (p, math.log(1.0 / (1.0 - d)))
        for p, d in zip(pressures_mpa, densities)
        if p > 0 and 0 < d < 1
    ]
    return _fit_pairs("Heckel", pairs, lambda slope, intercept: {"K": slope, "A": intercept})


def fit_kawakita(
    pressures_mpa: list[float],
    densities: list[float],
    *,
    dm: float | None = None,
) -> FitResult:
    del dm
    if not densities:
        raise ValueError("Kawakita fit requires density samples")
    d0 = densities[0]
    pairs: list[tuple[float, float]] = []
    for p, d in zip(pressures_mpa, densities):
        if p <= 0 or d <= 0:
            continue
        c = 1.0 - d0 / d
        if c > 0:
            pairs.append((p, p / c))

    def params(slope: float, intercept: float) -> dict[str, float]:
        if slope == 0 or intercept == 0:
            raise ValueError("invalid Kawakita regression")
        a = 1.0 / slope
        b = slope / intercept
        return {"a": a, "b": b, "D0": d0}

    return _fit_pairs("Kawakita", pairs, params)


def fit_huang(
    pressures_mpa: list[float],
    densities: list[float],
    *,
    dm: float | None = None,
) -> FitResult:
    if len(densities) < 3:
        raise ValueError("Huang fit requires at least three density samples")
    d0 = densities[0]
    density_max = max(densities)
    dm_value = dm if dm is not None else min(0.999, max(density_max + 0.03, density_max * 1.01))
    pairs: list[tuple[float, float]] = []
    for p, d in zip(pressures_mpa, densities):
        if p <= 0 or d <= d0 or d >= dm_value:
            continue
        ratio = (dm_value - d0) / (d - d0)
        if ratio > 1.0 and math.log(ratio) > 0:
            pairs.append((math.log(p), math.log(math.log(ratio))))

    def params(slope: float, intercept: float) -> dict[str, float]:
        return {"n": slope, "M": math.exp(-intercept), "D0": d0, "Dm": dm_value}

    return _fit_pairs("Huang", pairs, params)


def _fit_pairs(
    model: str,
    pairs: list[tuple[float, float]],
    parameter_builder,
) -> FitResult:
    if len(pairs) < 2:
        raise ValueError(f"{model} fit has insufficient valid samples")
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    slope, intercept, r2 = linear_fit(xs, ys)
    parameters = parameter_builder(slope, intercept)
    return FitResult(model, slope, intercept, r2, len(pairs), parameters)
