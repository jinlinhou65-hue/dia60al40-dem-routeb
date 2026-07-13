# 00 Project Control

## 阶段目的

本阶段是总控层。它负责定义项目边界、阶段归档方式、验收规则和后续执行纪律。
它不是物理仿真阶段，而是保证后续工作不再反复混杂、难以检阅。

## 当前状态

状态：进行中。

当前仓库已经有基础复现和轻量 DEM 证据，但完整目标仍未完成。后续所有新增结果都
应归档到 `docs/reproduction_goal/<stage>/` 下，避免数据散落在 workflow 页面、
临时输出目录或口头描述里。

## 总目标 Prompt

后续工程代理统一使用
[`full_reproduction_goal_prompt.md`](full_reproduction_goal_prompt.md) 作为任务合同。
当前执行版为 2.0（2026-07-13）。该 Prompt 记录当前已验证状态、八个复现阶段、
科学边界、阶段锁、变更登记、归档规范、验收门槛和完整电阻烧结闭环的可视化目标。
其中 `<current_next_task>` 是续跑入口，只有在对应证据提交并通过 workflow 后才能更新。

## 总控规则

1. 一个阶段只解决一个主要问题。
2. 每次开始阶段前先写清目的、输入、产物和验收门槛。
3. workflow 成功只是运行证据，不等于科学复现完成。
4. 缺数据、缺图、缺报告时，阶段不能标为完成。
5. 诊断、模型修改、文档更新应分开提交。
6. COMSOL 可以作为热场主线；开源 FEM 保留为平行验证和可公开复现路线。

## 统一数据合同

| 数据 | 来源 | 用途 |
|---|---|---|
| `pressure_density_curve.csv` | DEM workflow | 压力-密度曲线和宏观压制响应 |
| `dem_fem_handoff_*.csv` | DEM stage export | COMSOL/FEM 几何和材料输入 |
| `contact_forces/*_contacts.csv` | LIGGGHTS pair/gran/local | 接触力、力链、拱桥、电热源 |
| `series_network_metrics.csv` | Python 后处理 | Zhang/Yuan/Liu/Li 阶段指标 |
| `stage_details/*_arches.csv` | Python 后处理 | Yuan 拱桥结构分析 |
| `stage_details/*_electrothermal_*.csv` | Python 后处理或 COMSOL 回写 | 电流、Joule heat、温度和烧结输入 |

## 阶段状态定义

| 状态 | 含义 |
|---|---|
| `planned` | 目标明确，但还未实现或还未运行 |
| `in_progress` | 已有代码或运行证据，但还未完成判读 |
| `baseline_done` | 基础层已完成，可作为后续输入 |
| `review` | 数据完整，但科学趋势或参数仍需校准 |
| `done` | 数据、图、报告和验收均齐全 |

## 可视化和检阅要求

每个阶段完成后至少应有：

- 一个阶段 `report.md`，说明结论和局限。
- 一个可读表格，说明关键数值。
- 至少一张图或 Mermaid 图，说明数据流、压力曲线、网络结构或温度分布。
- 一个验收表，列出 `pass/review/fail`。
