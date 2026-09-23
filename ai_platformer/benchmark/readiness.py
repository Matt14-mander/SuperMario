"""Automated RL-readiness gates and reward exploit audits."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from math import isclose
from typing import Any

import numpy as np

from ai_platformer.agents.scripted import RuleJumpAgent
from ai_platformer.core import Action
from ai_platformer.envs import PlatformerStateEnv


@dataclass(frozen=True, slots=True)
class StabilityReport:
    episodes: int
    transitions: int
    max_steps_per_episode: int
    base_seed: int
    outcomes: dict[str, int]
    min_reward: float
    max_reward: float


@dataclass(frozen=True, slots=True)
class RewardAuditReport:
    passed: bool
    noop_return: float
    jump_in_place_return: float
    loop_return: float
    loop_progress_reward: float
    expected_loop_progress_reward: float
    duplicate_collectibles: tuple[str, ...]
    death_return: float
    success_return: float
    checks: dict[str, bool]


def run_sb3_checker() -> str:
    from stable_baselines3 import __version__ as sb3_version
    from stable_baselines3.common.env_checker import check_env

    env = PlatformerStateEnv(episode_step_limit=256)
    try:
        check_env(env, warn=True)
    finally:
        env.close()
    return sb3_version


def run_random_stability_gate(
    *,
    episodes: int = 1_000,
    max_steps_per_episode: int = 256,
    base_seed: int = 20_260_923,
) -> StabilityReport:
    if episodes <= 0 or max_steps_per_episode <= 0:
        raise ValueError("episodes and max_steps_per_episode must be positive")
    env = PlatformerStateEnv(episode_step_limit=max_steps_per_episode)
    outcomes: Counter[str] = Counter()
    transitions = 0
    min_reward = float("inf")
    max_reward = float("-inf")
    try:
        for episode in range(episodes):
            seed = base_seed + episode
            rng = np.random.default_rng(seed)
            observation, _ = env.reset(seed=seed)
            _assert_observation(env, observation)
            terminated = truncated = False
            info: dict[str, Any] = {}
            while not (terminated or truncated):
                action = int(rng.integers(env.action_space.n))
                observation, reward, terminated, truncated, info = env.step(action)
                transitions += 1
                _assert_observation(env, observation)
                if not np.isfinite(reward):
                    raise AssertionError("non-finite reward encountered")
                if not isclose(
                    reward,
                    sum(info["reward_components"].values()),
                    abs_tol=1e-9,
                ):
                    raise AssertionError("reward does not match component breakdown")
                min_reward = min(min_reward, reward)
                max_reward = max(max_reward, reward)
            outcomes[str(info.get("outcome", "unknown"))] += 1
    finally:
        env.close()
    return StabilityReport(
        episodes=episodes,
        transitions=transitions,
        max_steps_per_episode=max_steps_per_episode,
        base_seed=base_seed,
        outcomes=dict(sorted(outcomes.items())),
        min_reward=min_reward,
        max_reward=max_reward,
    )


def run_reward_exploit_audit() -> RewardAuditReport:
    noop = _rollout_fixed([Action.NOOP], 256)
    jump = _rollout_fixed([Action.JUMP, Action.NOOP], 256)
    loop_actions = [Action.RIGHT_RUN] * 12 + [Action.LEFT_RUN] * 24
    loop = _rollout_fixed(loop_actions, 360)
    expected_progress = loop["final_progress"] * 5.0

    death = _rollout_agent(RuleJumpAgent(trigger_distance=0.34), 1_000)
    success = _rollout_agent(RuleJumpAgent(), 1_000)
    duplicates = tuple(sorted(loop["duplicate_collectibles"]))
    checks = {
        "noop_cannot_profit": noop["return"] < 0.0,
        "jump_in_place_cannot_profit": jump["return"] < 0.0,
        "progress_is_path_independent": isclose(
            loop["components"]["progress"], expected_progress, abs_tol=1e-9
        ),
        "coins_are_one_shot": not duplicates,
        "death_is_penalized": death["outcome"] == "death"
        and death["terminal_components"]["death"] < 0.0,
        "success_is_rewarded": success["outcome"] == "success"
        and success["terminal_components"]["success"] > 0.0,
    }
    return RewardAuditReport(
        passed=all(checks.values()),
        noop_return=noop["return"],
        jump_in_place_return=jump["return"],
        loop_return=loop["return"],
        loop_progress_reward=loop["components"]["progress"],
        expected_loop_progress_reward=expected_progress,
        duplicate_collectibles=duplicates,
        death_return=death["return"],
        success_return=success["return"],
        checks=checks,
    )


def readiness_report(
    *,
    episodes: int = 1_000,
    max_steps_per_episode: int = 256,
    base_seed: int = 20_260_923,
) -> dict[str, Any]:
    sb3_version = run_sb3_checker()
    stability = run_random_stability_gate(
        episodes=episodes,
        max_steps_per_episode=max_steps_per_episode,
        base_seed=base_seed,
    )
    reward = run_reward_exploit_audit()
    return {
        "schema_version": 1,
        "passed": reward.passed and stability.episodes == episodes,
        "sb3_checker": {"passed": True, "version": sb3_version},
        "stability": asdict(stability),
        "reward_audit": asdict(reward),
    }


def _rollout_fixed(actions: list[Action], steps: int) -> dict[str, Any]:
    env = PlatformerStateEnv(episode_step_limit=steps)
    observation, _ = env.reset(seed=123)
    return _rollout(
        env,
        lambda index, _: int(actions[index % len(actions)]),
        steps,
        observation,
    )


def _rollout_agent(agent: RuleJumpAgent, steps: int) -> dict[str, Any]:
    env = PlatformerStateEnv(episode_step_limit=steps)
    observation, _ = env.reset(seed=123)
    agent.reset(seed=123)
    return _rollout(env, lambda _, obs: agent.act(obs), steps, observation)


def _rollout(env, policy, steps: int, observation=None) -> dict[str, Any]:
    if observation is None:
        raise ValueError("an initial observation is required")
    total = 0.0
    components: Counter[str] = Counter()
    collected: set[str] = set()
    duplicates: set[str] = set()
    info: dict[str, Any] = {}
    terminal_components: dict[str, float] = {}
    try:
        for index in range(steps):
            observation, reward, terminated, truncated, info = env.step(
                policy(index, observation)
            )
            total += reward
            components.update(info["reward_components"])
            for entity_id in info.get("collected", ()):
                if entity_id in collected:
                    duplicates.add(entity_id)
                collected.add(entity_id)
            if terminated or truncated:
                terminal_components = dict(info["reward_components"])
                break
    finally:
        env.close()
    return {
        "return": total,
        "components": dict(components),
        "final_progress": float(info["progress"]),
        "duplicate_collectibles": duplicates,
        "outcome": info.get("outcome"),
        "terminal_components": terminal_components,
    }


def _assert_observation(env: PlatformerStateEnv, observation: np.ndarray) -> None:
    if not env.observation_space.contains(observation):
        raise AssertionError("observation escaped declared space")
    if not np.all(np.isfinite(observation)):
        raise AssertionError("non-finite observation encountered")
