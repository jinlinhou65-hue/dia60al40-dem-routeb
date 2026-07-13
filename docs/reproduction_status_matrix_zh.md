# 四篇论文复现状态矩阵

本文档把当前目标拆成可验收项：PDF 内容、论文算法复现、真实 DEM 轻量验证、开源算法路线、以及尚未完成的高保真升级。它不是最终结题报告，而是后续继续推进应力-接触-电流-温度-致密化耦合模拟的工作台账。

阶段化总目标、文件夹索引、验收纪律和后续归档规则见
`docs/reproduction_goal/README.md`。后续每个阶段完成后的数据、图、报告和
workflow 证据应放入对应阶段文件夹，避免证据散落。

## 当前判定

- 当前阶段结论：四篇论文的算法层已经可重复生成，真实 LIGGGHTS DEM 轻量 demo 已在 GitHub Actions 跑通。
- 最新导入证据目录：`docs/reproduction_goal/03_zhang_particle_scale/evidence/pscale2_c_loading_rate_recheck_run_28729754426/`
- 论文算法 workflow：[paper-algorithm-reproduction run 27866974626](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27866974626)，状态 `success`
- Zhang 推荐 sweep 调度器：[zhang-recommended-sweep run 27866837375](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27866837375)，状态 `success`
- Zhang 推荐 6-job DEM sweep：[dia60al40-dem run 27866838829](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27866838829)，状态 `success`
- Zhang 9-job 稳健性 DEM sweep：[dia60al40-dem run 27867380830](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27867380830)，状态 `success`
- Zhang 尺寸分组调度器：[zhang-size-specific-sweep run 27874057448](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874057448)，状态 `success`
- Zhang 尺寸分组 DEM sweep：C [run 27874059503](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874059503)、D [run 27874061902](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874061902)、E [run 27874064063](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874064063)，均为 `success`，合计 36 个轻量 DEM job
- Zhang 尺寸分组证据导入：[zhang-size-specific-artifact-report run 27874391838](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27874391838)，状态 `success`，自动提交 `a8d4319`
- Zhang 粒子数升级路径：`particle_count_scale=2` 的 C/D/E 三条 GitHub demo 均已跑通并导入 `docs/reproduction_goal/03_zhang_particle_scale/`。D 的初始失败被定位为 verifier 硬编码 `radius>24 um` 误判；修复为按渲染 DS/DL 半径分类后，D run `27875951506` 成功并产出完整 artifact。2x 判读结果为 `review`：C/D/E 的 P95 分别为 `411.866/413.405/371.868 MPa`，均低于 Zhang `572-638 MPa` endpoint window。
- Zhang pscale=2 follow-up：C/D/E follow-up 已运行并导入。C 已得到 `Emax=63.462 GPa, mu=0.654, P95=586.646 MPa` 的 pressure pass + trend pass 候选；D 仍为 trend review；E 仍低于压力窗口。
- Zhang C seed recheck：C-only 5-job 已在 GitHub Actions 成功运行并导入，固定 `Emax=63.462 GPa, mu=0.654, particle_count_scale=2`，只扫 seeds `0..4`。结果为 `review`：只有 1/5 seed 同时满足压力窗口和 trend gate。
- Zhang C pressure-lift recheck：固定 `mu=0.654, particle_count_scale=2` 和 seeds `0..4`，只把 Emax 从 `63.462` 提高到 `72.581 GPa`。5 个 DEM job 和 ensemble 均成功；平均 P95 从 `524.619` 提高到 `574.211 MPa`，CV 从 `0.0804` 降到 `0.0396`，但仍只有 2/5 seed 同时满足压力窗口和 trend gate。
- Zhang C 4x-settle recheck：固定 Emax/mu/速度/时间步/粒子尺度/seeds，只把 demo settle steps 从 `20k/20k/50k` 提高到 `80k/80k/200k`。有效 run `28710536524` 的 5 个 DEM job 与 ensemble 均成功，运行参数已进入 artifact；trend 从 4/5 提高到 5/5，但压力 CV 增加 130.22%，双门槛覆盖从 2/5 降到 1/5，因此拒绝 settle scale 4。
- Zhang C settle=2 midpoint：dispatcher `28729401297` 调度有效 DEM run `28729403153`，5 个 seed job 与 ensemble 均成功；artifact digest 已本地复核。`40k/40k/100k` 使 trend 达到 5/5，但平均 P95 降为 `563.323 MPa`、CV 升为 `0.1268`、压力窗口与双门槛覆盖均为 0/5，因此拒绝 scale 2，并停止 dwell 分支。
- Zhang C 25 cm/s loading-rate recheck：dispatcher `28729752015` 调度有效 DEM run `28729754426`，5 个 seed job 与 ensemble 均成功，artifact digest 已本地复核。平均 P95 为 `578.432 MPa`、trend 5/5、双门槛 3/5，但 CV 从 `0.0396` 升到 `0.0528`，增加 33.52%，因此拒绝 25 cm/s 并恢复 50 cm/s。
- Zhang 接触参数审计：用户提供的文件是 2024 年 10 页期刊论文，不是 2019 年学位论文全文。PDF p.3 的法/切向阻尼系数 `0.2` 缺少方程和单位，不能直接映射为 LIGGGHTS `coefficientRestitution`。当前全局 `mu_scale` 还混合了粒间和粒壁机制，因此已新增 sidewall-only scale、固定 LIGGGHTS 提交 `3d5c00f...e649d`，并完成 `wall scale=1/0.019113 x seeds 0..4` 的 10-job 成对试验。
- Zhang C sidewall-friction recheck：dispatcher `28747844572` 调度 child run `28747847286`，10 个 DEM job 与 ensemble 全部成功；artifact `8093807720` 的 SHA-256 已本地复核。`mu_w=0.001` 使均值从 `574.211` 降到 `565.114 MPa`、CV 从 `0.0396` 升到 `0.0561`、双门槛从 2/5 降到 1/5，因此拒绝低侧壁摩擦并恢复 wall scale 1。
- Zhang C particle-friction plan：复用 run `28747847286` 的 wall-scale 1 五种子基线，只新增 5 个相同 seed 的 `mu_p=0.001` test jobs；粒壁、粒压头、求解器、Emax、速度、时间步和 dwell 全部冻结。
- Zhang C particle-friction recheck：dispatcher `28789102529` 调度 child run `28789107809`，5 个 DEM job 与 ensemble 全部成功；artifact `8108026788` 的 SHA-256 已本地复核。`mu_p=0.001` 使平均 P95 降至 `409.996 MPa`、CV 升至 `0.0463`、压力窗口和双门槛均为 0/5，因此拒绝并停止 C 低摩擦分支。
- Zhang E pressure-lift plan：由 seed-2 趋势候选 `87.368 GPa / 543.689 MPa` 按 600 MPa 一阶比例得到唯一 Emax=`96.417 GPa`；预注册 5 个 seeds，只改变 Emax 并固定其余物理量和求解器。
- Zhang E pressure-lift recheck：dispatcher `28790007125` 调度 child run `28790012884`，5 个 DEM job 与 ensemble 全部成功；artifact `8108372828` 的 SHA-256 已本地复核。结果 trend 4/5、双门槛 3/5、seed-2 升至 626.608 MPa，但均值 644.331 MPa 超上限，故停止 Emax-only 分支。
- DEM evidence：`87 pass / 0 missing / 0 mismatch`
- 真实 DEM artifact：`dia60al40-dem-artifacts-sizeC-Emax12-mu1.0-seed0`
- 最终轻量 demo 结果：`rho_total=0.95`，`p_target=297.8374 MPa`
- Zhang 力链校准扫描：27 组强接触阈值/最小链长组合均为 `review`；最佳组 `threshold_factor=0.05`、`min_chain_length=2`，D1 下降但 strong-force participation 下降
- Zhang ensemble 校准诊断：第二轮推荐矩阵 `Emax=[36.261,41.686]`、`mu=[0.63,0.7,0.77]` 已在 GitHub Actions 以 6 个 DEM job 跑通并导入到 `docs/zhang_sweep_evidence/run_27866838829/`；其中 `Emax=41.686`、`mu=0.77` 的 P95 为 `632.842 MPa`，进入 Zhang 572-638 MPa 端点窗口且力链趋势为 `pass`
- Zhang 稳健性诊断：`Emax=41.686`、`mu=0.77` 的 seeds `0,1,2` 和 size cases `C,D,E` 已在 GitHub Actions 以 9 个 DEM job 跑通并导入到 `docs/zhang_sweep_evidence/run_27867380830/`；workflow 可行，但全局参数不稳健：5/9 为 Zhang trend `pass`，只有 2/9 同时 `pass` 且落入 572-638 MPa 窗口。
- Zhang 尺寸分组校准：三段 size-specific sweep 已跑完并导入合并证据，36/36 行有 best-row 记录，15/36 通过 Zhang trend gate，15/36 落入 572-638 MPa 窗口，5/36 同时 `pass` 且落入压力窗口；当前候选为 C `Emax=44.772 GPa, mu=0.654, seed=2, P95=634.203 MPa`，D `Emax=37.517 GPa, mu=0.77, seed=2, P95=620.578 MPa`，E `Emax=37.517 GPa, mu=0.693, seed=2, P95=604.217 MPa`。
- 运行环境策略：现阶段优先 GitHub Actions/Ubuntu；WSL2 在 workflow 稳定后用于本地长时间调参，而不是当前必要前置条件。

