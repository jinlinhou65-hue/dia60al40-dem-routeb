# Al 氧化膜归档图网络敏感性

判定：`bounded_oxide_network_sensitivity_pass`  
实验标定：`false`

跨平台输入合同同时保留原始 CRLF SHA-256 和 canonical-LF SHA-256。后者只消除
GitHub Ubuntu checkout 的换行编码差异，不放宽任何数值内容、拓扑或场景门槛。

## 运行命令

```powershell
py scripts/analyze_al_oxide_contact_network.py `
  --parameters docs/reproduction_goal/04_comsol_electrothermal_field/data/source/al_oxide_contact_preregistered_parameters.json `
  --archive-dir docs/reproduction_goal/04_comsol_electrothermal_field/evidence/true_3d_percolation/run_29246532552 `
  --output-dir docs/reproduction_goal/04_comsol_electrothermal_field/evidence/al_oxide_network_sensitivity
```

## 文件含义

| 文件 | 内容 |
|---|---|
| `network_summary.json` | 全局判定、范围、最大守恒误差和声明边界 |
| `scenarios.csv` | 18 个 clean/完整膜/部分破膜场景的完整网络量 |
| `edge_results.csv` | `18 x 50=900` 条逐边电压、电流、Joule 功率、路径和排名 |
| `gate_table.csv` | 八项预注册门槛及不可修改判定 |
| `oxide_network_sensitivity.png` | 膜参数、破膜比例、等效电阻和两种电源模式响应 |
| `oxide_network_hotspots_3d.png` | clean、完整膜和 `f_m=1e-6` 的三维相对热点路径 |
| `evidence_manifest.json` | 输入、实现、NumPy/Matplotlib 版本和输出 SHA-256 |

## 核心结果

- clean 完整网络等效电阻为 `0.0146764894 ohm`，明显低于单条最短路径的
  `0.0353279646 ohm`，证明并联通道不可忽略。
- 完整膜九场景为 `2.8075e9-4.4921e15 ohm`；这是假定完整膜的有界结果，不是实测。
- 部分破膜主模型从 `f_m=0` 的 `3.3691e9 ohm` 降到 `f_m=1` 的
  `0.0146765 ohm`；`f_m=1e-12` 已降至 `1.4676e4 ohm`，说明极小金属微桥可能支配
  传输，但不能据此宣称真实破膜比例达到该值。
- 固定 `0.1 V` 时桥接增加使总功率单调上升；归一化固定 `1 A` 时总功率单调下降。
- 18 场景的最短路径均为 `95->41->36->27->33`，top-5 Joule 边也相同。当前统一
  `f_m` 假设主要改变幅值，没有产生热点迁移；未来只有逐边非均匀破膜或烧结反馈才
  可能改变路径拓扑。
- 所有场景在 `0.1 V` 下均未超过 `4e8 V/m` 器件薄膜诊断边界。该结果不排除机械破膜。

最大相对 KCL 残差为 `2.132e-15`，最大相对功率平衡误差为 `3.969e-15`。所有八项
门槛通过。固定 `1 A` 的完整膜功率可达非物理大值，它只用于方向极限检验，不能作为
实验电源方案或温升输入。
