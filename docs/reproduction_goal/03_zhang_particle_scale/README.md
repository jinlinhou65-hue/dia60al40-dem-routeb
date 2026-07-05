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
| pscale=2 size-specific follow-up plan | 已生成 10-job GitHub Actions 调度矩阵 |
| pscale=2 size-specific follow-up results | 已运行并导入，C 进入窗口且 trend pass，D/E 仍需校准 |
| pscale=2 C seed robustness recheck | 已运行并导入，结论为 C 不具备 seed 稳健性 |
| pscale=2 C pressure-lift recheck | 已运行并导入；均值回窗但仅 2/5 seeds 同时通过双门槛 |
| pscale=2 C 4x-settle recheck | 已运行并导入；trend 全 pass，但压力稳健性显著恶化 |
| pscale=2 C settle=2 midpoint | 已运行并导入；trend 5/5，但压力窗口 0/5、CV 高于 scale 1/4，故拒绝 |
| pscale=2 C 25 cm/s loading-rate recheck | 已运行并导入；trend 与双门槛覆盖改善，但 CV 增加 33.52%，故拒绝 |
| Zhang 接触模型与阻尼参数审计 | 已完成；论文阻尼系数 0.2 不等同于 LIGGGHTS 恢复系数 |
| pscale=2 C sidewall-friction paired recheck | 已预注册 10-job 计划，待 GitHub Actions 实算 |

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

## 下一轮 follow-up 矩阵

`zhang-pscale2-followup.yml` 将运行 3 个 dispatch payload，合计 10 个 demo
DEM job。矩阵只围绕上轮结果的主要矛盾调整，不进入 4x/8x：

| Size | 目的 | Emax candidates GPa | mu scale candidates | Jobs |
|---|---|---|---|---:|
| C | trend 已 pass，压力略低，围绕局部最优做窄扫 | `60.462, 61.462, 62.462, 63.462` | `0.654` | 4 |
| D | 压力已回窗，固定 Emax，调高摩擦看 participation 是否转正 | `57.173` | `0.77, 0.847, 0.963` | 3 |
| E | 压力远低，先按比例提高 endpoint modulus | `75.454, 79.426, 87.368` | `0.693` | 3 |

计划文件：`data/pscale2_followup_plan.json`。

## follow-up 结果

`zhang-pscale2-followup.yml` run `27883030240` 已成功调度 C/D/E 三条 DEM
run，三条 ensemble summary 均已导入。判读结果：

| Size | Best Emax GPa | Best mu | Best P95 MPa | Pressure Gate | Trend | 下一步 |
|---|---:|---:|---:|---|---|---|
| C | 63.462 | 0.654 | 586.646 | pass | pass | 保留候选，做 seed robustness recheck |
| D | 57.173 | 0.770 | 634.795 | pass | review | 压力和力链趋势冲突，不能只靠提高摩擦解决 |
| E | 87.368 | 0.693 | 543.689 | review | pass | 趋势可用但压力仍低，继续提高压力或调整加载路径 |

follow-up 报告：`pscale2_followup_report.md`。

## C seed robustness recheck

`zhang-pscale2-c-seed-recheck.yml` 固定 follow-up 中唯一同时满足 pressure
window 和 trend gate 的 C 候选，只改变随机 seed。该 recheck 用于判断 C 候选是否
稳健，而不是继续扩大参数搜索。

| Size | Emax GPa | Mu | Particle scale | Seeds | Jobs | 目的 |
|---|---:|---:|---:|---|---:|---|
| C | 63.462 | 0.654 | 2 | `0,1,2,3,4` | 5 | 验证 C 候选是否通过多随机初始排列 |

计划文件：`data/pscale2_c_seed_recheck_plan.json`。

执行证据：`zhang-pscale2-c-seed-recheck.yml` run `27898768547` 成功，
其调度的 `dia60al40-dem.yml` run `27898770533` 中 5 个 seed DEM job 和
aggregate ensemble 全部成功。ensemble summary artifact 已导入到
`evidence/pscale2_c_seed_recheck_run_27898770533/`。

判读结果：C 不是 seed-robust 候选。5 个 seed 中只有 1 个 seed 同时满足
pressure window 和 trend gate；P95 平均值为 `524.619 MPa`，低于 Zhang
`572-638 MPa` 端点窗口。

