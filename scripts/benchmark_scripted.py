"""Run fixed-seed scripted baselines for PlatformerState-v0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_platformer.agents.scripted import SCRIPTED_AGENTS
from ai_platformer.benchmark import evaluate_scripted_agent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("train", "validation", "unseen"), default="validation")
    parser.add_argument(
        "--agents",
        nargs="+",
        choices=tuple(SCRIPTED_AGENTS),
        default=list(SCRIPTED_AGENTS),
    )
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="optional benchmark-only episode cap",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    with (root / "config" / "benchmark_v0.json").open(encoding="utf-8") as stream:
        config = json.load(stream)
    seeds = config["suites"][args.suite]
    results = [
        evaluate_scripted_agent(
            name,
            SCRIPTED_AGENTS[name],
            seeds,
            action_repeat=int(config["action_repeat"]),
            max_steps=args.max_steps,
        ).to_dict()
        for name in args.agents
    ]
    report = {
        "schema_version": 1,
        "environment_id": config["environment_id"],
        "suite": args.suite,
        "seeds": seeds,
        "results": results,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
