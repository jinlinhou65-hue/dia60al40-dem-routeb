# 03 Zhang Particle Scale

## 阶段目的

解决 Zhang 论文的 DEM 校准问题：当前轻量 DEM 已经能输出真实接触力和力链指标，
但还需要判断 C/D/E 三个粒径组的参数在粒子数提高后是否稳定。

## 当前已完成

| 内容 | 状态 |
|---|---|
| 6-job 推荐 sweep | 成功 |
| 9-job 稳健性 sweep | 成功，但全局参数不稳健 |
| 36-job C/D/E size-specific sweep | 成功 |
| C/D/E 各自候选参数 | 已得到 |
| `particle_count_scale=2` C/D/E demo | 已成功 |
| D 组 verifier 半径误判 | 已修复 |

## 当前候选参数

| Size case | Emax GPa | mu scale | seed | 1x P95 MPa |
|---|---:|---:|---:|---:|
| C | 44.772 | 0.654 | 2 | 634.203 |
| D | 37.517 | 0.770 | 2 | 620.578 |
| E | 37.517 | 0.693 | 2 | 604.217 |

## 2x 成功证据

| Run | Size | 状态 |
|---|---|---|
| `27875950305` | C | success |
| `27875951506` | D | success |
| `27875952754` | E | success |

调度 run：`zhang-scale-pilot.yml` run `27875947935`。

## 当前未完成

2x workflow 已成功，但 artifacts 还需要导入本阶段目录并形成判读报告。网页成功
只能证明运行完成，不能替代仓库内的可检阅数据。

## 下一步动作

1. 下载或通过 workflow 导入三个 2x DEM ensemble artifacts。
2. 在本阶段目录建立：

```text
03_zhang_particle_scale/
  data/
    2x_ensemble_runs.csv
    2x_pressure_summary.csv
    1x_vs_2x_comparison.csv
  figures/
    pressure_density_1x_vs_2x.png
    zhang_force_chain_metrics_1x_vs_2x.png
  evidence/
    github_runs.md
  report.md
```

3. 判读 2x 是否保持：
   - 572-638 MPa endpoint pressure window。
   - Zhang trend gate。
   - D1/D2 随压实下降或合理收敛。
   - 接触数量和强接触比例不出现非物理突变。

## 验收门槛

| 验收项 | 判定 |
|---|---|
| 三个 2x run artifact 已导入 | 待完成 |
| 1x vs 2x 对比表已生成 | 待完成 |
| P95 和 trend 结论明确 | 待完成 |
| 是否继续 4x/8x 或 WSL2 有明确建议 | 待完成 |

