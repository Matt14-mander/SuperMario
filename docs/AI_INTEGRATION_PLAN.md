# AI 接入门槛与顺序

## 结论

PPO 适合作为本项目第一个“学习型”AI，但不应成为第一个 agent。正确顺序是：

1. Gymnasium environment；
2. random / move-right / rule-jump scripted agents；
3. benchmark 与 reward sanity check；
4. MLP PPO；
5. ONNX 导出与轻量推理；
6. 再扩展 PCG/LLM、DDA 和 Jev。

## 当前成熟度

| Gate | 要求 | 当前状态 |
| --- | --- | --- |
| Core | 确定性 reset/step、固定 action、终止条件 | 已满足 |
| Dynamic content | 至少一种动态实体、score/reward/reset | 金币已满足 |
| Settings | 版本化 seed、物理与 episode 参数 | 已满足 |
| Environment | Gymnasium reset/step/spaces/render | `PlatformerState-v0` 已实现 |
| Validation | Gymnasium 与 SB3 checker | Gymnasium 已通过，SB3 待执行 |
| Baselines | random、move-right、rule-jump | 已实现 |
| Benchmark | 固定训练/验证/未见 seeds 与指标 | v0 已实现 |

因此环境接口已经达到 PPO 预备阶段；在 reward 压力测试、随机 rollout 门禁和 SB3 checker 完成后即可开始正式 PPO baseline，不需要等待所有敌人和砖块迁移完成。

## PlatformerState-v0 建议契约

### Action

继续使用当前离散 action ID 0–9。训练开始后，v0 action ID 不再静默修改；新增组合动作需要创建新环境版本。

### Observation

首版使用结构化 float vector，而不是像素：

- player x/y、velocity x/y；
- grounded、facing；
- normalized progress；
- 前方地面边缘/缺口距离；
- 最近静态障碍相对位置与尺寸；
- 最近若干 active coin 相对位置；
- 当前 score/coin ratio；
- remaining step ratio。

所有值必须有固定 shape、dtype 和归一化范围。

### Reward v1

- 正向 progress delta；
- 收集金币奖励；
- 通关显著正奖励；
- 死亡显著负奖励；
- 很小的时间成本，避免原地等待；
- reward breakdown 写入 `info`，方便调参与消融。

reward 应由 environment/wrapper 组合，core 只保留语义事件与基础 transition 数据。

## PPO 开始条件

只有以下条件全部满足才开始正式训练：

- `gymnasium.utils.env_checker.check_env` 通过；
- SB3 checker 通过；
- 1,000 次随机 episode 无崩溃或状态泄漏；
- 相同 seed/action replay 完全一致；
- move-right 和 rule-jump baseline 有固定评估报告；
- reward 不存在原地刷分、反复刷金币或自杀获利；
- train/validation/unseen seeds 已分离；
- observation/action/reward 标记为 v1 并写入 checkpoint metadata。

## 其他 AI 的接入时机

### DDA

在 telemetry 能记录死亡点、重试次数、通关速度、金币偏好和操作错误后接入。第一版应为规则 DDA，而不是神经网络。

### LLM + PCG

在 `LevelSpec v1`、schema validator 和可玩性检查器完成后接入。LLM 输出设计意图和结构化 spec，不直接控制逐帧物理。

### Jev

在定义高级候选动作后接入，例如“快速推进 / 收集 / 保守通过”。Jev 不负责低层跳跃时序。

### 像素策略

状态 PPO 稳定后再建立 `PlatformerPixels-v0`，否则视觉学习和游戏规则问题会混在一起。
