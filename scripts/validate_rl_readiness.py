"""Run SB3 compatibility, random stability, and reward exploit gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_platformer.benchmark import readiness_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, help="override configured episode count")
    parser.add_argument("--max-steps", type=int, help="override per-episode step limit")
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    with (root / "config" / "rl_readiness_v0.json").open(encoding="utf-8") as stream:
        config = json.load(stream)
    report = readiness_report(
        episodes=args.episodes or int(config["episodes"]),
        max_steps_per_episode=args.max_steps or int(config["max_steps_per_episode"]),
        base_seed=int(config["base_seed"]),
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