## 用户目标拆解

| 目标项 | 当前状态 | 证据 | 下一步 |
|---|---|---|---|
| 分析四篇 PDF | 已建立 PDF 页码锚点和方法映射 | `docs/paper_pdf_reproduction_map.md` | 如需写论文式综述，再把页码锚点扩成逐节中文摘录 |
| 每篇论文先复现出来 | 算法层已复现并通过内容检查 | `outputs/paper_direct_liggghts_contact_check/**`，`paper-algorithm-reproduction` workflow | 用真实 DEM/MPFEM/热场逐步替换代理模型 |
| 找合适开源 DEM 算法 | 已选择 LIGGGHTS-PUBLIC 为当前 backend，并列出 LAMMPS/YADE/MercuryDPM/Chrono 备选 | `docs/dem_algorithm_selection.md` | Yuan 形状升级时优先评估 LAMMPS superquadric/cluster 或 Chrono DEME |
| 应力分布模拟 | 已从 DEM contact force 计算 virial stress 和 fabric tensor | `series_network_metrics.csv`，`dem_evidence_report.md` | 校准 Zhang 局部应力 D2 与论文测量圆方法 |
| 颗粒接触状态 | 已导出 LIGGGHTS `pair/gran/local` 直接接触力并转换为 stage contact CSV | `liggghts/DEM/contact_forces/*_contacts.csv` | 继续校准强接触阈值、力链角度和最小链长 |
| 拱桥结构形成 | 已有强接触连通图 arch candidate、强度、方向、buckling 输出 | `stage_details/*_arches.csv`，`yuan/yuan_arch_bridge_metrics.csv` | 增加非球形颗粒或 MPFEM，复现 Yuan 的圆/六边形/条形差异 |
| 电流和温度场 | 恒压/恒流与 GitHub 重放已验证；z schema 已补齐，现有 deck 被审计为严格准二维 | `04_comsol_electrothermal_field/three_dimensional_readiness_audit.md` | 按预注册实现独立轻量真三维 DEM 贯通 pilot，再决定氧化膜标定 |
| 致密化链条 | 已有压力-密度曲线、Heckel/Kawakita/Huang fit、neck-growth proxy | `pressure_density_curve.csv`，`series_compaction_fits.csv` | 加入材料扩散常数、活化能和烧结时间标定 |

