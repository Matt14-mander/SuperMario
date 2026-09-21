import os
import unittest
from collections import defaultdict

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame
except ModuleNotFoundError:  # Local headless-only environments may omit Pygame.
    pygame = None


@unittest.skipIf(pygame is None, "Pygame is not installed")
class SharedCorePygameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from source import setup
        from source.states.level import Level

        cls.surface = setup.SCREEN
        cls.level_type = Level

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def keys(self, *pressed_keys):
        values = defaultdict(bool)
        for key in pressed_keys:
            values[key] = True
        return values

    def test_keyboard_drives_shared_core(self) -> None:
        level = self.level_type()
        start = level.state

        for _ in range(60):
            level.update(self.surface, self.keys(pygame.K_RIGHT))

        self.assertGreater(level.state.player.x, start.player.x)
        self.assertEqual(level.state.tick, 60)

    def test_jump_and_run_are_mapped_to_core_action(self) -> None:
        level = self.level_type()
        start_y = level.state.player.y

        level.update(
            self.surface,
            self.keys(pygame.K_RIGHT, pygame.K_SPACE, pygame.K_LSHIFT),
        )

        self.assertLess(level.state.player.y, start_y)
        self.assertLess(level.state.player.velocity_y, 0.0)
        self.assertGreater(level.state.player.velocity_x, 0.0)

    def test_enter_starts_a_fresh_episode(self) -> None:
        level = self.level_type()
        for _ in range(60):
            level.update(self.surface, self.keys(pygame.K_RIGHT))
        self.assertGreater(level.state.tick, 0)
        self.assertGreater(level.renderer.camera_x, 0.0)

        level.enter()

        self.assertEqual(level.state.tick, 0)
        self.assertEqual(level.state.player.x, 110.0)
        self.assertEqual(level.renderer.camera_x, 0.0)
        self.assertIsNone(level.outcome)

    def test_terminal_outcome_routes_to_correct_screen(self) -> None:
        level = self.level_type()
        level.outcome = "success"
        level.terminal_timer = pygame.time.get_ticks() - level.TERMINAL_DISPLAY_MS

        level.update(self.surface, self.keys())

        self.assertTrue(level.finished)
        self.assertEqual(level.next, "level_complete")


if __name__ == "__main__":
    unittest.main()
