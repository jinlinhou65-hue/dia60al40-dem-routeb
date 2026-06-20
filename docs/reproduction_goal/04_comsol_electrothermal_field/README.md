# 04 COMSOL Electrothermal Field

## 阶段目的

用 COMSOL 作为电流场和温度场主线，替代当前 Python 中的 lumped temperature
proxy。DEM 负责颗粒位置、接触力和接触网络；COMSOL 负责连续场求解。

## 为什么使用 COMSOL

用户已有 COMSOL。热场、电流场和 Joule heating 正是 COMSOL 的强项，因此热场
不需要绕开 COMSOL。开源 FEM 只作为平行验证和无授权环境下的轻量替代。

## 输入数据

| 输入 | 来源 | 用途 |
|---|---|---|
| `dem_fem_handoff_stage*.csv` | DEM workflow | 颗粒位置、半径、材料 |
| `contact_forces/*_contacts.csv` | DEM workflow | 接触关系、接触力、可换算接触电导/热源 |
| 材料参数 | PDF/材料手册 | Al、diamond、Cu、Fe 的电导、热导、热容 |
| 边界条件 | 论文/实验设定 | 电极、电压/电流、散热、环境温度 |

## COMSOL 模块建议

| 物理场 | COMSOL 模块 |
|---|---|
| 电流分布 | Electric Currents |
| 温度场 | Heat Transfer in Solids |
| 电热耦合 | Joule Heating |
| 后续热-力耦合 | Solid Mechanics + Thermal Expansion |

## 最小可行模型

第一步只做一个 DEM stage 的小模型：

1. 导入 stage5 或中间 stage 的颗粒几何。
2. 给 Al/diamond 或 Cu/Fe 分配材料参数。
3. 对上下边界施加电压或电流。
4. 接触处采用接触电阻/热阻，或把 DEM 接触热源映射为局部热源。
5. 求解电势、电流密度、Joule heat、温度场。
6. 导出粒子平均温度、热点位置、热通量和温度梯度。

## 可视化目标

阶段完成后应至少包含：

- 颗粒几何图。
- 电势场图。
- 电流密度图。
- 温度场图。
- 颗粒温度分布直方图。
- 接触力与温度热点的相关性图。

## 验收门槛

| 验收项 | 判定 |
|---|---|
| COMSOL 能导入 DEM 颗粒几何 | 待完成 |
| 电流场求解收敛 | 待完成 |
| 温度场求解收敛 | 待完成 |
| 输出能回写到 Python 后处理 | 待完成 |
| 热源-温度-烧结指标链条可运行 | 待完成 |

