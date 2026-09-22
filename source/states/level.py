"""Playable Pygame state backed by the deterministic shared core."""

import pygame

from ai_platformer.content.legacy import LegacyLevelRepository
from ai_platformer.core import BasicPlatformerCore
from ai_platformer.rendering.keyboard import PygameKeyboardController
from ai_platformer.rendering.pygame_level import PygameLevelRenderer
from ai_platformer.settings import GameplaySettings, load_gameplay_settings
from source import constants as C
from source import setup
from source.components import info


class Level:
    def __init__(self, settings: GameplaySettings | None = None):
        self.settings = settings or load_gameplay_settings()
        self.finished = False
        self.next = 'game_over'
        self.info = info.Info('level')
        self.repository = LegacyLevelRepository()
        self.level_definition = self.repository.load(self.settings.level_id)
        self.core = BasicPlatformerCore(
            self.repository.load,
            config=self.settings.physics,
        )
        self.controller = PygameKeyboardController()
        self.renderer = self._create_renderer()
        self.state = None
        self.outcome = None
        self.terminal_timer = None
        self.paused = False
        self.enter()

    def _create_renderer(self):
        background = setup.GRAPHICS[self.settings.level_id]
        rect = background.get_rect()
        background = pygame.transform.scale(
            background,
            (int(rect.width * C.BG_MULTI), int(rect.height * C.BG_MULTI)),
        )
        return PygameLevelRenderer(
            background=background,
            player_sheet=setup.GRAPHICS['mario_bros'],
            item_sheet=setup.GRAPHICS['item_objects'],
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
        self.paused = False
        self.state = self.core.reset(
            seed=self.settings.seed,
            level_id=self.settings.level_id,
        )
        self.renderer.reset()

    def is_finished(self):
        return self.finished

    def update(self, surface, keys):
        current_time = pygame.time.get_ticks()
        was_pressed = getattr(keys, 'was_pressed', lambda _key: False)
        if was_pressed(pygame.K_r):
            self.enter()
            self.info.update()
            self.draw(surface)
            return
        if was_pressed(pygame.K_p) or was_pressed(pygame.K_ESCAPE):
            self.paused = not self.paused

        if self.outcome is None and not self.paused:
            action = self.controller.action(keys)
            result = self.core.step(action)
            self.state = result.state
            if result.terminated or result.truncated:
                self.outcome = result.info.get('outcome', 'time_limit')
                self.terminal_timer = current_time
        elif (
            self.outcome is not None
            and current_time - self.terminal_timer >= self.settings.terminal_display_ms
        ):
            self.next = 'level_complete' if self.outcome == 'success' else 'game_over'
            self.finished = True

        self.info.update()
        self.draw(surface)

    def draw(self, surface):
        self.renderer.draw(surface, self.state)
        self.info.draw(surface, self.state)
        if self.paused:
            self.renderer.draw_pause(surface)
