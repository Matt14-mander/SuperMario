# 初步开发计划

## 项目北极星

构建一个既能作为完整横版平台游戏，也能作为 AI agent 研究环境运行的项目。所有实验必须可复现、可比较，并能从训练一路走到轻量部署。

## Phase 0：仓库基线与架构骨架

状态：**进行中**

目标：保住原始项目，同时为新实现建立清晰边界。

- [x] 保留 `source/`、`resources/` 和旧 JSON 数据作为 legacy 基线；
- [x] 建立新 Python package 和模块目录；
- [x] 定义稳定离散动作、状态快照和核心引擎协议；
- [x] 建立依赖分组、测试目录和基础文档；
- [ ] 修复 legacy 启动入口，记录可运行基线；
- [ ] 清点重复的 `data/` 与 `source/data/`，确定唯一事实来源；
- [ ] 为旧版录制一个人工操作 smoke path。

验收标准：旧版可启动；新包可导入；基础测试通过；没有移动或删除用户原始素材。

## Phase 1：确定性 Headless Core

目标：在没有 Pygame 窗口、图片和音频的条件下完整推进基础关卡。

- [ ] 定义固定 timestep 和数值单位；
- [ ] 从旧版迁移玩家移动、跳跃和重力；
- [ ] 实现 axis-aligned tile/rect collision；
- [ ] 实现出生、死亡、终点和 episode 上限；
- [ ] 将旧 `level_1.json` 适配到临时 LevelSpec；
- [ ] 支持 `reset(seed, level_id)` 和 `step(action)`；
- [ ] 增加 determinism、碰撞、跳跃和终止条件测试。

验收标准：相同 seed 与 action 序列产生完全相同的 snapshots；10,000 个 headless ticks 不需要初始化 Pygame。

## Phase 2：Pygame Adapter 与 Gymnasium Environment

目标：同一个 core 同时支持人类游玩和 agent 训练。

- [ ] 新建 Pygame renderer 和 keyboard controller；
- [ ] 实现 `PlatformerState-v0`；
- [ ] 定义紧凑状态 observation 和 reward v1；
- [ ] 添加 action repeat、time limit 和统计 wrappers；
- [ ] 通过 Gymnasium environment checker；
- [ ] 实现 random、move-right、rule-jump 三个 scripted baselines；
- [ ] 记录 episode replay 和关键指标。

验收标准：键盘与 scripted agent 走相同 action 接口；environment checker 通过；benchmark 可批量运行。

## Phase 3：PPO 基线与 Benchmark v1

目标：形成第一个可以量化比较的学习闭环。

- [ ] 固定训练、验证和未见关卡 seed；
- [ ] 训练 MLP PPO 状态策略；
- [ ] 建立 curriculum：平地 → 缺口 → 障碍 → 敌人；
- [ ] 保存配置、随机种子、checkpoint 和评估结果；
- [ ] 指标包含成功率、最大进度、死亡原因和 sample efficiency；
- [ ] 建立回归阈值，防止引擎改动悄悄破坏策略。

验收标准：PPO 在未见基础关卡上显著超过 scripted move-right baseline，训练过程可复现。

## Phase 4：PCG、LLM 与可玩性验证

目标：让生成内容进入受约束、可验证的数据管线。

- [ ] 定义版本化 LevelSpec JSON Schema；
- [ ] 实现基于 segment/grammar 的生成器；
- [ ] 静态验证几何、出生点和终点；
- [ ] 用图搜索或运动可达性检查过滤明显死图；
- [ ] 用 scripted/PPO rollout 做动态验证；
- [ ] LLM 只生成符合 schema 的主题与关卡设计意图；
- [ ] 保存 prompt、model、seed、spec 和验证报告。

验收标准：生成关卡全部通过 schema；不可玩候选不会进入游戏；同 seed 可重建同一关卡。

## Phase 5：DDA 与 Jev 决策层

目标：验证低频高级决策与自适应难度，而不是把模型塞进逐帧循环。

- [ ] 定义玩家技能画像和事件特征；
- [ ] 建立可解释的 DDA 参数边界；
- [ ] 建立固定、规则 DDA、学习型 DDA 三组实验；
- [ ] Jev 从合法高级策略候选中进行选择；
- [ ] 记录选择、置信度、输入状态和后续结果；
- [ ] 设计消融实验，比较 Jev、规则和 PPO hierarchy。

验收标准：所有难度调整可审计；固定 seed 下能回放决策；网络失败时安全降级到本地策略。

## Phase 6：ONNX、轻量推理与原创资产

目标：完成训练到部署链路，并建立可替换的原创主题系统。

- [ ] 固化 observation preprocessing；
- [ ] 导出 PPO policy 到 ONNX；
- [ ] 对比 PyTorch 与 ONNX 输出及 episode 行为；
- [ ] 明确目标 TinyInfer 项目及支持的 ONNX operators；
- [ ] 必要时简化 policy network 或编写运行时 adapter；
- [ ] 建立角色、tileset、动画、音频和 UI theme manifest；
- [ ] 用原创/AI 辅助资产替换现有第三方 IP 素材。

验收标准：端侧 policy 与 PyTorch policy 在固定测试集上一致；发布构建不包含马里奥版权素材。

## 下一迭代建议

下一迭代只处理 Phase 0 剩余项和 Phase 1 的最小竖切：

1. 修复 legacy 启动；
2. 加入输入抽象，让玩家不再直接访问 `pygame.key.get_pressed()`；
3. 用旧 `level_1.json` 构造最小 headless world；
4. 完成平地行走、跳跃、死亡和终点；
5. 用固定动作序列验证 deterministic replay。

在这条竖切完成前，不开始接入 PPO、Jev 或 LLM SDK。

## 暂不纳入首轮的工作

- 像素 observation 与 CNN policy；
- 多智能体与 PettingZoo；
- 实时 LLM 生成碰撞几何；
- 大规模素材生成；
- 多平台发布和联机功能。

这些能力不是被放弃，而是要等核心接口、可复现性和 benchmark 稳定后再进入。