## 分论文复现矩阵

| 论文 | PDF 中的核心机制 | 当前已复现内容 | 真实 DEM 状态 | 未完成高保真项 |
|---|---|---|---|---|
| Zhang：多尺度力学不均匀性 | 宏观压力、介观力链、微观接触力 Gini/participation、D1、D2，摩擦影响 | `zhang_multiscale_metrics.csv`、`zhang_friction_sensitivity.csv`、趋势 gate 全通过 | 真实 direct-force stage series 中压力、密度、coordination、D2 gate 通过；尺寸分组轻量 sweep 已得到 C/D/E 各自的 pass+pressure-window 候选 | 需要按论文 3000 粒子/600 MPa/力链图像校准接触律、摩擦参数、加载路径和 D1 单调趋势 |
| Yuan：拱桥结构 | DEM/MPFEM 压制，arch count、length、strength、buckling、direction，颗粒形状影响致密化 | `yuan_arch_bridge_metrics.csv`，圆/条形代理趋势和 arch gate 通过 | 真实 stage 输出 arch candidates、strength、direction angle、buckling angle | 当前 LIGGGHTS 用球形颗粒；需 clump/polygon/superquadric 或 MPFEM 才能严格复现圆/六边形/条形颗粒 |
| Liu：压制-烧结耦合 | Huang/Heckel/Kawakita 压实模型，压制微结构传给烧结，扩散 neck growth | `liu_compaction_curve.csv`、`liu_compaction_fits.csv`、`liu_electrothermal_sintering.csv` | 真实 stage 输出 force-current、force-Joule、particle heat-neck 正相关，Heckel/Kawakita fit 可用 | 当前温度是网络代理；需真实热传导场、扩散常数、活化能、烧结时间标定 |
| Li：包覆式复合粉末 | Cu@Fe 包覆粉、温度/摩擦/速度/长径比/颗粒数对致密化影响，PFC2D 到 MSC.MARC | `li_coated_powder_sweeps.csv`、`li_core_shell_metrics.csv`、温度压力、颗粒数收敛输出 | 真实 DEM stage schema 支持把压力、密度、接触和非均匀性传入 Li 代理模型 | 需要核心-包覆 MPFEM/FEM handoff，加入 Cu/Fe 界面摩擦、塑性和热膨胀 |

