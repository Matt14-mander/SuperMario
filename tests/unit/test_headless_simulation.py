import unittest

from ai_platformer.content.legacy import LegacyLevelRepository
from ai_platformer.core import (
    Action,
    BasicPlatformerCore,
    LevelDefinition,
    SolidRect,
)


def flat_level(
    *,
    level_id: str = "flat",
    width: float = 500.0,
    height: float = 200.0,
    spawn_x: float = 10.0,
    floor_y: float = 100.0,
    goal_x: float = 450.0,
) -> LevelDefinition:
    return LevelDefinition(
        level_id=level_id,
        width=width,
        height=height,
        spawn_x=spawn_x,
        spawn_bottom=floor_y,
        goal_x=goal_x,
        solids=(SolidRect(0.0, floor_y, width, 20.0),),
    )


class HeadlessSimulationTests(unittest.TestCase):
    def test_player_walks_right(self) -> None:
        level = flat_level()
        core = BasicPlatformerCore(lambda _: level)
        start = core.reset(seed=7, level_id=level.level_id)

        for _ in range(20):
            result = core.step(Action.RIGHT)

        self.assertGreater(result.state.player.x, start.player.x)
        self.assertTrue(result.state.player.grounded)
        self.assertFalse(result.terminated)

    def test_player_jumps(self) -> None:
        level = flat_level()
        core = BasicPlatformerCore(lambda _: level)
        start = core.reset(seed=7, level_id=level.level_id)

        result = core.step(Action.RIGHT_JUMP)

        self.assertLess(result.state.player.y, start.player.y)
        self.assertLess(result.state.player.velocity_y, 0.0)
        self.assertFalse(result.state.player.grounded)

    def test_player_dies_after_falling_below_level(self) -> None:
        level = LevelDefinition(
            level_id="pit",
            width=500.0,
            height=100.0,
            spawn_x=10.0,
            spawn_bottom=20.0,
            goal_x=450.0,
            solids=(),
        )
        core = BasicPlatformerCore(lambda _: level)
        core.reset(seed=7, level_id=level.level_id)

        for _ in range(100):
            result = core.step(Action.NOOP)
            if result.terminated:
                break

        self.assertTrue(result.terminated)
        self.assertFalse(result.state.player.alive)
        self.assertEqual(result.info["outcome"], "death")

    def test_reaching_goal_terminates_episode(self) -> None:
        level = flat_level(goal_x=40.0)
        core = BasicPlatformerCore(lambda _: level)
        core.reset(seed=7, level_id=level.level_id)

        for _ in range(30):
            result = core.step(Action.RIGHT_RUN)
            if result.terminated:
                break

        self.assertTrue(result.terminated)
        self.assertEqual(result.info["outcome"], "success")
        self.assertEqual(result.state.progress, 1.0)

    def test_same_seed_and_actions_produce_identical_replay(self) -> None:
        level = flat_level()
        actions = [Action.RIGHT] * 8 + [Action.RIGHT_JUMP] + [Action.RIGHT_JUMP] * 8

        def replay():
            core = BasicPlatformerCore(lambda _: level)
            states = [core.reset(seed=123, level_id=level.level_id)]
            states.extend(core.step(action).state for action in actions)
            return states

        self.assertEqual(replay(), replay())

    def test_legacy_level_one_loads_and_spawns_on_ground(self) -> None:
        repository = LegacyLevelRepository()
        core = BasicPlatformerCore(repository.load)

        state = core.reset(seed=42, level_id="level_1")

        self.assertEqual(state.player.x, 110.0)
        self.assertEqual(state.player.y, 506.0)
        self.assertTrue(state.player.grounded)


if __name__ == "__main__":
    unittest.main()
