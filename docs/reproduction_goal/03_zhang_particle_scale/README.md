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

## 已归档产物

```text
03_zhang_particle_scale/
  data/
    combined_2x_27875950305_27875951506_27875952754/
    1x_vs_2x_comparison.csv
    zhang_particle_scale_acceptance.csv
    summary.json
  evidence/
    github_runs.md
    run_27875950305/
    run_27875951506/
    run_27875952754/
  figures/
    p95_1x_vs_2x.png
    p95_delta_percent.png
  report.md
```

## 下一步动作

1. 不启动 4x/8x。
2. 在 pscale=2 上做窄范围再标定：
   - 提高 endpoint modulus 或调整加载路径，使 P95 回到 572-638 MPa。
   - D/E 同时校准 participation trend。
   - 保留 `allow_evidence_mismatch=true`，缺文件仍失败，趋势不通过进入 review。
3. 只有 C/D/E 同时满足 pressure window 和 trend gate 后，才启动 4x 粒子数 pilot。

## 验收门槛

| 验收项 | 判定 |
|---|---|
| 三个 2x run artifact 已导入 | 通过 |
| 1x vs 2x 对比表已生成 | 通过 |
| P95 和 trend 结论明确 | 通过：2x 压力显著偏低，D/E trend review |
| 是否继续 4x/8x 或 WSL2 有明确建议 | 通过：暂不进入 4x/8x，先 pscale=2 重标定 |
