# 05 Yuan Shape And Arch Bridge

## 阶段目的

复现 Yuan 论文中颗粒形状对拱桥结构和致密化的影响。当前 LIGGGHTS 轻量 DEM
使用球形颗粒，只能得到接触网络和拱桥代理指标，不能严格复现圆形、六边形、
条形颗粒之间的形状差异。

## 当前基础

已有：

- 强接触连通图。
- arch count、length、strength、buckling、direction。
- stage-level `*_arches.csv`。
- Yuan 算法层趋势检查。

不足：

- 当前 DEM 粒子是球形。
- 缺少真实非球形颗粒旋转、嵌锁和形状导致的拱桥形成机制。
- 还没有 MPFEM 颗粒变形。

## 可选技术路线

| 路线 | 用途 | 优先级 |
|---|---|---|
| LAMMPS superquadric/cluster | 非球形 DEM 快速试验 | 高 |
| YADE clump/polygon | PFC-like 接触律研究 | 中 |
| Chrono DEME clump | 高粒子数形状模拟 | 后续 |
| CalculiX/Code_Aster MPFEM | 小规模可变形颗粒 | 后续 |
| COMSOL | 小样本形状应力场对照 | 可选 |

## 第一阶段小目标

不直接上大模型。先做三组形状 demo：

1. 圆形颗粒。
2. 六边形或近似多边形颗粒。
3. 条形或低长径比颗粒。

每组输出相同压制阶段下的：

- 密度。
- 平均配位数。
- arch count。
- arch total length。
- arch obstruction index。
- direction angle。
- buckling angle。

## 验收门槛

| 验收项 | 判定 |
|---|---|
| 至少一种非球形 DEM 后端可运行 | 待完成 |
| 三种形状输出统一 arch 指标 | 待完成 |
| 形状趋势与 Yuan 论文方向一致 | 待完成 |
| 可视化展示拱桥网络 | 待完成 |

