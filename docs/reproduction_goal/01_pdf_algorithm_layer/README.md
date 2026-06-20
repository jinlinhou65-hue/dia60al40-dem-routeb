# 01 PDF And Algorithm Layer

## 阶段目的

把四篇硕士论文中的物理机制、参数、指标和趋势转化为可执行的算法层复现。
这一层不依赖具体 DEM/FEM 软件，目的是先建立统一指标和验收语言。

## 对应论文

| 论文 | 机制 | 已建立指标 |
|---|---|---|
| Zhang | 多尺度力学不均匀性 | 压力、密度、Gini、participation、力链、D1、D2 |
| Yuan | 拱桥结构 | arch count、length、strength、buckling、direction |
| Liu | 压制-烧结耦合 | Heckel、Kawakita、Huang、Joule heat、neck growth |
| Li | 包覆式复合粉末 | Cu fraction、温度、摩擦、速度、长径比、颗粒数收敛 |

## 已完成内容

- PDF 页码锚点和方法映射：`docs/paper_pdf_reproduction_map.md`。
- 论文算法入口：`scripts/run_paper_algorithm_reproduction.py`。
- 内容验证 workflow：`paper-algorithm-reproduction` 已成功运行。
- 输出结构已包含 acceptance summary、manifest、趋势检查和报告。

## 主要输入

- 用户提供的四篇硕士论文 PDF。
- `python/paper_reproduction/*` 中的 solver-neutral 指标实现。
- `docs/paper_pdf_reproduction_map.md` 中的页码锚点。

## 主要产物

后续该阶段新增产物应放在本文件夹：

```text
01_pdf_algorithm_layer/
  report.md
  data/
  figures/
  evidence/
```

当前基础证据仍保留在仓库已有文档和 workflow artifact 中。

## 验收门槛

| 验收项 | 当前状态 |
|---|---|
| 四篇论文均有核心机制映射 | 通过 |
| 每篇论文均有可执行算法层输出 | 通过 |
| 输出字段能与后续 DEM/FEM 数据合同对应 | 通过 |
| 每篇论文全部图表和实验值一比一复现 | 未完成 |

## 下一步

本阶段暂不继续扩展。只有当后续 COMSOL/FEM 高保真模型需要新的 PDF 参数时，
再回到本阶段补充页码锚点和参数表。

