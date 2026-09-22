"""Gymnasium state-vector environment backed by the shared game core."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from ai_platformer.content.legacy import LegacyLevelRepository
from ai_platformer.core import Action, BasicPlatformerCore, WorldSnapshot
from ai_platformer.settings import GameplaySettings, load_gameplay_settings


class ObservationIndex(IntEnum):
    """Stable indices of the ``PlatformerState-v0`` observation contract."""

    PLAYER_X = 0
    PLAYER_Y = 1
    VELOCITY_X = 2
    VELOCITY_Y = 3
    GROUNDED = 4
    FACING = 5
    PROGRESS = 6
    GROUND_EDGE_DISTANCE = 7
    OBSTACLE_DISTANCE = 8
    OBSTACLE_HEIGHT = 9
    COIN_DELTA_X = 10
    COIN_DELTA_Y = 11
    COIN_RATIO = 12
    REMAINING_TIME = 13


OBSERVATION_SIZE = len(ObservationIndex)


class PlatformerStateEnv(gym.Env[np.ndarray, int]):
    """Deterministic state observation environment for training and evaluation."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        *,
        level_id: str | None = None,
        seed: int | None = None,
        action_repeat: int = 4,
        sensor_range: float = 240.0,
        settings: GameplaySettings | None = None,
    ) -> None:
        super().__init__()
        if action_repeat <= 0:
            raise ValueError("action_repeat must be positive")
        if sensor_range <= 0:
            raise ValueError("sensor_range must be positive")

        self.settings = settings or load_gameplay_settings()
        self.level_id = level_id or self.settings.level_id
        self.default_seed = self.settings.seed if seed is None else seed
        self.action_repeat = action_repeat
        self.sensor_range = sensor_range
        self.repository = LegacyLevelRepository()
        self.level = self.repository.load(self.level_id)
        self.core = BasicPlatformerCore(self.repository.load, config=self.settings.physics)
        self.action_space = spaces.Discrete(len(Action))
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(OBSERVATION_SIZE,),
            dtype=np.float32,
        )
        self._episode_done = True
        self._episode_return = 0.0

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        actual_seed = self.default_seed if seed is None else seed
        requested_level = (
            self.level_id if options is None else options.get("level_id", self.level_id)
        )
        self.level_id = str(requested_level)
        self.level = self.repository.load(self.level_id)
        state = self.core.reset(seed=actual_seed, level_id=self.level_id)
        self._episode_done = False
        self._episode_return = 0.0
        return self._observation(state), self._info(state, core_ticks=0)

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if self._episode_done:
            raise RuntimeError("episode is finished; call reset() before step()")
        if not self.action_space.contains(action):
            raise ValueError(f"unsupported action id: {action}")

        previous = self.core.state
        previous_coins = int(previous.metadata.get("coins_collected", 0))
        terminated = False
        truncated = False
        core_ticks = 0
        core_info: dict[str, Any] = {}

        for _ in range(self.action_repeat):
            result = self.core.step(Action(int(action)))
            core_ticks += 1
            core_info = dict(result.info)
            terminated = result.terminated
            truncated = result.truncated
            if terminated or truncated:
                break

        state = self.core.state
        progress_reward = (state.progress - previous.progress) * 5.0
        coin_delta = int(state.metadata.get("coins_collected", 0)) - previous_coins
        reward_parts = {
            "progress": progress_reward,
            "coin": coin_delta * 0.5,
            "success": 10.0 if core_info.get("outcome") == "success" else 0.0,
            "death": -10.0 if core_info.get("outcome") == "death" else 0.0,
            "time": -0.001,
        }
        reward = float(sum(reward_parts.values()))
        self._episode_return += reward
        self._episode_done = terminated or truncated

        info = self._info(state, core_ticks=core_ticks)
        info.update(core_info)
        info["reward_components"] = reward_parts
        info["episode_return"] = self._episode_return
        return self._observation(state), reward, terminated, truncated, info

    def render(self) -> None:
        return None

    def close(self) -> None:
        return None

    def _observation(self, state: WorldSnapshot) -> np.ndarray:
        player = state.player
        config = self.settings.physics
        obstacle_distance, obstacle_height = self._obstacle(state)
        coin_dx, coin_dy = self._nearest_coin_delta(state)
        coins_total = int(state.metadata.get("coins_total", 0))
        coins_collected = int(state.metadata.get("coins_collected", 0))
        return np.array(
            [
                self._unit(player.x / self.level.width),
                self._unit(player.y / self.level.height),
                self._signed(player.velocity_x / config.max_run_speed),
                self._signed(
                    player.velocity_y
                    / max(abs(config.jump_velocity), config.max_fall_speed)
                ),
                1.0 if player.grounded else 0.0,
                float(player.facing),
                self._unit(state.progress),
                self._unit(self._ground_edge_distance(state) / self.sensor_range),
                self._unit(obstacle_distance / self.sensor_range),
                self._unit(obstacle_height / (config.player_height * 4.0)),
                self._signed(coin_dx / self.sensor_range),
                self._signed(coin_dy / self.sensor_range),
                self._unit(coins_collected / coins_total if coins_total else 0.0),
                self._unit(1.0 - state.tick / config.max_episode_steps),
            ],
            dtype=np.float32,
        )

    def _ground_edge_distance(self, state: WorldSnapshot) -> float:
        player = state.player
        feet = player.y + self.settings.physics.player_height
        cursor = player.x + self.settings.physics.player_width
        intervals = sorted(
            (solid.x, solid.right)
            for solid in self.level.solids
            if abs(solid.y - feet) <= 1e-5 and solid.right >= cursor
        )
        limit = cursor
        for start, end in intervals:
            if start > limit + 1e-5:
                break
            if end > limit:
                limit = end
        return min(self.sensor_range, max(0.0, limit - cursor))

    def _obstacle(self, state: WorldSnapshot) -> tuple[float, float]:
        player = state.player
        player_right = player.x + self.settings.physics.player_width
        player_bottom = player.y + self.settings.physics.player_height
        candidates = [
            solid
            for solid in self.level.solids
            if solid.right >= player_right
            and solid.x >= player_right - 1e-5
            and solid.y < player_bottom - 1e-5
            and solid.bottom > player.y
        ]
        if not candidates:
            return self.sensor_range, 0.0
        obstacle = min(candidates, key=lambda solid: solid.x)
        return (
            min(self.sensor_range, max(0.0, obstacle.x - player_right)),
            max(0.0, player_bottom - obstacle.y),
        )

    def _nearest_coin_delta(self, state: WorldSnapshot) -> tuple[float, float]:
        active = [entity for entity in state.entities if entity.active and entity.kind == "coin"]
        if not active:
            return self.sensor_range, 0.0
        player = state.player
        coin = min(active, key=lambda item: (item.x - player.x) ** 2 + (item.y - player.y) ** 2)
        return coin.x - player.x, coin.y - player.y

    def _info(self, state: WorldSnapshot, *, core_ticks: int) -> dict[str, Any]:
        return {
            "level_id": state.level_id,
            "seed": state.seed,
            "tick": state.tick,
            "core_ticks": core_ticks,
            "progress": state.progress,
            "score": int(state.metadata.get("score", 0)),
            "coins_collected": int(state.metadata.get("coins_collected", 0)),
            "coins_total": int(state.metadata.get("coins_total", 0)),
        }

    @staticmethod
    def _unit(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _signed(value: float) -> float:
        return max(-1.0, min(1.0, value))
