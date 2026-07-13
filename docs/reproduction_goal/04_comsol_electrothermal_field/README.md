# 04 COMSOL Electrothermal Field

## 阶段目的

用 COMSOL 作为电流场和温度场主线。DEM 提供颗粒位置、直接接触力和接触网络；
COMSOL 求解连续电势、电流密度、Joule heat 和温度场；开源有限体积求解器负责
守恒和跨求解器复核。

## 当前完成状态

单阶段均匀化电热 smoke model 已完成，并通过跨求解器和三档网格门槛：

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
| 阶段判定 | `smoke_pass + mesh_pass + contact_screened` |

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
evidence/github_run_28793218330.md  # GitHub run、artifact digest 和证据边界
evidence/github_run_29236808994.md  # 三档网格轻量复核 run 与 artifact digest
evidence/github_run_29240835995.md  # 材料接触敏感性轻量复核 run 与 artifact digest
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

## 下一门槛

三档网格和接触倍率筛查已经通过。阶段 04 下一步不是重复 smoke 或继续加密网格，
而是获得 Al 粉氧化膜/压制电阻标定，或建立能确认贯通性的三维接触网络；随后只在
已接受的 3316 单元网格上跑选定参数的 COMSOL 场，再把粒子温度输出交给阶段 06。
