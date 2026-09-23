"""Gymnasium adapters around :mod:`ai_platformer.core`."""

from gymnasium.envs.registration import register, registry

from .platformer_state import OBSERVATION_SIZE, ObservationIndex, PlatformerStateEnv
from .reward import RewardConfig, compose_reward

ENV_ID = "PlatformerState-v0"

if ENV_ID not in registry:
    register(id=ENV_ID, entry_point="ai_platformer.envs:PlatformerStateEnv")

__all__ = [
    "ENV_ID",
    "OBSERVATION_SIZE",
    "ObservationIndex",
    "PlatformerStateEnv",
    "RewardConfig",
    "compose_reward",
]
