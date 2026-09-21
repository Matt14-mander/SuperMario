"""Port implemented by the deterministic game simulation."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

from .actions import Action
from .state import WorldSnapshot


@dataclass(frozen=True, slots=True)
class StepResult:
    """One simulation transition using Gymnasium-compatible episode semantics."""

    state: WorldSnapshot
    reward: float
    terminated: bool
    truncated: bool
    info: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class GameCore(Protocol):
    """Boundary shared by keyboard play, training, replay, and benchmarks."""

    @property
    def state(self) -> WorldSnapshot:
        """Return the current immutable world snapshot."""

    def reset(self, *, seed: int, level_id: str) -> WorldSnapshot:
        """Start a deterministic episode."""

    def step(self, action: Action) -> StepResult:
        """Advance exactly one fixed simulation tick."""
