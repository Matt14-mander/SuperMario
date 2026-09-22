import json
import tempfile
import unittest
from pathlib import Path

from ai_platformer.settings import load_gameplay_settings


class GameplaySettingsTests(unittest.TestCase):
    def test_project_settings_load(self) -> None:
        settings = load_gameplay_settings()

        self.assertEqual(settings.schema_version, 1)
        self.assertEqual(settings.level_id, "level_1")
        self.assertEqual(settings.render_fps, 60)
        self.assertEqual(settings.physics.max_episode_steps, 36_000)

    def test_unknown_schema_version_is_rejected(self) -> None:
        data = {
            "schema_version": 99,
            "level_id": "level_1",
            "seed": 0,
            "render_fps": 60,
            "terminal_display_ms": 1000,
            "physics": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_gameplay_settings(path)


if __name__ == "__main__":
    unittest.main()
