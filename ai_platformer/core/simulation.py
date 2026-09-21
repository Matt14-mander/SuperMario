"""First deterministic, headless platformer simulation vertical slice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .actions import Action, Control, control_for
from .engine import StepResult
from .level import LevelDefinition, SolidRect
from .state import PlayerSnapshot, WorldSnapshot


@dataclass(frozen=True, slots=True)
class PhysicsConfig:
    player_width: float = 24.0
    player_height: float = 32.0
    walk_acceleration: float = 0.15
    run_acceleration: float = 0.3
    turn_acceleration: float = 0.35
    max_walk_speed: float = 6.0
    max_run_speed: float = 12.0
    jump_velocity: float = -10.5
    rising_gravity: float = 0.3
    falling_gravity: float = 1.0
    max_fall_speed: float = 11.0
    max_episode_steps: int = 36_000


class BasicPlatformerCore:
    """Deterministic movement, collision, death, and goal simulation."""

    def __init__(
        self,
        level_loader: Callable[[str], LevelDefinition],
        *,
        config: PhysicsConfig | None = None,
    ) -> None:
        self._level_loader = level_loader
        self.config = config or PhysicsConfig()
        self._level: LevelDefinition | None = None
        self._state: WorldSnapshot | None = None
        self._x = 0.0
        self._y = 0.0
        self._velocity_x = 0.0
        self._velocity_y = 0.0
        self._grounded = False
        self._alive = True
        self._facing = 1
        self._tick = 0
        self._seed = 0
        self._episode_id = ""
        self._jump_was_pressed = False

    @property
    def state(self) -> WorldSnapshot:
        if self._state is None:
            raise RuntimeError("reset() must be called before reading state")
        return self._state

    def reset(self, *, seed: int, level_id: str) -> WorldSnapshot:
        self._level = self._level_loader(level_id)
        self._seed = seed
        self._episode_id = f"{level_id}:{seed}"
        self._tick = 0
        self._x = self._level.spawn_x
        self._y = self._level.spawn_bottom - self.config.player_height
        self._velocity_x = 0.0
        self._velocity_y = 0.0
        self._alive = True
        self._facing = 1
        self._jump_was_pressed = False
        self._grounded = self._has_support()
        self._state = self._snapshot()
        return self._state

    def step(self, action: Action) -> StepResult:
        level = self._require_level()
        if not self._alive or self.state.progress >= 1.0:
            raise RuntimeError("episode is finished; call reset() before step()")

        control = control_for(action)
        previous_progress = self.state.progress
        self._tick += 1
        self._update_horizontal_velocity(control)
        self._start_jump(control)
        self._move_horizontal()
        self._apply_vertical_acceleration(control)
        self._move_vertical()

        outcome: str | None = None
        if self._y > level.height:
            self._alive = False
            outcome = "death"

        progress = self._progress()
        if self._alive and progress >= 1.0:
            outcome = "success"

        truncated = self._tick >= self.config.max_episode_steps and outcome is None
        if truncated:
            outcome = "time_limit"

        self._jump_was_pressed = control.jump
        self._state = self._snapshot()
        reward = self._state.progress - previous_progress
        if outcome == "success":
            reward += 1.0
        elif outcome == "death":
            reward -= 1.0

        return StepResult(
            state=self._state,
            reward=reward,
            terminated=outcome in {"success", "death"},
            truncated=truncated,
            info={"outcome": outcome} if outcome else {},
        )

    def _require_level(self) -> LevelDefinition:
        if self._level is None:
            raise RuntimeError("reset() must be called before step()")
        return self._level

    def _update_horizontal_velocity(self, control: Control) -> None:
        if control.horizontal == 0:
            acceleration = self.config.run_acceleration if control.run else self.config.walk_acceleration
            if self._velocity_x > 0:
                self._velocity_x = max(0.0, self._velocity_x - acceleration)
            elif self._velocity_x < 0:
                self._velocity_x = min(0.0, self._velocity_x + acceleration)
            return

        self._facing = control.horizontal
        max_speed = self.config.max_run_speed if control.run else self.config.max_walk_speed
        normal_acceleration = self.config.run_acceleration if control.run else self.config.walk_acceleration
        is_turning = self._velocity_x != 0 and (self._velocity_x > 0) != (control.horizontal > 0)
        acceleration = self.config.turn_acceleration if is_turning else normal_acceleration
        self._velocity_x += control.horizontal * acceleration
        self._velocity_x = max(-max_speed, min(max_speed, self._velocity_x))

    def _start_jump(self, control: Control) -> None:
        if control.jump and not self._jump_was_pressed and self._grounded:
            self._velocity_y = self.config.jump_velocity
            self._grounded = False

    def _apply_vertical_acceleration(self, control: Control) -> None:
        gravity = self.config.rising_gravity if self._velocity_y < 0 and control.jump else self.config.falling_gravity
        self._velocity_y = min(self.config.max_fall_speed, self._velocity_y + gravity)

    def _move_horizontal(self) -> None:
        level = self._require_level()
        self._x += self._velocity_x
        self._x = max(0.0, min(self._x, level.width - self.config.player_width))
        for solid in level.solids:
            if not self._overlaps(solid):
                continue
            if self._velocity_x > 0:
                self._x = solid.x - self.config.player_width
            elif self._velocity_x < 0:
                self._x = solid.right
            self._velocity_x = 0.0

    def _move_vertical(self) -> None:
        previous_y = self._y
        self._y += self._velocity_y
        self._grounded = False
        for solid in self._require_level().solids:
            if not self._overlaps(solid):
                continue
            previous_bottom = previous_y + self.config.player_height
            if self._velocity_y >= 0 and previous_bottom <= solid.y:
                self._y = solid.y - self.config.player_height
                self._velocity_y = 0.0
                self._grounded = True
            elif self._velocity_y < 0 and previous_y >= solid.bottom:
                self._y = solid.bottom
                self._velocity_y = 0.0

        if not self._grounded:
            self._grounded = self._has_support()

    def _has_support(self) -> bool:
        feet = self._y + self.config.player_height
        player_right = self._x + self.config.player_width
        return any(
            abs(feet - solid.y) <= 1e-6
            and self._x < solid.right
            and player_right > solid.x
            for solid in self._require_level().solids
        )

    def _overlaps(self, solid: SolidRect) -> bool:
        return (
            self._x < solid.right
            and self._x + self.config.player_width > solid.x
            and self._y < solid.bottom
            and self._y + self.config.player_height > solid.y
        )

    def _progress(self) -> float:
        level = self._require_level()
        distance = level.goal_x - level.spawn_x
        return max(0.0, min(1.0, (self._x - level.spawn_x) / distance))

    def _snapshot(self) -> WorldSnapshot:
        level = self._require_level()
        return WorldSnapshot(
            episode_id=self._episode_id,
            tick=self._tick,
            level_id=level.level_id,
            seed=self._seed,
            player=PlayerSnapshot(
                x=self._x,
                y=self._y,
                velocity_x=self._velocity_x,
                velocity_y=self._velocity_y,
                grounded=self._grounded,
                alive=self._alive,
                facing=self._facing,
            ),
            progress=self._progress(),
        )
