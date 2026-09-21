"""Minimal level-domain objects consumed by the deterministic core."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SolidRect:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("solid dimensions must be positive")

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


@dataclass(frozen=True, slots=True)
class LevelDefinition:
    level_id: str
    width: float
    height: float
    spawn_x: float
    spawn_bottom: float
    goal_x: float
    solids: tuple[SolidRect, ...]

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("level dimensions must be positive")
        if not 0 <= self.spawn_x < self.width:
            raise ValueError("spawn_x must be inside the level")
        if not self.spawn_x < self.goal_x <= self.width:
            raise ValueError("goal_x must be after the spawn and inside the level")
