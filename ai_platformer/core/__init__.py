"""Deterministic game-domain contracts with no rendering dependency."""

from .actions import Action, Control, control_for
from .engine import GameCore, StepResult
from .level import LevelDefinition, SolidRect
from .simulation import BasicPlatformerCore, PhysicsConfig
from .state import EntitySnapshot, PlayerSnapshot, WorldSnapshot

__all__ = [
    "Action",
    "BasicPlatformerCore",
    "Control",
    "EntitySnapshot",
    "GameCore",
    "LevelDefinition",
    "PhysicsConfig",
    "PlayerSnapshot",
    "StepResult",
    "SolidRect",
    "WorldSnapshot",
    "control_for",
]
