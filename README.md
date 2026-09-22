# AI-Native Platformer Lab

一个从大一 Pygame 学习项目演进而来的 AI-native 横版平台游戏与智能体实验场。

项目正在把原始马里奥练习代码迁移成一套可复现、可无头运行、可训练 agent、可程序化生成关卡，并最终能部署轻量策略模型的原创游戏基础设施。

> 当前仍包含学习阶段使用的马里奥相关素材，仅用于本地研究和迁移验证。公开发行前会全部替换为原创或明确授权的角色、美术、音乐与音效。

## 当前能力

- 确定性 `BasicPlatformerCore`，不依赖 Pygame、窗口或系统时间；
- 人类玩家与未来 agent 共用同一套离散 `Action`；
- Pygame renderer 只消费 `WorldSnapshot`，不维护第二套物理状态；
- 固定 seed 的 episode、死亡、通关和重新开始；
- 旧 `level_1.json` 的地形、管道、台阶、出生点、旗杆和金币迁移；
- 金币动态实体、收集状态、score、reward 与 HUD；
- 暂停、快速重开和版本化 gameplay settings；
- headless 单元测试与真实 Pygame 集成测试；
- 为 Gymnasium、PPO、PCG、DDA、Jev、LLM 和 ONNX 预留的模块边界。

尚未迁移：敌人、可交互砖块/箱子、power-up、checkpoint/传送、完整音频流程与原创资产。

## 快速开始

推荐使用 64 位官方 CPython 3.11 或 3.12。某些 MSYS Python 发行版没有可用的 Pygame wheel，会被迫本地编译 SDL。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m source.main
```

当前 Codex 工作区也可以使用已经准备好的隔离依赖：

```powershell
$env:PYTHONPATH = (Resolve-Path ".deps").Path
& "C:\Users\Rog\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m source.main
```

## 操作

| 操作 | 按键 |
| --- | --- |
| 移动 | `←` / `→` |
| 跳跃 | `A` / `Space` |
| 奔跑 | `S` / `Shift` |
| 暂停/继续 | `P` / `Esc` |
| 重开当前关卡 | `R` |
| 菜单确认 | `Enter` |

游戏参数位于 [`config/gameplay.json`](config/gameplay.json)，包括关卡、seed、帧率、终局展示时间和物理参数。

## 测试

不安装 Pygame 也能运行 headless core 测试；Pygame 集成测试会自动跳过：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

安装完整项目依赖后，所有集成测试都应执行并通过：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

## 架构

```text
Keyboard / Scripted / PPO / Jev
              │
            Action
              │
    Deterministic Game Core  <── LevelDefinition / future LevelSpec
              │
         WorldSnapshot
       ┌──────┼──────────┐
   Pygame   Gymnasium   Replay/Benchmark
```

```text
ai_platformer/
├── core/          # 动作、物理、碰撞、状态和 episode 规则
├── content/       # legacy adapter、未来 LevelSpec/PCG/验证器
├── envs/          # Gymnasium environment（下一阶段）
├── agents/        # scripted、PPO、Jev、LLM adapters
├── adaptive/      # 玩家建模与 DDA
├── rendering/     # Pygame 输入和显示
├── benchmark/     # 固定 seed、指标、replay 和回归评估
└── deployment/    # ONNX 导出和轻量推理
game_content/
└── levels/         # 新内容 overlay，逐步替代 legacy JSON
```

详细文档：

- [架构约束](docs/ARCHITECTURE.md)
- [开发计划](docs/DEVELOPMENT_PLAN.md)
- [游戏内容迁移计划](docs/CONTENT_MIGRATION_PLAN.md)
- [AI 接入门槛与顺序](docs/AI_INTEGRATION_PLAN.md)
- [GitHub 项目元数据](docs/GITHUB.md)

## AI 路线

首个学习型 agent 计划采用 **PPO**，但接入顺序是：

1. 冻结 `Action v1`、结构化 observation 和 reward v1；
2. 实现并注册 `PlatformerState-v0` Gymnasium environment；
3. 通过 Gymnasium/SB3 environment checker；
4. 建立 random、move-right、rule-jump scripted baselines；
5. 再训练 MLP PPO，并在未见 seed/关卡上评估；
6. 稳定后导出 ONNX，最后适配目标轻量推理运行时。

LLM/PCG、DDA 和 Jev 会在 LevelSpec、telemetry 与 benchmark 稳定后接入，避免模型依赖不断变化的游戏协议。

## 内容与版权

`source/` 和 `resources/` 中的旧内容是迁移参考。未来可发布内容放在 `assets/`，通过主题 manifest 引用。发布构建不得包含第三方游戏 IP 素材。

## 项目阶段

当前阶段：**可玩共享核心 + 首个动态内容（金​​币）**。

下一阶段：**`PlatformerState-v0`、observation/reward v1、scripted benchmark，然后 PPO baseline**。
