"""Reproducible evaluation loop for scripted agents."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from typing import Any

from ai_platformer.agents.scripted import ScriptedAgent
from ai_platformer.envs import PlatformerStateEnv


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    seed: int
    episode_return: float
    steps: int
    core_ticks: int
    progress: float
    coins_collected: int
    outcome: str


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    agent: str
    episodes: tuple[EpisodeResult, ...]

    def summary(self) -> dict[str, Any]:
        count = len(self.episodes)
        outcomes = Counter(episode.outcome for episode in self.episodes)
        return {
            "agent": self.agent,
            "episodes": count,
            "success_rate": outcomes["success"] / count,
            "death_rate": outcomes["death"] / count,
            "truncation_rate": (outcomes["time_limit"] + outcomes["benchmark_limit"]) / count,
            "mean_return": sum(item.episode_return for item in self.episodes) / count,
            "mean_progress": sum(item.progress for item in self.episodes) / count,
            "mean_steps": sum(item.steps for item in self.episodes) / count,
            "mean_coins": sum(item.coins_collected for item in self.episodes) / count,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "episodes": [asdict(episode) for episode in self.episodes],
        }


def evaluate_scripted_agent(
    agent_name: str,
    agent_factory: Callable[[], ScriptedAgent],
    seeds: Iterable[int],
    *,
    action_repeat: int = 4,
    max_steps: int | None = None,
) -> BenchmarkResult:
    episodes: list[EpisodeResult] = []
    env = PlatformerStateEnv(action_repeat=action_repeat)
    try:
        for seed in seeds:
            agent = agent_factory()
            agent.reset(seed=seed)
            observation, info = env.reset(seed=seed)
            episode_return = 0.0
            steps = 0
            terminated = truncated = False
            while not (terminated or truncated):
                observation, reward, terminated, truncated, info = env.step(
                    agent.act(observation)
                )
                episode_return += reward
                steps += 1
                if max_steps is not None and steps >= max_steps and not terminated:
                    truncated = True
                    info = dict(info)
                    info["outcome"] = "benchmark_limit"

            fallback_outcome = (
                "success" if terminated and info["progress"] >= 1.0 else "unknown"
            )
            outcome = str(info.get("outcome", fallback_outcome))
            episodes.append(
                EpisodeResult(
                    seed=seed,
                    episode_return=episode_return,
                    steps=steps,
                    core_ticks=int(info["tick"]),
                    progress=float(info["progress"]),
                    coins_collected=int(info["coins_collected"]),
                    outcome=outcome,
                )
            )
    finally:
        env.close()
    if not episodes:
        raise ValueError("at least one benchmark seed is required")
    return BenchmarkResult(agent=agent_name, episodes=tuple(episodes))
