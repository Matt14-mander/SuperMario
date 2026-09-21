# Scripts

后续命令行入口放在这里，包括：

- legacy smoke run；
- headless benchmark；
- PPO train/evaluate；
- replay playback；
- ONNX export/validation；
- PCG batch generation/validation。

脚本只负责编排，领域逻辑必须保留在 `ai_platformer/` 中。
