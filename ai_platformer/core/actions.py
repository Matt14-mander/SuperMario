"""Shared action vocabulary for humans and autonomous agents."""

from dataclasses import dataclass
from enum import IntEnum


class Action(IntEnum):
    """Stable discrete action IDs used by replays, Gymnasium, and exported models."""

    NOOP = 0
    LEFT = 1
    RIGHT = 2
    JUMP = 3
    LEFT_JUMP = 4
    RIGHT_JUMP = 5
    RIGHT_RUN = 6


@dataclass(frozen=True, slots=True)
class Control:
    """Engine-level controls after decoding a discrete action."""

    horizontal: int = 0
    jump: bool = False
    run: bool = False

    def __post_init__(self) -> None:
        if self.horizontal not in (-1, 0, 1):
            raise ValueError("horizontal must be -1, 0, or 1")


_ACTION_CONTROLS: dict[Action, Control] = {
    Action.NOOP: Control(),
    Action.LEFT: Control(horizontal=-1),
    Action.RIGHT: Control(horizontal=1),
    Action.JUMP: Control(jump=True),
    Action.LEFT_JUMP: Control(horizontal=-1, jump=True),
    Action.RIGHT_JUMP: Control(horizontal=1, jump=True),
    Action.RIGHT_RUN: Control(horizontal=1, run=True),
}


def control_for(action: Action | int) -> Control:
    """Decode a stable action ID into controls understood by the game core."""

    try:
        normalized = Action(action)
    except ValueError as exc:
        raise ValueError(f"unsupported action id: {action}") from exc
    return _ACTION_CONTROLS[normalized]
