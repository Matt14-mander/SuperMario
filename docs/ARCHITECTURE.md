# 架构说明

## 1. 边界

新项目采用“核心在内、适配器在外”的结构。

```text
Human Input ─┐
Scripted ────┤
Jev ─────────┼── Action ──> Deterministic Game Core ──> WorldSnapshot
PPO ─────────┘                         │                       │
                                      │                       ├── Pygame renderer
LevelSpec ──> Generator ──> Validator ┘                       ├── Gymnasium env
                                                              ├── Replay recorder
                                                              └── Benchmark metrics
```

`ai_platformer.core` 不允许导入以下模块：

- `pygame`；
- `gymnasium`；
- Stable-Baselines3 或 PyTorch；
- Jev/LLM SDK；
- 网络客户端；
- 原始 `source` 包。

这一约束保证同一套规则可以运行在人类游玩、批量训练、回放验证和端侧推理中。

## 2. 模块职责

| 模块 | 职责 | 不负责 |
| --- | --- | --- |
| `core` | 固定步长模拟、动作、状态、碰撞、胜负条件 | 窗口、键盘、模型调用 |
| `content` | LevelSpec、PCG、静态与动态可玩性验证 | 实时渲染 |
| `envs` | Gymnasium observation/action/reward 封装 | 重复实现物理 |
| `agents` | Scripted、PPO、Jev、LLM 适配 | 修改世界状态 |
| `adaptive` | 玩家画像、DDA 策略、约束和审计 | 隐式改写核心规则 |
| `rendering` | Pygame 显示、音频、键盘输入 | 作为权威状态源 |
| `benchmark` | 固定 seed、评估集、指标、回放 | 训练时临时逻辑 |
| `deployment` | ONNX 导出、校验、运行时适配 | 模型训练 |

## 3. 数据流

每个 simulation tick 只执行一次以下流程：

1. controller 根据 observation 选择稳定的离散 `Action`；
2. `GameCore.step` 解码 action 并推进一个固定 tick；
3. core 返回新的 `WorldSnapshot` 和 episode 结果；
4. renderer、environment、replay 和 metrics 分别消费这个结果；
5. 任何外部组件都不能绕过 action 直接修改 core 状态。

## 4. 时间尺度

- Physics：固定 60 Hz，保证轨迹可复现。
- Agent control：初期每 4 个 physics ticks 决策一次，即 15 Hz。
- Jev/DDA：按事件或较低频率决策，不进入逐帧物理循环。
- LLM：默认只用于关卡生成前或非实时内容，不阻塞 gameplay loop。

具体频率在基准测试后调整，但层级关系保持不变。

## 5. 版本化契约

以下对象必须具有稳定版本：

- 离散 action ID；
- observation layout；
- LevelSpec schema；
- replay format；
- benchmark suite；
- ONNX 输入输出名称和 shape。

修改上述接口时应提升对应版本，避免旧模型、旧回放和新引擎静默不兼容。

## 6. Legacy 迁移

当前 `source/` 是参考实现而不是新架构的一部分。迁移顺序为：

1. 输入抽象；
2. 玩家运动；
3. 地面与碰撞；
4. 相机和渲染；
5. 敌人、砖块、金币和终点；
6. 菜单、音频和完整关卡流程。

每迁移一块，先添加 headless 测试，再由 Pygame adapter 展示。迁移完成前不删除 legacy 文件。
