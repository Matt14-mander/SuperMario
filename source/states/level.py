"""Playable Pygame state backed by the deterministic shared core."""

import pygame

from ai_platformer.content.legacy import LegacyLevelRepository
from ai_platformer.core import BasicPlatformerCore
from ai_platformer.rendering.keyboard import PygameKeyboardController
from ai_platformer.rendering.pygame_level import PygameLevelRenderer
from source import constants as C
from source import setup
from source.components import info


class Level:
    LEVEL_ID = 'level_1'
    TERMINAL_DISPLAY_MS = 1000

    def __init__(self):
        self.finished = False
        self.next = 'game_over'
        self.info = info.Info('level')
        self.repository = LegacyLevelRepository()
        self.level_definition = self.repository.load(self.LEVEL_ID)
        self.core = BasicPlatformerCore(self.repository.load)
        self.controller = PygameKeyboardController()
        self.renderer = self._create_renderer()
        self.state = None
        self.outcome = None
        self.terminal_timer = None
        self.enter()

    def _create_renderer(self):
        background = setup.GRAPHICS['level_1']
        rect = background.get_rect()
        background = pygame.transform.scale(
            background,
            (int(rect.width * C.BG_MULTI), int(rect.height * C.BG_MULTI)),
        )
        return PygameLevelRenderer(
            background=background,
            player_sheet=setup.GRAPHICS['mario_bros'],
            screen_size=setup.SCREEN.get_size(),
            level_width=self.level_definition.width,
            scale=C.PLAYER_MULTI,
        )

    def enter(self):
        """Start a fresh episode every time the state becomes active."""

        self.finished = False
        self.next = 'game_over'
        self.outcome = None
        self.terminal_timer = None
        self.state = self.core.reset(seed=0, level_id=self.LEVEL_ID)
        self.renderer.reset()

    def is_finished(self):
        return self.finished

    def update(self, surface, keys):
        current_time = pygame.time.get_ticks()
        if self.outcome is None:
            action = self.controller.action(keys)
            result = self.core.step(action)
            self.state = result.state
            if result.terminated or result.truncated:
                self.outcome = result.info.get('outcome', 'time_limit')
                self.terminal_timer = current_time
        elif current_time - self.terminal_timer >= self.TERMINAL_DISPLAY_MS:
            self.next = 'level_complete' if self.outcome == 'success' else 'game_over'
            self.finished = True

        self.info.update()
        self.draw(surface)

    def draw(self, surface):
        self.renderer.draw(surface, self.state)
        self.info.draw(surface)