| Seeds | Trend pass | Pressure window | Pass + window | P95 mean MPa | P95 min MPa | P95 max MPa | Decision |
|---:|---:|---:|---:|---:|---:|---:|---|
| 5 | 4 | 1 | 1 | 524.619 | 493.878 | 586.646 | `c_candidate_not_seed_robust` |

报告：`pscale2_c_seed_recheck_report.md`。

## C pressure-lift recheck

上一轮 C recheck 的 5-seed 平均 P95 为 `524.619 MPa`。本轮用
`63.462 * 600 / 524.619 = 72.581 GPa` 得到待验证的 Emax，并保持
`mu=0.654`、`particle_count_scale=2`、size C 和 seeds `0..4` 不变。

这不是把线性比例关系当成物理结论，而是用 5 个轻量 DEM job 检验该假设：

| Size | Source Emax | Target Emax | Mu | Seeds | Jobs | Changed variable |
|---|---:|---:|---:|---|---:|---|
| C | 63.462 GPa | 72.581 GPa | 0.654 | `0,1,2,3,4` | 5 | `e_al_emax_gpa` only |

计划文件：`data/pscale2_c_pressure_lift_recheck_plan.json`。

GitHub dispatcher run `28709922833` 和 DEM run `28709925303` 均成功，5 个
seed job 与 aggregate ensemble 全部完成。结果证明 Emax 抬升有效，但比例假设
高估了平均压力响应：Emax 增加 `14.37%`，平均 P95 只增加 `9.45%`。

| Metric | Baseline | Emax 72.581 GPa | Result |
|---|---:|---:|---|
| Mean P95 MPa | 524.619 | 574.211 | 平均值进入 572-638 MPa 窗口 |
| P95 CV | 0.0804 | 0.0396 | 离散性下降 50.80% |
| Trend pass | 4/5 | 4/5 | 未改善全 seed trend gate |
| Pressure window | 1/5 | 3/5 | 有改善但未稳健 |
| Pass + window | 1/5 | 2/5 | 仍不满足 seed robustness |

因此保留 `Emax=72.581 GPa` 作为 C 的压力参考，不再把继续提高 Emax 当作
唯一控制变量。下一轮应只改变一个加载路径或接触松弛变量以降低 seed 方差，
保持 `mu=0.654` 并复跑相同 seeds `0..4`。

结果报告：`pscale2_c_pressure_lift_report.md`。

## C 4x-settle recheck

pressure-lift 结果的主要矛盾已经从平均压力不足变成 seed 方差。下一轮固定
`Emax=72.581 GPa`、`mu=0.654`、size C、`particle_count_scale=2`、压头速度
`50 cm/s`、时间步和 seeds `0..4`，只把各阶段静置步数统一放大 4 倍：

| Control | Baseline demo | 4x-settle test |
|---|---:|---:|
| Initial settle | 20,000 steps | 80,000 steps |
| Per-stage settle | 20,000 steps | 80,000 steps |
| Final settle | 50,000 steps | 200,000 steps |
| DEM jobs | 5 | 5 |

该试验检验更充分的接触松弛是否能降低 seed-to-seed 压力和力链方差。实际
速度、时间步和 settle steps 会写入每个 artifact 的 `model_parameters.csv`。

计划文件：`data/pscale2_c_settle_recheck_plan.json`。

首次 child run `28710435532` 因 workflow heredoc 缩进在 deck 渲染前失败，
没有产生物理结果。修复提交 `e2eb4ea` 后，dispatcher run `28710534299`
调度 child run `28710536524`；5 个 DEM job 与 aggregate ensemble 全部成功，
且 `model_parameters.csv` 记录了 `80k/80k/200k` settle steps。

| Metric | Settle scale 1 | Settle scale 4 | Result |
|---|---:|---:|---|
| Mean P95 MPa | 574.211 | 567.232 | 降低 6.979 MPa，跌出窗口均值下限 |
| P95 CV | 0.0396 | 0.0911 | 增加 130.22%，seed 方差恶化 |
| Trend pass | 4/5 | 5/5 | 力链趋势改善 |
| Pressure window | 3/5 | 1/5 | 压力覆盖恶化 |
| Pass + window | 2/5 | 1/5 | 总体稳健性恶化 |

结论：拒绝 settle scale 4，恢复 scale 1。若继续检验 dwell，下一步只测试
有界中点 scale 2，并继续固定 `Emax=72.581 GPa, mu=0.654`。

结果报告：`pscale2_c_settle_report.md`。

## C settle=2 midpoint result

