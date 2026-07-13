# 04 COMSOL Electrothermal Field

## 阶段目的

用 COMSOL 作为电流场和温度场主线。DEM 提供颗粒位置、直接接触力和接触网络；
COMSOL 求解连续电势、电流密度、Joule heat 和温度场；开源有限体积求解器负责
守恒和跨求解器复核。

## 当前完成状态

单阶段均匀化电热 smoke、跨求解器、三档网格、材料感知接触筛查、恒压/恒流机制
验证和真三维直接接触贯通 pilot 均已完成。Al 原生氧化膜来源矩阵、三模型方程、
参数网格和离线网络验收门槛也已在计算前冻结。恒压/恒流结果保留“原比较 review、
加密诊断 pass”两层判定；三维结果保留“贯通 smoke pass、氧化膜预注册 review”：

| 项目 | 结果 |
|---|---:|
| DEM stage | `stage5_rho095` |
| 颗粒数 | 76 |
| LIGGGHTS 直接接触数 | 157 |
| COMSOL 网格 | 3316 个三角形单元 |
| COMSOL 自由度 | 13570 + 308 internal DOF |
| COMSOL 最大温升 | 0.639814 K |
| 开源 FVM 最大温升 | 0.636193 K |
| Joule 功率相对差 | 1.202% |
| 电势场归一化 RMSE | 0.293% |
| 温度场归一化 RMSE | 0.765% |
| GitHub verifier | run `28793218330`, success, 27 s |
| COMSOL 网格 | `1512 / 3316 / 8390` 个三角形单元 |
| 中/细网格 Joule 功率差 | `0.0277%` |
| 中/细网格最大温升差 | `0.0187%` |
| GitHub mesh verifier | run `29236808994`, success, 29 s |
| GitHub contact verifier | run `29240835995`, success, 41 s |
| 恒压/恒流 COMSOL | 6 组，均为固定 3316 单元网格 |
| 原六组 COMSOL/FVM 判定 | `review`，倍率 1 功率/电流差 `5.0737% > 5%` |
| 预注册 FVM 加密判定 | `fvm_refinement_pass` |
| 3x FVM/COMSOL 功率差 | `0.6823%` |
| 3x FVM/COMSOL温升差 | `0.4508%` |
| Joule 热 top-1% 质心距离 | `6.156 um < 24 um` |
| 真三维 DEM | 96 颗粒，115 条直接接触，z span `66.1922 um` |
| 真三维活跃网络 | 50 条 Al-Al 边；三档阈值均贯通 |
| 最短贯通路径 | 5 个 Al 颗粒，clean-contact `0.0353279646 ohm` |
| GitHub 3D pilot | run `29246532552`, success, 140 s |
| 氧化膜预注册 | `5/6/8 nm`、`1e6/1e9/1e12 ohm m`、8 档金属微桥比例 |
| 阶段判定 | `oxide_model_preregistered_review`，离线网络计算和实验标定仍未完成 |

## 代码入口

- `scripts/prepare_comsol_electrothermal_input.py`：验证直接接触来源、转换力单位、
  生成空间电导率和热导率网格。
- `comsol/Dia60Al40_ElectrothermalMVP.java`：COMSOL Electric Currents + Heat Transfer
  + Electromagnetic Heat Source builder。
- `scripts/solve_electrothermal_fvm.py`：开源有限体积平行求解器。
- `scripts/analyze_electrothermal_mvp.py`：COMSOL/FVM 场和能量交叉验证。
- `scripts/run_comsol_electrothermal_mvp.ps1`：Windows COMSOL 受控目录批处理入口。
- `scripts/run_comsol_electrothermal_mesh_study.ps1`：三档 COMSOL 网格研究入口。
- `scripts/analyze_comsol_mesh_convergence.py`：解析 COMSOL 日志并执行收敛门槛。
- `.github/workflows/electrothermal-mvp-verification.yml`：不依赖 COMSOL 许可证的
  GitHub 轻量复核。
- `scripts/electrothermal_contact_model.py`：Hertz 接触半径、Holm 电收缩电阻、
  热收缩/界面热阻和电网络贯通性。
- `scripts/run_electrothermal_contact_sensitivity.py`：冻结归一化下的 `1/10/100`
  Al-Al 接触电阻倍率重跑、热点和趋势判定。
- `scripts/run_electrothermal_loading_sensitivity.py`：在同一属性场上生成恒压和恒流
  六组开源算例，并固定恒流目标与 COMSOL 运行计划。
- `scripts/analyze_electrothermal_loading_comsol.py`：比较六组归档 COMSOL 与 FVM，
  保留原 5% 门槛和 `review` 判定。
- `scripts/analyze_electrothermal_fvm_refinement.py`：只对失败的倍率 1 恒压 case 做
  预注册 1x/2x/3x 开源网格诊断，不重跑 COMSOL。
- `scripts/build_electrothermal_loading_manifest.py`：验证 116 个输入、实现、模型、
  日志和结果文件的大小、SHA-256、结构与三层判定。
- `python/render_dem_3d_pilot.py` 与 `liggghts/in.dia60al40_dem_3d_pilot.template.liggghts`：
  生成独立真三维球形颗粒轻量算例，不改动准二维基线。
- `scripts/analyze_dem_3d_percolation.py`：只接收 `pair/gran/local` 直接接触，执行 z、
  数量守恒、电极、三档阈值、最短电阻路径和瓶颈 gate。
- `.github/workflows/dem-3d-percolation-pilot.yml`：固定 10 分钟预算的无许可证真三维
  GitHub 运行入口。
