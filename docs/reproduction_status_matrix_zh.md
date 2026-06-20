# 四篇论文复现状态矩阵

本文档把当前目标拆成可验收项：PDF 内容、论文算法复现、真实 DEM 轻量验证、开源算法路线、以及尚未完成的高保真升级。它不是最终结题报告，而是后续继续推进应力-接触-电流-温度-致密化耦合模拟的工作台账。

## 当前判定

- 当前阶段结论：四篇论文的算法层已经可重复生成，真实 LIGGGHTS DEM 轻量 demo 已在 GitHub Actions 跑通。
- 最新验证代码 commit：`a461664b80a0c5c7993554a761716ec49ffdc504`
- 论文算法 workflow：[paper-algorithm-reproduction run 27836537652](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27836537652)，状态 `success`
- 真实 DEM workflow：[dia60al40-dem run 27836537650](https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/27836537650)，状态 `success`
- DEM evidence：`87 pass / 0 missing / 0 mismatch`
- 真实 DEM artifact：`dia60al40-dem-artifacts-sizeC-Emax12-mu1.0-seed0`
- 最终轻量 demo 结果：`rho_total=0.95`，`p_target=297.8374 MPa`
- Zhang 力链校准扫描：27 组强接触阈值/最小链长组合均为 `review`；最佳组 `threshold_factor=0.05`、`min_chain_length=2`，D1 下降但 strong-force participation 下降
- Zhang ensemble 校准诊断：跨 artifact 汇总器会输出最佳候选、分组统计和下一轮轻量 sweep 建议；按接近目标趋势排序，当前 artifact 最佳为 `threshold_factor=1.25`、`min_chain_length=2`，诊断 `needs_participation_increase`
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
| 电流和温度场 | 已有接触电导、电流、Joule heat、粒子温度代理场 | `stage_details/*_electrothermal_contacts.csv`，`stage_details/*_electrothermal_particles.csv` | 建立真实热传导/边界散热场，替换 lumped temperature proxy |
| 致密化链条 | 已有压力-密度曲线、Heckel/Kawakita/Huang fit、neck-growth proxy | `pressure_density_curve.csv`，`series_compaction_fits.csv` | 加入材料扩散常数、活化能和烧结时间标定 |

## 分论文复现矩阵

| 论文 | PDF 中的核心机制 | 当前已复现内容 | 真实 DEM 状态 | 未完成高保真项 |
|---|---|---|---|---|
| Zhang：多尺度力学不均匀性 | 宏观压力、介观力链、微观接触力 Gini/participation、D1、D2，摩擦影响 | `zhang_multiscale_metrics.csv`、`zhang_friction_sensitivity.csv`、趋势 gate 全通过 | 真实 direct-force stage series 中压力、密度、coordination、D2 gate 通过；`zhang_force_chain_calibration` 扫描显示仅调强力阈值/最小链长仍为 `review` | 需要按论文 3000 粒子/600 MPa/力链图像校准接触律、摩擦参数、加载路径和 D1 单调趋势 |
| Yuan：拱桥结构 | DEM/MPFEM 压制，arch count、length、strength、buckling、direction，颗粒形状影响致密化 | `yuan_arch_bridge_metrics.csv`，圆/条形代理趋势和 arch gate 通过 | 真实 stage 输出 arch candidates、strength、direction angle、buckling angle | 当前 LIGGGHTS 用球形颗粒；需 clump/polygon/superquadric 或 MPFEM 才能严格复现圆/六边形/条形颗粒 |
| Liu：压制-烧结耦合 | Huang/Heckel/Kawakita 压实模型，压制微结构传给烧结，扩散 neck growth | `liu_compaction_curve.csv`、`liu_compaction_fits.csv`、`liu_electrothermal_sintering.csv` | 真实 stage 输出 force-current、force-Joule、particle heat-neck 正相关，Heckel/Kawakita fit 可用 | 当前温度是网络代理；需真实热传导场、扩散常数、活化能、烧结时间标定 |
| Li：包覆式复合粉末 | Cu@Fe 包覆粉、温度/摩擦/速度/长径比/颗粒数对致密化影响，PFC2D 到 MSC.MARC | `li_coated_powder_sweeps.csv`、`li_core_shell_metrics.csv`、温度压力、颗粒数收敛输出 | 真实 DEM stage schema 支持把压力、密度、接触和非均匀性传入 Li 代理模型 | 需要核心-包覆 MPFEM/FEM handoff，加入 Cu/Fe 界面摩擦、塑性和热膨胀 |

## 当前真实 DEM 证据

| 证据项 | 当前值 |
|---|---|
| workflow | `dia60al40-dem` run `27836537650` |
| verified code commit | `a461664b80a0c5c7993554a761716ec49ffdc504` |
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
| Zhang ensemble aggregator | `zhang_calibration_best_by_run.csv` and `zhang_calibration_group_summary.csv` rank future mu/E/seed/size sweeps; `zhang_next_sweep_recommendation.json` turns the current diagnosis into a small next workflow matrix; current target-oriented best is `threshold_factor=1.25`, `min_chain_length=2`, `needs_participation_increase` |

Zhang 的真实 DEM `review` 不是文件缺失或算法失败，而是科学上更诚实的状态：完整直接接触力已经进入计算链，但轻量 demo 的 force-chain participation 和 D1 还没有按 Zhang 原文的粒子数量、材料参数、压力终点和图像阈值校准。`scripts/calibrate_zhang_force_chain.py` 已把“只调强接触阈值和最小链长是否足够”变成可重复扫描；`scripts/aggregate_zhang_calibration.py` 进一步把多参数 DEM artifact 汇总成按摩擦、Al 模量、seed 和尺寸 case 分组的校准表，并输出下一轮 GitHub Actions 轻量 sweep 建议。当前真实 artifact 的答案是否定的，因此下一步应转向接触律、摩擦、加载路径和粒子规模校准。

## 下一阶段制作方法

1. 保持 GitHub Actions 为主运行环境，继续用 `runtime_profile=demo` 做快速回归。
2. 以 LIGGGHTS-PUBLIC 输出为统一数据源，稳定 `pressure_density_curve.csv`、`dem_fem_handoff_*.csv`、`contact_forces/*_contacts.csv` 和 `stage_details/*` 合同。
3. Zhang 优先做力链校准：强接触阈值、链长下限、角度阈值、摩擦参数和压力终点。
4. Yuan 优先做形状后端：先在开源 DEM 里实现 clump/superquadric/polygon，再和现有 arch metric 对接。
5. Liu 优先做热场：用接触 Joule heat 做源项，加入热传导边界，输出真实温度场。
6. Li 优先做 MPFEM/FEM handoff：保留 DEM 随机坐标与接触网络，新增 Cu@Fe core-shell 几何和材料参数。
7. 当参数迭代变频繁，再部署 WSL2/Ubuntu 22.04 本地环境；否则继续用 workflow 节省 Windows 依赖成本。

## 当前未宣称完成的内容

- 还没有一比一复现四篇论文的全部图表和实验数值。
- 还没有 Zhang 论文级 3000 粒子 DEM 与 572-638 MPa endpoint 校准。
- 还没有 Yuan 的真实非球形/MPFEM 颗粒形状模型。
- 还没有 Liu 的全热传导温度场和材料扩散参数标定。
- 还没有 Li 的真实 Cu@Fe core-shell MPFEM 变形模型。

因此当前目标仍应保持 active：已经完成的是“可运行的四论文算法复现层 + 真实 DEM 轻量验证层”，下一步是把代理/轻量 demo 逐项升级成论文级物理模型。