中点试验不修改旧的 4x workflow，也不重新搜索 Emax 或摩擦系数。它复用相同
五个 seed，并将静置步数设置为 `40k/40k/100k`。GitHub workflow 在调度前
验证 size、粒子倍率、Emax、mu、seed 集和目标步数，防止多变量漂移。

中点结果将与 settle scale 1 和 4 做逐 seed 三组配对。预先固定的接受条件是：

1. trend pass 数高于 scale 1；
2. pass + pressure-window 数不低于 scale 1；
3. 五 seed 平均压力位于 `572-638 MPa`；
4. P95 CV 不超过 scale 1 的 `1.25` 倍。

只有四项同时满足，scale 2 才可作为更好的 C 加载路径候选；否则停止继续调整
dwell，恢复 scale 1 并改测一个不同的加载或接触变量。

计划文件：`data/pscale2_c_settle_midpoint_plan.json`。

dispatcher run `28729401297` 成功调度 child run `28729403153`；五个 DEM
seed job 与 aggregate ensemble 全部成功。summary artifact `8088289183` 的本地
SHA-256 与 GitHub digest `8a94ce39...e3ba4f` 一致，运行参数验证为
`40k/40k/100k`。

| Metric | Settle scale 1 | Settle scale 2 | Settle scale 4 |
|---|---:|---:|---:|
| Mean P95 MPa | 574.211 | 563.323 | 567.232 |
| P95 CV | 0.0396 | 0.1268 | 0.0911 |
| Trend pass | 4/5 | 5/5 | 5/5 |
| Pressure window | 3/5 | 0/5 | 1/5 |
| Pass + window | 2/5 | 0/5 | 1/5 |

scale 2 没有满足预注册的压力均值、CV 和双门槛覆盖要求。其 seed 2 达到
`674.741 MPa`，seed 3 降到 `478.278 MPa`，说明中点静置并未产生平滑插值，
反而放大了不同初始接触网络的重排差异。因此 C 的 dwell 分支到此停止，恢复
settle scale 1。

结果报告：`pscale2_c_settle_midpoint_report.md`。

## C 25 cm/s loading-rate result

dwell 分支已经由 scale 2/4 两个实验排除。本轮恢复 settle scale 1，只把 demo
压头速度从 `50` 降到 `25 cm/s`，并保持 `Emax=72.581 GPa`、`mu=0.654`、
size C、`particle_count_scale=2`、时间步和 seeds `0..4` 不变。速度会写入
`model_parameters.csv` 和 ensemble CSV，artifact 名称也包含速度值。

预先固定的接受条件是：五 seed 平均 P95 仍在 `572-638 MPa`、P95 CV 低于
50 cm/s 基线、trend pass 数不下降、pass + window 覆盖高于基线 2/5。
任一条件不满足，就恢复 50 cm/s 并停止把加载速率作为下一控制变量。

计划文件：`data/pscale2_c_loading_rate_plan.json`。

dispatcher run `28729752015` 成功调度 child run `28729754426`；五个 DEM
seed job 与 aggregate ensemble 全部成功。summary artifact `8088409305` 的本地
SHA-256 与 GitHub digest `2047d65c...27060a` 一致，artifact 运行参数验证为
`25 cm/s`、`dt=2e-10 s`、settle steps `20k/20k/50k`。

| Metric | 50 cm/s baseline | 25 cm/s test | Result |
|---|---:|---:|---|
| Mean P95 MPa | 574.211 | 578.432 | 保持在窗口内 |
| P95 CV | 0.0396 | 0.0528 | 增加 33.52% |
| Trend pass | 4/5 | 5/5 | 改善 1 seed |
| Pressure window | 3/5 | 3/5 | 不变 |
| Pass + window | 2/5 | 3/5 | 改善 1 seed |

降低速度改善了 trend 和双门槛覆盖，但 seed 0/1 压力上升、seed 2/3 压力下降，
导致 CV 明显恶化，未满足预注册的方差门槛。因此拒绝 25 cm/s，恢复 50 cm/s，
并停止把加载速率作为 C 的下一控制变量。

结果报告：`pscale2_c_loading_rate_report.md`。

## Contact-model audit and sidewall-friction plan

对用户提供的 Zhang PDF 做了整本页级复核。该文件实际是 2024 年《机械工程学报》
10 页期刊论文，而不是 2019 年学位论文全文。论文在 PDF p.3（印刷 p.170）给出
Hertz-Mindlin-Deresiewicz、Coulomb、法/切向阻尼系数 `0.2`，但没有阻尼方程、
单位、恢复系数换算或求解器名称。因此不能把 `0.2` 直接写入 LIGGGHTS 的
`coefficientRestitution`，也不能无依据切换到 `hertz/stiffness`。

