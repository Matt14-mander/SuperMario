"""Pygame view for renderer-independent world snapshots."""

from __future__ import annotations

import pygame

from ai_platformer.core import WorldSnapshot


class PygameLevelRenderer:
    def __init__(
        self,
        *,
        background: pygame.Surface,
        player_sheet: pygame.Surface,
        screen_size: tuple[int, int],
        level_width: float,
        scale: float = 2.0,
    ) -> None:
        self.background = background
        self.screen_width, self.screen_height = screen_size
        self.level_width = level_width
        self.camera_x = 0.0
        self.player_right = self._player_image(player_sheet, scale)
        self.player_left = pygame.transform.flip(self.player_right, True, False)

    @staticmethod
    def _player_image(sheet: pygame.Surface, scale: float) -> pygame.Surface:
        image = pygame.Surface((12, 16))
        image.blit(sheet, (0, 0), (178, 32, 12, 16))
        image.set_colorkey((0, 0, 0))
        return pygame.transform.scale(image, (int(12 * scale), int(16 * scale)))

    def reset(self) -> None:
        self.camera_x = 0.0

    def draw(self, surface: pygame.Surface, state: WorldSnapshot) -> None:
        self._update_camera(state)
        camera_x = int(self.camera_x)
        viewport = pygame.Rect(camera_x, 0, self.screen_width, self.screen_height)
        surface.blit(self.background, (0, 0), viewport)

        player_image = self.player_right if state.player.facing > 0 else self.player_left
        player_position = (int(state.player.x - self.camera_x), int(state.player.y))
        surface.blit(player_image, player_position)

    def _update_camera(self, state: WorldSnapshot) -> None:
        follow_line = self.screen_width / 3
        player_screen_x = state.player.x - self.camera_x
        if player_screen_x > follow_line:
            self.camera_x = state.player.x - follow_line

        max_camera = max(0.0, self.level_width - self.screen_width)
        self.camera_x = max(0.0, min(max_camera, self.camera_x))
