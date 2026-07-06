# 04 COMSOL Electrothermal Field

## 阶段目的

用 COMSOL 作为电流场和温度场主线。DEM 提供颗粒位置、直接接触力和接触网络；
COMSOL 求解连续电势、电流密度、Joule heat 和温度场；开源有限体积求解器负责
守恒和跨求解器复核。

## 当前完成状态

单阶段均匀化电热 smoke model 已完成并通过九项门槛：

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
| 阶段判定 | `smoke_pass` |

## 代码入口

- `scripts/prepare_comsol_electrothermal_input.py`：验证直接接触来源、转换力单位、
  生成空间电导率和热导率网格。
- `comsol/Dia60Al40_ElectrothermalMVP.java`：COMSOL Electric Currents + Heat Transfer
  + Electromagnetic Heat Source builder。
- `scripts/solve_electrothermal_fvm.py`：开源有限体积平行求解器。
- `scripts/analyze_electrothermal_mvp.py`：COMSOL/FVM 场和能量交叉验证。
- `scripts/run_comsol_electrothermal_mvp.ps1`：Windows COMSOL 受控目录批处理入口。
- `.github/workflows/electrothermal-mvp-verification.yml`：不依赖 COMSOL 许可证的
  GitHub 轻量复核。

详细公式、边界条件和验收条件见 [model_spec.md](model_spec.md)。阶段结果见
[report.md](report.md)。

## 证据位置

```text
data/source/       # 最小 DEM 粒子、直接接触和模型参数输入
data/prepared/     # 属性网格、COMSOL 插值文件、哈希 manifest
evidence/comsol_smoke/  # MPH、原始 COMSOL CSV、图和 batch log
evidence/fvm_smoke/     # 开源 FVM 场、摘要和图
evidence/comparison/    # 九项验收、跨求解器报告和对比图
evidence/github_run_28793218330.md  # GitHub run、artifact digest 和证据边界
```

## 证据边界

当前 `smoke_pass` 证明真实 DEM 直接接触可以稳定映射到 COMSOL 电热连续场，且
独立开源离散化得到一致结果。它不证明以下内容：

- 颗粒分辨的 Al/diamond 几何与接触电阻；
- 电导率、热导率和接触半径已经由论文或实验标定；
- 网格独立性和电压/电流加载路径独立性；
- 多压制阶段热历史、扩散和烧结颈增长已经闭环。

## 下一门槛

阶段 04 下一步不是重复 smoke run，而是引入论文/材料来源的电热参数和接触电阻，
完成至少三档网格验证，再把粒子温度输出交给阶段 06 的 Liu 烧结模型。