- `al_oxide_contact_preregistration.md`：冻结 clean、完整氧化膜、部分破膜三个模型，
  输入哈希、参数网格、网络边界、验收门槛和停止条件。
- `data/source/al_oxide_contact_parameter_sources.csv`：区分粉末实测、方法来源、器件
  边界、数值辨识扫描和待实验标定参数。
- `data/source/al_oxide_contact_preregistered_parameters.json`：供下一步离线网络脚本直接
  读取的机器可读参数合同。

详细公式、边界条件和验收条件见 [model_spec.md](model_spec.md)。阶段结果见
[report.md](report.md)。

## 证据位置

```text
data/source/       # 最小 DEM 粒子、直接接触和模型参数输入
data/prepared/     # 属性网格、COMSOL 插值文件、哈希 manifest
evidence/comsol_smoke/  # MPH、原始 COMSOL CSV、图和 batch log
evidence/fvm_smoke/     # 开源 FVM 场、摘要和图
evidence/comparison/    # 九项验收、跨求解器报告和对比图
evidence/mesh_convergence/  # 三档网格场、日志、摘要和收敛图
evidence/contact_sensitivity/  # 接触物理表、网络图、三档 FVM 场和敏感性判定
evidence/loading_mode_sensitivity/  # 六组 COMSOL/FVM、原 review、加密 pass、失败证据和 manifest
evidence/true_3d_percolation/  # 首次失败、接受 run、原始接触、3D 网络图和哈希 manifest
evidence/github_run_28793218330.md  # GitHub run、artifact digest 和证据边界
evidence/github_run_29236808994.md  # 三档网格轻量复核 run 与 artifact digest
evidence/github_run_29240835995.md  # 材料接触敏感性轻量复核 run 与 artifact digest
evidence/github_run_29248571646.md  # Al 氧化膜预注册 Linux 测试与两个 artifact digest
```

## 证据边界

当前 `smoke_pass` 证明真实 DEM 直接接触可以稳定映射到 COMSOL 电热连续场，且
独立开源离散化得到一致结果。它不证明以下内容：

- 颗粒分辨的 Al/diamond 几何与接触电阻；
- 电导率、热导率和接触半径已经由论文或实验标定；
- 电压/电流加载路径独立性；
- 多压制阶段热历史、扩散和烧结颈增长已经闭环。

材料感知筛查进一步证明：157 条接触中有 `63 Al-Al / 80 Al-diamond /
14 diamond-diamond`；按未掺杂 diamond 电阻率和相对导纳阈值筛选后，只有 63 条
Al-Al 边活跃，当前二维截面不形成上下电极贯通路径。`130/157` 个接触还超过
Hertz 小变形警戒线。因此三档 FVM 的趋势是条件性响应，不是实际电阻烧结温升预测。

恒压/恒流研究进一步证明，电源控制方式会改变接触电阻对发热的方向：固定 `0.1 V`
时倍率 `1/10/100` 的 FVM 功率为 `209.770/32.511/7.818 W/m`，随电阻上升而下降；
固定约 `325.107 A/m` 时对应功率为 `5.039/32.511/135.200 W/m`，随电阻上升而
上升。COMSOL 得到相同方向。该结果是项目机制扩展；刘畅 PDF 没有给出复现模型的
电压或电流边界，不能把该边界写成论文原设定。

原六组比较仍为 `review`，因为倍率 1 的恒压与恒流 case 都有 `5.0737%` 的
COMSOL/FVM 功率和电流差，略超预注册 5% 门槛。后续预注册的 FVM 网格加密把同一
恒压倍率 1 case 的功率差降至 `0.6823%`、温升差降至 `0.4508%`，并使 top-1%
Joule 热质心距离达到 `6.156 um`，说明原超限来自粗开源网格离散误差；该诊断不
覆盖原判定。完整哈希证据见 `evidence/loading_mode_sensitivity/evidence_manifest.json`。

独立真三维 pilot 进一步证明：96 个颗粒和 115 条 LIGGGHTS 直接接触在非零厚度中
保持完整，颗粒与接触点 z span 分别为 `66.1922/65.4849 um`。三档预注册导纳阈值
均保留 50 条 Al-Al 活跃边，并得到同一条 `95→41→36→27→33` 五颗粒贯通路径。
clean-contact Hertz/Holm 路径电阻为 `0.0353279646 ohm`。该值没有包含 Al 氧化膜，
仅证明网络拓扑和分析链可用，不是实验电阻。

首次 run `29246371198` 因中心安全插入区与 `all_in yes` 二次缩小而在动力学前失败；
只把三条插入命令改为 `all_in no` 后，run `29246532552` 在 140 秒内成功。失败日志、
接受结果、artifact digest 和 27 个归档文件哈希均保存在
`evidence/true_3d_percolation/`。

可视化入口：[真三维材料-电极-直接接触-最短路径网络图](figures/true_3d_percolation_network.png)。

## 下一门槛

Al 氧化膜模型已预注册。唯一下一门槛是只读取归档图和机器参数合同，对 50 条 Al-Al
边求完整 KCL 电阻网络，输出 clean、完整膜和部分破膜场景的等效电阻、最短路径、
逐边电流/Joule 功率、top-5 热点、单调性和电源功率守恒。本门槛不重跑 DEM、
COMSOL 网格或六组恒压/恒流。没有压片电阻实验前，结果最高只能是
`bounded_oxide_network_sensitivity_pass`，不能称为氧化膜标定。
