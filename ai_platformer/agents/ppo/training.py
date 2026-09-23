"""Reproducible Stable-Baselines3 PPO training for PlatformerState-v0."""

from __future__ import annotations

import json
import platform
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
import torch
from stable_baselines3 import PPO, __version__ as sb3_version
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.vec_env import DummyVecEnv

from ai_platformer.core import Action
from ai_platformer.envs import OBSERVATION_SIZE, PlatformerStateEnv


@dataclass(frozen=True, slots=True)
class PolicyEpisode:
    seed: int
    episode_return: float
    steps: int
    progress: float
    coins_collected: int
    outcome: str


def train_ppo(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Train, evaluate, save, and describe one PPO baseline run."""

    seed = int(config["seed"])
    torch.set_num_threads(int(config.get("torch_threads", 1)))
    set_random_seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    monitor_dir = output_dir / "monitor"
    monitor_dir.mkdir(exist_ok=True)

    env = _training_env(config, monitor_dir)
    policy_kwargs = {
        "activation_fn": torch.nn.ReLU,
        "net_arch": {
            "pi": list(config["network"]["policy_layers"]),
            "vf": list(config["network"]["value_layers"]),
        },
    }
    algorithm = config["algorithm"]
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=float(algorithm["learning_rate"]),
        n_steps=int(algorithm["n_steps"]),
        batch_size=int(algorithm["batch_size"]),
        n_epochs=int(algorithm["n_epochs"]),
        gamma=float(algorithm["gamma"]),
        gae_lambda=float(algorithm["gae_lambda"]),
        clip_range=float(algorithm["clip_range"]),
        ent_coef=float(algorithm["ent_coef"]),
        vf_coef=float(algorithm["vf_coef"]),
        policy_kwargs=policy_kwargs,
        seed=seed,
        device=str(config.get("device", "cpu")),
        verbose=int(config.get("verbose", 1)),
    )
    try:
        model.learn(total_timesteps=int(config["total_timesteps"]), progress_bar=False)
        model_path = output_dir / "model"
        model.save(model_path)
        evaluation = evaluate_policy(
            model,
            seeds=[int(item) for item in config["evaluation"]["seeds"]],
            action_repeat=int(config["environment"]["action_repeat"]),
            episode_step_limit=int(config["environment"]["episode_step_limit"]),
        )
    finally:
        env.close()

    report = {
        "schema_version": 1,
        "environment_id": "PlatformerState-v0",
        "observation_size": OBSERVATION_SIZE,
        "action_ids": {action.name: int(action) for action in Action},
        "config": config,
        "runtime": {
            "python": platform.python_version(),
            "stable_baselines3": sb3_version,
            "torch": torch.__version__,
            "numpy": np.__version__,
        },
        "trained_timesteps": int(model.num_timesteps),
        "evaluation": evaluation,
        "artifacts": {
            "model": str((output_dir / "model.zip").resolve()),
            "monitor": str(monitor_dir.resolve()),
        },
    }
    (output_dir / "run.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def evaluate_policy(
    model: PPO,
    *,
    seeds: list[int],
    action_repeat: int,
    episode_step_limit: int,
) -> dict[str, Any]:
    episodes: list[PolicyEpisode] = []
    env = PlatformerStateEnv(
        action_repeat=action_repeat,
        episode_step_limit=episode_step_limit,
    )
    try:
        for seed in seeds:
            observation, info = env.reset(seed=seed)
            total_reward = 0.0
            terminated = truncated = False
            steps = 0
            while not (terminated or truncated):
                action, _ = model.predict(observation, deterministic=True)
                observation, reward, terminated, truncated, info = env.step(int(action))
                total_reward += reward
                steps += 1
            episodes.append(
                PolicyEpisode(
                    seed=seed,
                    episode_return=total_reward,
                    steps=steps,
                    progress=float(info["progress"]),
                    coins_collected=int(info["coins_collected"]),
                    outcome=str(info.get("outcome", "unknown")),
                )
            )
    finally:
        env.close()
    return {
        "summary": {
            "episodes": len(episodes),
            "success_rate": sum(item.outcome == "success" for item in episodes)
            / len(episodes),
            "mean_return": mean(item.episode_return for item in episodes),
            "mean_progress": mean(item.progress for item in episodes),
            "mean_steps": mean(item.steps for item in episodes),
        },
        "episodes": [asdict(episode) for episode in episodes],
    }


def _training_env(config: dict[str, Any], monitor_dir: Path) -> DummyVecEnv:
    seed = int(config["seed"])
    environment = config["environment"]

    def factory(rank: int):
        def make():
            env = PlatformerStateEnv(
                seed=seed + rank,
                action_repeat=int(environment["action_repeat"]),
                episode_step_limit=int(environment["episode_step_limit"]),
            )
            return Monitor(env, filename=str(monitor_dir / f"env_{rank}"))

        return make

    return DummyVecEnv([factory(rank) for rank in range(int(config["n_envs"]))])
