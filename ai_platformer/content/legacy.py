"""Read-only adapter from the original map JSON to the new core model."""

from __future__ import annotations

import json
from pathlib import Path

from ai_platformer.core.level import LevelDefinition, SolidRect


class LegacyLevelRepository:
    """Load legacy maps without leaking their JSON shape into the core."""

    def __init__(self, maps_directory: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.maps_directory = maps_directory or project_root / "source" / "data" / "maps"

    def load(self, level_id: str) -> LevelDefinition:
        path = self.maps_directory / f"{level_id}.json"
        if not path.is_file():
            raise KeyError(f"unknown legacy level: {level_id}")

        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)

        maps = data.get("maps")
        if not maps:
            raise ValueError(f"legacy level has no spawn metadata: {path}")
        initial_map = maps[0]
        width = float(initial_map["end_x"])
        solids = tuple(
            SolidRect(
                x=float(item["x"]),
                y=float(item["y"]),
                width=float(item["width"]),
                height=float(item["height"]),
            )
            for group in ("ground", "pipe", "step")
            for item in data.get(group, ())
        )
        flagpoles = data.get("flagpole", ())
        goal_x = float(flagpoles[0]["x"]) if flagpoles else width
        return LevelDefinition(
            level_id=level_id,
            width=width,
            height=600.0,
            spawn_x=float(initial_map["player_x"]),
            spawn_bottom=float(initial_map["player_y"]),
            goal_x=goal_x,
            solids=solids,
        )
