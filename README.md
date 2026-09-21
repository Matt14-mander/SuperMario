# AI-Native Platformer Lab

这是一个由早期 Pygame 超级马里奥练习项目演进而来的 AI-native 横版平台游戏实验场。

项目的长期目标包括：

- 可复现、可无头加速运行的游戏核心；
- Gymnasium 兼容的 agent benchmark environment；
- Scripted agent、Jev 决策层和 PPO policy；
- Dynamic Difficulty Adjustment（DDA）；
- Procedural Content Generation（PCG）与 LLM 内容设计；
- PPO policy 导出为 ONNX，并接入轻量推理运行时；
- 用原创或 AI 辅助制作的角色、美术、音乐和音效替换现有素材。

## 当前状态

- `source/`、`resources/`、`data/`：原始学习项目，暂时作为 legacy 参考实现保留。
- `ai_platformer/`：新的 AI-native 代码，所有新增能力从这里开始。
- `tests/`：不依赖窗口和素材的单元测试，以及后续端到端测试。
- `docs/`：架构约束和分阶段开发计划。
- `assets/`：未来原创资产及主题包；现有马里奥素材不会迁入这里。

详细设计见：

- [架构说明](docs/ARCHITECTURE.md)
- [初步开发计划](docs/DEVELOPMENT_PLAN.md)

## 开发原则

1. 游戏规则与物理由纯 Python 核心维护，不能读取键盘或依赖窗口。
2. 人类、Scripted、Jev、PPO 都通过同一个 `Action` 接口控制游戏。
3. 渲染只是状态的消费者；训练时可以完全关闭。
4. 每个 episode 都能用 seed、关卡版本和动作序列复现。
5. LLM 生成结构化内容意图，确定性代码负责验证并生成可运行关卡。

## 当前最小验证

项目骨架只依赖 Python 标准库：

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

旧项目尚未迁移到新核心，现阶段不要删除 `source/` 或 `resources/`。
