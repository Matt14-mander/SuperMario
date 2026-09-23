"""Versioned reward composition for state-based platformer environments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RewardConfig:
    progress_scale: float = 5.0
    coin_reward: float = 0.5
    success_reward: float = 10.0
    death_penalty: float = -10.0
    time_penalty: float = -0.001


def compose_reward(
    *,
    previous_progress: float,
    current_progress: float,
    coin_delta: int,
    outcome: str | None,
    config: RewardConfig,
) -> tuple[float, dict[str, float]]:
    """Return reward and an auditable component breakdown.

    Progress is a potential difference rather than a positive-only delta. Moving
    forward and then backward therefore cannot farm progress reward.
    """

    if coin_delta < 0:
        raise ValueError("coin_delta cannot be negative")
    parts = {
        "progress": (current_progress - previous_progress) * config.progress_scale,
        "coin": coin_delta * config.coin_reward,
        "success": config.success_reward if outcome == "success" else 0.0,
        "death": config.death_penalty if outcome == "death" else 0.0,
        "time": config.time_penalty,
    }
    return float(sum(parts.values())), parts
