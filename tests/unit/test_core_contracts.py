import unittest

from ai_platformer.core import Action, PlayerSnapshot, WorldSnapshot, control_for


class ActionContractTests(unittest.TestCase):
    def test_action_ids_are_stable(self) -> None:
        self.assertEqual(Action.NOOP.value, 0)
        self.assertEqual(Action.RIGHT_RUN.value, 6)
        self.assertEqual(Action.LEFT_RUN.value, 7)
        self.assertEqual(Action.LEFT_RUN_JUMP.value, 8)
        self.assertEqual(Action.RIGHT_RUN_JUMP.value, 9)

    def test_combined_action_decodes_to_control(self) -> None:
        control = control_for(Action.LEFT_JUMP)
        self.assertEqual(control.horizontal, -1)
        self.assertTrue(control.jump)
        self.assertFalse(control.run)

    def test_unknown_action_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            control_for(99)

    def test_run_jump_action_preserves_all_controls(self) -> None:
        control = control_for(Action.RIGHT_RUN_JUMP)
        self.assertEqual(control.horizontal, 1)
        self.assertTrue(control.jump)
        self.assertTrue(control.run)


class SnapshotContractTests(unittest.TestCase):
    def test_world_progress_is_bounded(self) -> None:
        player = PlayerSnapshot(0, 0, 0, 0, grounded=True)
        with self.assertRaises(ValueError):
            WorldSnapshot(
                episode_id="test",
                tick=0,
                level_id="level-1",
                seed=7,
                player=player,
                progress=1.1,
            )


if __name__ == "__main__":
    unittest.main()
