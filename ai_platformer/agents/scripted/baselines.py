"""Simple deterministic and stochastic baselines for benchmark calibration."""

from __future__ import annotations

from typing import Protocol

import numpy as np

from ai_platformer.core import Action
from ai_platformer.envs import ObservationIndex


class ScriptedAgent(Protocol):
    def reset(self, *, seed: int) -> None: ...

    def act(self, observation: np.ndarray) -> int: ...


class RandomAgent:
    def __init__(self) -> None:
        self._rng = np.random.default_rng(0)

    def reset(self, *, seed: int) -> None:
        self._rng = np.random.default_rng(seed)

    def act(self, observation: np.ndarray) -> int:
        del observation
        return int(self._rng.integers(0, len(Action)))


class MoveRightAgent:
    def reset(self, *, seed: int) -> None:
        del seed

    def act(self, observation: np.ndarray) -> int:
        del observation
        return int(Action.RIGHT_RUN)


class RuleJumpAgent:
    """Run right and jump when a gap or obstacle enters the look-ahead window."""

    def __init__(self, *, trigger_distance: float = 0.5) -> None:
        self.trigger_distance = trigger_distance

    def reset(self, *, seed: int) -> None:
        del seed

    def act(self, observation: np.ndarray) -> int:
        grounded = observation[ObservationIndex.GROUNDED] > 0.5
        rising = observation[ObservationIndex.VELOCITY_Y] < 0.0
        edge_distance = observation[ObservationIndex.GROUND_EDGE_DISTANCE]
        obstacle_distance = observation[ObservationIndex.OBSTACLE_DISTANCE]
        if not grounded and rising:
            return int(Action.RIGHT_RUN_JUMP)
        if grounded and min(edge_distance, obstacle_distance) <= self.trigger_distance:
            return int(Action.RIGHT_RUN_JUMP)
        return int(Action.RIGHT_RUN)


SCRIPTED_AGENTS = {
    "random": RandomAgent,
    "move-right": MoveRightAgent,
    "rule-jump": RuleJumpAgent,
}
