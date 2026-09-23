# PPO Baseline v0

## 结论

首个 `PlatformerState-v0` MLP PPO 训练链路已经闭环：环境检查、训练、模型保存、确定性评估和模型重载全部通过。

这次基线没有学会通关。100,000 配置步实际按完整 rollout 执行了 100,352 步，validation seeds `100–103` 的结果为：

| 指标 | PPO v0 | move-right | rule-jump |
| --- | ---: | ---: | ---: |
| 成功率 | 0% | 0% | 100% |
| 平均进度 | 12.76% | 12.76% | 100% |
| 平均 episode 步数 | 1024 | 1024 | 244 |

PPO v0 的 deterministic policy 选择 `RIGHT_RUN`，推进到第一个管道后停滞。这是有用的负结果：完整关卡上的探索难度对首轮 PPO 过高，下一轮应先建立 curriculum，而不是直接堆训练步数。

## 固定配置

- seed：`20260923`
- vector environments：4
- action repeat：4
- 训练 episode 上限：1024 environment steps
- actor：`[64, 64]` ReLU
- critic：`[64, 64]` ReLU
- rollout：`4 × 256 = 1024` transitions
- batch size：256
- epochs：5
- entropy coefficient：0.01
- device：CPU

完整配置见 [`config/ppo_state_v0.json`](../config/ppo_state_v0.json)。每次运行会在输出目录保存 `model.zip`、Monitor CSV 和包含依赖版本、动作表、配置及评估结果的 `run.json`。

## 下一轮实验

1. 增加平地、单管道、单缺口三个小型训练关卡；
2. 按平地 → 管道 → 缺口 → 完整关卡建立 curriculum；
3. 在 curriculum 各阶段保持 validation seeds 不参与训练；
4. 加入定期 evaluation callback 和 best-model checkpoint；
5. PPO 至少超过 move-right 后，再开始 ONNX 导出。

不建议立即修改 reward 让“接近管道”获得人工奖励。这会把关卡解法写入 reward，并增加 reward hacking 风险；优先通过课程难度解决探索问题。
