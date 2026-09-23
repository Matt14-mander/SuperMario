"""Train the first reproducible MLP PPO baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_platformer.agents.ppo import train_ppo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/ppo_state_v0.json"),
    )
    parser.add_argument("--timesteps", type=int, help="override total training timesteps")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/ppo_state_v0"),
    )
    args = parser.parse_args()

    with args.config.open(encoding="utf-8") as stream:
        config = json.load(stream)
    if args.timesteps is not None:
        if args.timesteps <= 0:
            parser.error("--timesteps must be positive")
        config["total_timesteps"] = args.timesteps
    report = train_ppo(config, args.output_dir)
    print(json.dumps(report["evaluation"], ensure_ascii=False, indent=2))
    print(f"model: {report['artifacts']['model']}")
    print(f"metadata: {(args.output_dir / 'run.json').resolve()}")


if __name__ == "__main__":
    main()