## 当前真实 DEM 证据

| 证据项 | 当前值 |
|---|---|
| workflow | `dia60al40-dem` run `27866838829` |
| verified code commit | `093331250ea5c01158f91e4f050161142d499ea1` |
| DEM backend | LIGGGHTS-PUBLIC serial build on `ubuntu-22.04` |
| stage count | 6 stages: preload, rho065, rho072, rho080, rho088, rho095 |
| particle count gate | 76 particles in each handoff stage |
| direct contact source | `contact_source=direct` in final stage metrics |
| direct contact completeness | `direct_contact_force_fraction=1.0` |
| final density | `0.95` |
| final pressure | `297.8374 MPa` |
| DEM evidence | `87 pass / 0 missing / 0 mismatch` |
| paper acceptance on real DEM | Li pass, Liu pass, Yuan pass, Zhang review with 0 mismatch |
| Zhang force-chain calibration | 27 threshold/chain-length candidates scanned; best `threshold_factor=0.05`, `min_chain_length=2`, `chain_coverage=1.0`, D1 decreases but strong-force participation decreases, so status remains `review` |
| Zhang recommended sweep | dispatcher run `27866837375` triggered DEM run `27866838829`; all 6 matrix jobs plus aggregate ensemble job completed `success` |
| Zhang robustness sweep | dispatcher run `27867379295` triggered DEM run `27867380830`; all 9 matrix jobs plus aggregate ensemble job completed `success` |
| Zhang size-specific sweep | dispatcher run `27874057448` triggered C/D/E DEM runs `27874059503`, `27874061902`, and `27874064063`; all three 12-job matrices and their aggregate ensemble jobs completed `success` |
| Zhang size-specific artifact import | report run `27874391838` completed `success` and auto-committed `a8d4319` with C/D/E run directories plus `docs/zhang_sweep_evidence/size_specific_27874059503_27874061902_27874064063/summary.json` |
| Zhang sweep imported evidence | `docs/zhang_sweep_evidence/run_27867380830/README.md` summarizes the 9-job ensemble; P95 range is `510.770-787.592 MPa`, mean `669.490 MPa`; 5/9 candidates pass Zhang force-chain trend gates |
| Zhang size-specific aggregator | The combined 36-row summary shows 15 trend-pass rows, 15 pressure-window rows, and 5 rows that satisfy both. Best current candidates are C `44.772/0.654/seed2/P95=634.203 MPa`, D `37.517/0.77/seed2/P95=620.578 MPa`, and E `37.517/0.693/seed2/P95=604.217 MPa`. |
| Zhang particle-count scale pilot | `zhang-scale-pilot.yml` run `27875947935` dispatched the fixed 2x C/D/E candidates. C run `27875950305`, D run `27875951506`, and E run `27875952754` all completed `success` with full DEM artifacts and ensemble summaries. The imported stage report in `docs/reproduction_goal/03_zhang_particle_scale/report.md` shows P95 drops by `33-38%`, so 2x is runnable but needs recalibration before 4x/8x. |
| Zhang pscale=2 pressure recalibration | `zhang-pscale2-recalibration.yml` run `27882364909` dispatched DEM runs `27882367107`, `27882368312`, and `27882369414`; all three completed `success` and were imported. The report `docs/reproduction_goal/03_zhang_particle_scale/pscale2_recalibration_report.md` shows C best `567.207 MPa/pass`, D best `634.795 MPa/review`, E best `480.140 MPa/review`; therefore continue pscale=2 size-specific calibration before 4x. |
| Zhang pscale=2 follow-up plan | `scripts/dispatch_zhang_pscale2_followup.py` and `zhang-pscale2-followup.yml` define the next 10-job GitHub demo matrix. C runs four narrow Emax candidates around the local 61.962 GPa best, D holds `Emax=57.173 GPa` and sweeps `mu=0.77/0.847/0.963`, and E extends Emax to `75.454/79.426/87.368 GPa`. Plan artifact: `docs/reproduction_goal/03_zhang_particle_scale/data/pscale2_followup_plan.json`. |
| Zhang pscale=2 follow-up results | `zhang-pscale2-followup.yml` run `27883030240` dispatched C run `27883033303`, D run `27883034434`, and E run `27883035658`; all completed `success` and were imported. The report `docs/reproduction_goal/03_zhang_particle_scale/pscale2_followup_report.md` shows C best `586.646 MPa/pass`, D best `634.795 MPa/review`, E best `543.689 MPa/pass`. C is ready for seed recheck; D/E are not ready for 4x. |
| Zhang C seed recheck results | `zhang-pscale2-c-seed-recheck.yml` run `27898768547` dispatched `dia60al40-dem.yml` run `27898770533`; all five C seed jobs and aggregate ensemble completed `success`. The report `docs/reproduction_goal/03_zhang_particle_scale/pscale2_c_seed_recheck_report.md` shows C is not seed-robust: 4/5 trend pass, 1/5 pressure-window pass, and 1/5 pass both. |
| Zhang C pressure-lift results | `zhang-pscale2-c-pressure-lift-recheck.yml` run `28709922833` dispatched `dia60al40-dem.yml` run `28709925303`; all five jobs and aggregate ensemble completed `success`. The paired report shows Emax +14.37% produced mean P95 +9.45%, reduced CV by 50.80%, and improved pass+window coverage from 1/5 to 2/5, so C remains review. |
| Zhang C 4x-settle results | First child run `28710435532` failed before DEM because of a heredoc indentation bug and is excluded. After fix `e2eb4ea`, dispatcher `28710534299` triggered valid child `28710536524`; all five DEM jobs and ensemble succeeded. The paired report shows all trend gates pass, but mean P95 falls to `567.232 MPa`, CV rises to `0.0911`, and pass+window coverage falls to 1/5. |
| Zhang C settle midpoint results | `zhang-pscale2-c-settle-midpoint.yml` run `28729401297` triggered valid child `28729403153`; all five DEM jobs and ensemble succeeded. Settle scale 2 gives 5/5 trend pass but mean P95 `563.323 MPa`, CV `0.1268`, and 0/5 pressure-window or combined passes, so it is rejected. |
| Zhang C loading-rate results | `zhang-pscale2-c-loading-rate-recheck.yml` run `28729752015` triggered valid child `28729754426`; all five DEM jobs and ensemble succeeded. Reducing velocity to 25 cm/s improves trend to 5/5 and combined coverage to 3/5, but raises CV by 33.52%, so it is rejected under the pre-registered gate. |
| Zhang contact-model audit and next plan | The supplied PDF is the 2024 journal article, not the full 2019 thesis. Damping `0.2` has no reported equation/units and is not mapped to restitution. LIGGGHTS is now pinned to `3d5c00f...e649d`; the next registered workflow pairs wall scale `1/0.019113` over seeds `0..4` while holding all other C controls fixed. |
| Zhang C sidewall-friction results | `zhang-pscale2-c-wall-friction-recheck.yml` dispatcher `28747844572` triggered child `28747847286`; all ten paired jobs and ensemble succeeded. The verified artifact shows low wall friction lowers mean P95 by `9.097 MPa`, raises CV by `41.71%`, and reduces combined coverage to 1/5, so `mu_w=0.001` is rejected. |
| Zhang C particle-friction plan | `pscale2_c_particle_friction_plan.json` preregisters effective `mu_p=0.001` for all particle pairs and reuses the verified five-seed baseline, reducing the new run count from ten to five without weakening the paired comparison. |
| Zhang C particle-friction results | Dispatcher `28789102529` triggered child `28789107809`; all five test jobs and ensemble succeeded. The verified artifact shows mean P95 `409.996 MPa`, CV `0.0463`, trend 3/5, and combined coverage 0/5, so `mu_p=0.001` is rejected. |
| Zhang E pressure-lift plan | `pscale2_e_pressure_lift_plan.json` preregisters one five-seed Emax test at `96.417 GPa`, with `mu=0.693`, size E, pscale 2, loading path, contact pairs and solver provenance held fixed. |
| Zhang E pressure-lift results | Dispatcher `28790007125` triggered child `28790012884`; all five jobs and ensemble succeeded. Trend and combined gates pass at 4/5 and 3/5, but mean P95 is `644.331 MPa`; a proportional per-seed screen has no common Emax interval, so no further Emax-only sweep is scheduled. |
| Zhang particle-scale feasibility diagnostic | `scripts/diagnose_particle_scale_feasibility.py` writes `outputs/zhang_particle_scale_feasibility.csv`. It shows D pscale=2 has 70 Al + 22 large-diamond particles, final DEM disk packing fraction `1.013`, insert-region disk packing `0.474`, and largest-diameter/final-height ratio `0.346`; these remain useful risk indicators for later 4x/8x scaling, but 2x no longer fails the DEM evidence gate after the verifier fix. |

