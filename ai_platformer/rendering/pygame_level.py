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
        item_sheet: pygame.Surface,
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
        self.coin_frames = self._coin_images(item_sheet)
        self.pause_font = pygame.font.Font(None, 54)

    @staticmethod
    def _player_image(sheet: pygame.Surface, scale: float) -> pygame.Surface:
        image = pygame.Surface((12, 16))
        image.blit(sheet, (0, 0), (178, 32, 12, 16))
        image.set_colorkey((0, 0, 0))
        return pygame.transform.scale(image, (int(12 * scale), int(16 * scale)))

    @staticmethod
    def _coin_images(sheet: pygame.Surface) -> tuple[pygame.Surface, ...]:
        frames = []
        for x in (1, 9, 17, 9):
            image = pygame.Surface((5, 8))
            image.blit(sheet, (0, 0), (x, 160, 5, 8))
            image.set_colorkey((0, 0, 0))
            frames.append(pygame.transform.scale(image, (14, 22)))
        return tuple(frames)

    def reset(self) -> None:
        self.camera_x = 0.0

    def draw(self, surface: pygame.Surface, state: WorldSnapshot) -> None:
        self._update_camera(state)
        camera_x = int(self.camera_x)
        viewport = pygame.Rect(camera_x, 0, self.screen_width, self.screen_height)
        surface.blit(self.background, (0, 0), viewport)

        coin_image = self.coin_frames[(state.tick // 8) % len(self.coin_frames)]
        for entity in state.entities:
            if entity.active and entity.kind == "coin":
                surface.blit(coin_image, (int(entity.x - self.camera_x), int(entity.y)))

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

    def draw_pause(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        surface.blit(overlay, (0, 0))
        label = self.pause_font.render("PAUSED", True, (255, 255, 255))
        rect = label.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        surface.blit(label, rect)