审计同时确认论文分别扫描 `mu_p` 与 `mu_w`，而当前 `mu_scale` 会一起缩放粒间、
压头和侧壁摩擦。下一轮因此新增 sidewall-only scale，并将 LIGGGHTS-PUBLIC 固定到
提交 `3d5c00f20519e6bb6eb6756f51f1ad36564e649d`。计划在同一次 child run 内执行
`wall scale=1.0/0.019113` 与相同 seeds `0..4`，共 10 个 job；测试点对应有效
Al-wall 和 diamond-wall 摩擦因数约 `0.001`，其余物理量不变。

审计：`zhang_contact_model_audit.md`。
术语表：`zhang_contact_terminology.md`。
机器证据：`data/zhang_contact_parameter_audit.json`。
试验计划：`data/pscale2_c_wall_friction_plan.json`。

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
    pscale2_followup_plan.json
    pscale2_followup_acceptance.csv
    pscale2_followup_candidates.csv
    pscale2_followup_size_summary.csv
    pscale2_followup_summary.json
    pscale2_c_seed_recheck_plan.json
    pscale2_c_seed_recheck_acceptance.csv
    pscale2_c_seed_recheck_candidates.csv
    pscale2_c_seed_recheck_summary.json
    pscale2_c_pressure_lift_recheck_plan.json
    pscale2_c_pressure_lift_acceptance.csv
    pscale2_c_pressure_lift_candidates.csv
    pscale2_c_pressure_lift_paired.csv
    pscale2_c_pressure_lift_summary.json
    pscale2_c_settle_recheck_plan.json
    pscale2_c_settle_acceptance.csv
    pscale2_c_settle_candidates.csv
    pscale2_c_settle_paired.csv
    pscale2_c_settle_summary.json
    pscale2_c_settle_midpoint_plan.json
    pscale2_c_settle_midpoint_acceptance.csv
    pscale2_c_settle_midpoint_candidates.csv
    pscale2_c_settle_midpoint_paired.csv
    pscale2_c_settle_midpoint_summary.json
    pscale2_c_loading_rate_plan.json
    pscale2_c_loading_rate_acceptance.csv
    pscale2_c_loading_rate_candidates.csv
    pscale2_c_loading_rate_paired.csv
    pscale2_c_loading_rate_summary.json
    zhang_contact_parameter_audit.json
    pscale2_c_wall_friction_plan.json
    zhang_particle_scale_acceptance.csv
    summary.json
  evidence/
    github_runs.md
    pscale2_c_seed_recheck_run_27898770533/
    pscale2_c_pressure_lift_recheck_run_28709925303/
    pscale2_c_settle_recheck_run_28710536524/
    pscale2_c_settle_midpoint_run_28729403153/
    pscale2_c_loading_rate_recheck_run_28729754426/
    pscale2_followup_run_27883033303/
    pscale2_followup_run_27883034434/
    pscale2_followup_run_27883035658/
    pscale2_recalibration_run_27882367107/
    pscale2_recalibration_run_27882368312/
    pscale2_recalibration_run_27882369414/
    run_27875950305/
    run_27875951506/
    run_27875952754/
  figures/
    p95_1x_vs_2x.png
    p95_delta_percent.png
    pscale2_followup_p95.png
    pscale2_recalibration_p95.png
    pscale2_c_seed_recheck_p95.png
    pscale2_c_pressure_lift_paired.png
    pscale2_c_settle_paired.png
    pscale2_c_settle_midpoint_paired.png
    pscale2_c_loading_rate_paired.png
  pscale2_c_pressure_lift_report.md
  pscale2_c_seed_recheck_report.md
  pscale2_c_settle_report.md
  pscale2_c_settle_midpoint_report.md
  pscale2_c_loading_rate_report.md
  zhang_contact_model_audit.md
  zhang_contact_terminology.md
  pscale2_followup_report.md
  pscale2_recalibration_report.md
  report.md