Zhang 的真实 DEM `review` 不是文件缺失或算法失败，而是科学上更诚实的状态：完整直接接触力已经进入计算链，但轻量 demo 的粒子数、接触律和加载路径仍低于论文级。第二轮 6-job sweep 找到了 `Emax=41.686`、`mu=0.77` 这一可行候选；随后 9-job 稳健性 sweep 证明 workflow 可稳定运行，但一个全局 mu/E 参数不能同时覆盖 C/D/E 粒径 case 和三个随机 seed。最新 36-job 尺寸分组 sweep 进一步证明 C/D/E 需要不同的 endpoint modulus/friction bracket，并给出了下一轮高保真 Zhang DEM 的三个起始参数。

## 下一阶段制作方法

1. 保持 GitHub Actions 为主运行环境，继续用 `runtime_profile=demo` 做快速回归。
2. 以 LIGGGHTS-PUBLIC 输出为统一数据源，稳定 `pressure_density_curve.csv`、`dem_fem_handoff_*.csv`、`contact_forces/*_contacts.csv` 和 `stage_details/*` 合同。
3. Zhang 轻量 pscale=2 路线已完成当前可解释的单变量筛查：C 低侧壁/低粒间摩擦被否决，E pressure-lift 达到部分覆盖但无共同 Emax 窗口。阶段保持 `review`，禁止无依据映射阻尼 `0.2`，也不启动 4x/8x。
4. Yuan 优先做形状后端：先在开源 DEM 里实现 clump/superquadric/polygon，再和现有 arch metric 对接。
5. COMSOL smoke、三档网格、材料接触筛查及六组恒压/恒流固定网格计算已完成。恒压下电阻升高使功率下降，恒流下使功率上升；原六组比较因倍率 1 的 5.0737% 差异保留 review，预注册 FVM 加密将差异降至 0.6823% 并通过。GitHub run `29244185796` 已无许可证重放成功。下一步优先恢复 z 坐标并验证三维直接接触贯通，不重复 COMSOL 网格和六组计算。
6. Liu 尚不能直接使用未标定绝对温升；Stage 04 物理可信度门槛通过后，再接入烧结颈增长、扩散和致密化指标。
7. Li 优先做 MPFEM/FEM handoff：保留 DEM 随机坐标与接触网络，新增 Cu@Fe core-shell 几何和材料参数。
8. COMSOL 继续使用 Windows 本地许可证；GitHub workflow 运行开源 FVM 和证据复核。DEM 参数迭代变频繁时再部署 WSL2。

## 当前未宣称完成的内容

- 还没有一比一复现四篇论文的全部图表和实验数值。
- 还没有 Zhang 论文级 3000 粒子 DEM；轻量 demo 已找到 C/D/E 尺寸分组的 572-638 MPa endpoint 候选，但这些仍是低粒子数、简化接触律和简化加载路径下的起始参数。
- 还没有 Yuan 的真实非球形/MPFEM 颗粒形状模型。
- Liu 已有单阶段均匀化 COMSOL 温度场、网格验证、材料接触筛查和恒压/恒流机制证据，但尚无 Al 氧化膜标定、三维贯通接触和扩散/烧结闭环。
- 还没有 Li 的真实 Cu@Fe core-shell MPFEM 变形模型。

因此当前目标仍应保持 active：已经完成的是“可运行的四论文算法复现层 + 真实 DEM 轻量验证层”，下一步是把代理/轻量 demo 逐项升级成论文级物理模型。
