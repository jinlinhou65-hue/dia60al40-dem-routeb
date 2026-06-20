# 07 Li Core-Shell FEM

## 阶段目的

复现 Li 论文中 Cu@Fe 包覆式复合粉末的致密化规律。论文路线是 PFC2D 生成
随机颗粒坐标，再导入 MSC.MARC 做多颗粒 core-shell FEM。本阶段要建立开源或
COMSOL 平行替代路线。

## 当前基础

已有：

- Cu fraction、温度、摩擦、速度、长径比、颗粒数收敛代理模型。
- DEM-FEM handoff schema。
- Li core-shell 指标输出。

不足：

- 还没有真实 Cu@Fe core-shell 几何。
- 还没有 Cu/Fe 界面摩擦、塑性和热膨胀。
- 还没有多颗粒 core-shell FEM 变形。

## 推荐路线

| 子任务 | 主线 | 开源平行线 |
|---|---|---|
| 单颗粒 core-shell 压缩 | COMSOL | CalculiX |
| 双颗粒 core-shell 接触 | COMSOL | CalculiX/Code_Aster |
| 10-20 颗粒小样本 | COMSOL | Code_Aster |
| 100/197 颗粒论文尺度 | 待评估 | WSL2/Linux + Code_Aster 或 CalculiX |

## 第一阶段小目标

先做单颗粒和双颗粒：

1. Fe core + Cu shell 几何。
2. 设置 Cu/Fe 弹塑性或简化弹性参数。
3. 设置上下压头压缩。
4. 输出等效应力、塑性应变、界面应力、相对密度变化。
5. 与代理模型中的 Cu fraction 趋势对比。

## 验收门槛

| 验收项 | 判定 |
|---|---|
| 单颗粒 core-shell 几何可求解 | 待完成 |
| 双颗粒接触模型可求解 | 待完成 |
| Cu shell 对应力分布的改善可观察 | 待完成 |
| 输出能回填 Li 指标表 | 待完成 |