```

## 下一步动作

1. 不启动 4x/8x。
2. C：接触律审计已完成。先运行固定 LIGGGHTS 提交下的 `wall scale=1/0.019113` 成对 10-job 试验；不要把论文阻尼 `0.2` 当作恢复系数。
3. D：保留 `Emax=57.173 GPa, mu=0.77` 的压力候选，但改调加载路径、接触律或力链阈值；单纯提高摩擦会让压力掉出窗口。
4. E：以 `Emax=87.368 GPa, mu=0.693` 为趋势候选，继续提高压力或调整加载路径，目标先进入 `572-638 MPa`。
5. 只有 C/D/E 同时满足 pressure window 和 trend gate 后，才启动 4x 粒子数 pilot。

上一轮计划文件：`data/pscale2_recalibration_plan.json`。
follow-up 计划文件：`data/pscale2_followup_plan.json`。
C seed recheck 计划文件：`data/pscale2_c_seed_recheck_plan.json`。
C seed recheck 报告：`pscale2_c_seed_recheck_report.md`。
C pressure-lift 报告：`pscale2_c_pressure_lift_report.md`。
C 4x-settle 报告：`pscale2_c_settle_report.md`。
C settle=2 midpoint 计划：`data/pscale2_c_settle_midpoint_plan.json`。
C settle=2 midpoint 报告：`pscale2_c_settle_midpoint_report.md`。
C 25 cm/s loading-rate 计划：`data/pscale2_c_loading_rate_plan.json`。
C 25 cm/s loading-rate 报告：`pscale2_c_loading_rate_report.md`。
Zhang 接触模型审计：`zhang_contact_model_audit.md`。
C sidewall-friction 成对计划：`data/pscale2_c_wall_friction_plan.json`。

## 验收门槛

| 验收项 | 判定 |
|---|---|
| 三个 2x run artifact 已导入 | 通过 |
| 1x vs 2x 对比表已生成 | 通过 |
| P95 和 trend 结论明确 | 通过：2x 压力显著偏低，D/E trend review |
| pscale=2 重标定结果已导入 | 通过：C 接近窗口，D 压力回窗但 trend review，E 仍偏低 |
| pscale=2 follow-up 矩阵已生成 | 通过：10 个 GitHub demo job，C/D/E 各自只改一个主要变量 |
| pscale=2 follow-up 结果已导入 | 通过：C pass，D/E review |
| pscale=2 C seed recheck 矩阵已生成 | 通过：5 个 GitHub demo job，只变 seed，不变 C 参数 |
| pscale=2 C seed recheck 结果已导入 | review：workflow/artifact 通过，但只有 1/5 seed 同时 pressure pass + trend pass |
| pscale=2 C pressure-lift recheck 矩阵已生成 | 通过：5 个 GitHub demo job，只改变 Emax，保持 mu/size/pscale/seeds 不变 |
| pscale=2 C pressure-lift 结果已导入 | review：平均 P95 回窗且 CV 下降，但只有 2/5 seeds 同时 pressure pass + trend pass |
| pscale=2 C 4x-settle recheck 矩阵已生成 | 通过：5 个 GitHub demo job，只改变 settle duration scale |
| pscale=2 C 4x-settle 结果已导入 | review：trend 5/5 pass，但 CV 恶化、仅 1/5 同时通过双门槛；拒绝 scale 4 |
| pscale=2 C settle=2 midpoint 矩阵已生成 | 通过：5 个 GitHub demo job，固定 Emax/mu/size/pscale/seeds，只把 settle scale 设为 2 |
| pscale=2 C settle=2 midpoint 结果已导入 | review：5/5 trend pass，但 0/5 进入压力窗口、CV=0.1268；拒绝 scale 2 并停止 dwell 分支 |
| pscale=2 C 25 cm/s loading-rate 矩阵已生成 | 通过：5 个 GitHub demo job，只改变压头速度，恢复 settle scale 1 |
| pscale=2 C 25 cm/s loading-rate 结果已导入 | review：trend 5/5、双门槛 3/5，但 CV 增加 33.52%；拒绝 25 cm/s |
| Zhang 接触模型和阻尼定义已审计 | 通过：带 PDF 页码、文件哈希和官方 LIGGGHTS 源码映射；禁止将阻尼 0.2 直接映射为恢复系数 |
| LIGGGHTS 求解器来源已固定 | 通过：workflow 与 cloud script 固定提交并输出 `solver_provenance.csv` |
| C sidewall-friction 成对矩阵已生成 | 通过：2 个 wall scales x 5 个相同 seeds，只改变 `mu_wall_scale`；尚待实算 |
| 是否继续 4x/8x 或 WSL2 有明确建议 | 通过：暂不进入 4x/8x，继续 pscale=2 分 size 校准 |
