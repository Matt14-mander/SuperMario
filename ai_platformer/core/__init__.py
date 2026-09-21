"""Deterministic game-domain contracts with no rendering dependency."""

from .actions import Action, Control, control_for
from .engine import GameCore, StepResult
from .state import EntitySnapshot, PlayerSnapshot, WorldSnapshot

__all__ = [
    "Action",
    "Control",
    "EntitySnapshot",
    "GameCore",
    "PlayerSnapshot",
    "StepResult",
    "WorldSnapshot",
    "control_for",
]
