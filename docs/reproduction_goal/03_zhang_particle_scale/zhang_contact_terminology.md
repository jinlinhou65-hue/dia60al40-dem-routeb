# Zhang Contact Terminology Ledger

| Chinese source term | English canonical term | Symbol / code name | Decision |
|---|---|---|---|
| 离散元法 | discrete element method | DEM | Spell out once, then use DEM. |
| Hertz-Mindlin-Deresiewicz 接触模型 | Hertz-Mindlin-Deresiewicz contact model | `model hertz tangential history` | Treat as model-family alignment, not exact implementation identity. |
| Coulomb 模型 | Coulomb friction limit | `coefficientFriction` | Use for the tangential-force cap. |
| 阻尼系数 | damping coefficient | paper value `0.2` | Keep distinct from coefficient of restitution; definition is missing. |
| 恢复系数 | coefficient of restitution | `coefficientRestitution`, `e` | Solver input from which current LIGGGHTS Hertz damping is derived. |
| 法向阻尼常数 | normal viscoelastic damping constant | `gamma_n` | Derived by current Hertz implementation; not the paper's reported scalar by default. |
| 切向阻尼常数 | tangential viscoelastic damping constant | `gamma_t` | Derived separately and enabled by default in current LIGGGHTS Hertz. |
| 颗粒间摩擦因数 | interparticle friction coefficient | `mu_p` | Must be controllable independently from sidewall friction. |
| 侧壁摩擦因数 | sidewall friction coefficient | `mu_w` | Next paper-guided sensitivity variable. |
| 颗粒与墙体间摩擦因数 | particle-wall friction coefficient | pair entries Al-wall and diamond-wall | Distinguish sidewall from punch/tool contacts in implementation notes. |
| 接触力基尼指数 | contact-force Gini coefficient | `G` | Lower value means more uniform contact forces. |
| 参与指数 | participation number | `P` | Higher value means more uniform contact forces. |
| 力链强度不均匀度 | normalized force-chain strength inhomogeneity | `D1` | Standard deviation divided by mean force-chain strength. |
| 局部应力不均匀度 | normalized local-stress inhomogeneity | `D2` | Standard deviation divided by mean local stress. |
| 压制轴向应变 | compaction axial strain | `epsilon_a` | Paper endpoint is 0.25. |
| 端点压力窗口 | endpoint pressure bracket | 572-638 MPa | Benchmark from paper experiment/simulation, not a universal material window. |
