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
| 2x C/D/E ensemble artifacts | 已导入 |
| 1x vs 2x 判读报告 | 已生成，结论为 `review` |
| pscale=2 pressure-first 重标定 | 已运行并导入，结论为分 size 继续校准 |

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

## 当前判读

2x workflow 和 verifier 路径已经证明可用，但 2x 结果没有保持 1x 的压力标定：

| Size | 1x P95 MPa | 2x P95 MPa | 变化 | 2x trend |
|---|---:|---:|---:|---|
| C | 634.203 | 411.866 | -35.06% | pass |
| D | 620.578 | 413.405 | -33.38% | review |
| E | 604.217 | 371.868 | -38.45% | review |

因此本阶段结论是：**不要直接进入 4x/8x；先在 `particle_count_scale=2`
重新标定 endpoint modulus、加载路径或接触参数。**

## 重标定结果

`zhang-pscale2-recalibration.yml` 已运行 9 个 demo job，并导入三条
ensemble summary。结果显示：

| Size | Best Emax GPa | Best P95 MPa | Pressure Gate | Trend | 下一步 |
|---|---:|---:|---|---|---|
| C | 61.962 | 567.207 | review | pass | 继续窄扫 Emax/加载路径，接近窗口下限 |
| D | 57.173 | 634.795 | pass | review | 固定压力候选，调 participation trend |
| E | 63.559 | 480.140 | review | review | 继续提高 Emax 或调整加载路径 |

重标定报告：`pscale2_recalibration_report.md`。

## 已归档产物

```text
03_zhang_particle_scale/
  data/
    combined_2x_27875950305_27875951506_27875952754/
    1x_vs_2x_comparison.csv
    pscale2_recalibration_acceptance.csv
    pscale2_recalibration_candidates.csv
    pscale2_recalibration_size_summary.csv
    pscale2_recalibration_summary.json
    zhang_particle_scale_acceptance.csv
    summary.json
  evidence/
    github_runs.md
    pscale2_recalibration_run_27882367107/
    pscale2_recalibration_run_27882368312/
    pscale2_recalibration_run_27882369414/
    run_27875950305/
    run_27875951506/
    run_27875952754/
  figures/
    p95_1x_vs_2x.png
    p95_delta_percent.png
    pscale2_recalibration_p95.png
  pscale2_recalibration_report.md
  report.md
```

## 下一步动作

1. 不启动 4x/8x。
2. 分 size 继续 pscale=2 校准：
   - C：围绕 `Emax≈62 GPa` 与加载路径做窄扫，目标是从 `567 MPa` 推入窗口。
   - D：以 `Emax=57.173 GPa`、`mu=0.77` 为压力候选，做 mu/contact-law 小矩阵，让 participation delta 转正。
   - E：继续提高 endpoint modulus 或调整加载路径，先把 P95 从 `480 MPa` 拉向窗口。
3. 只有 C/D/E 同时满足 pressure window 和 trend gate 后，才启动 4x 粒子数 pilot。

计划文件：`data/pscale2_recalibration_plan.json`。

## 验收门槛

| 验收项 | 判定 |
|---|---|
| 三个 2x run artifact 已导入 | 通过 |
| 1x vs 2x 对比表已生成 | 通过 |
| P95 和 trend 结论明确 | 通过：2x 压力显著偏低，D/E trend review |
| pscale=2 重标定结果已导入 | 通过：C 接近窗口，D 压力回窗但 trend review，E 仍偏低 |
| 是否继续 4x/8x 或 WSL2 有明确建议 | 通过：暂不进入 4x/8x，继续 pscale=2 分 size 校准 |
