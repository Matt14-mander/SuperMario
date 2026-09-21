from ..components import info
import pygame

class LoadScreen:
    def __init__(self):
        self.finished = False
        self.next = 'level'
        self.duration = 2000
        self.timer = 0
        self.info = info.Info('load_screen')

    def enter(self):
        self.finished = False
        self.timer = 0

    def is_finished(self):
        return self.finished
    def update(self, surface, keys):
        self.draw(surface)
        if self.timer == 0:
            self.timer = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - self.timer > self.duration:
            self.finished = True
            # print(self.finished)
            self.timer = 0



    def draw(self, surface):
        surface.fill((0, 0, 0))
        self.info.draw(surface)

class GameOver(LoadScreen):
    def __init__(self):
        LoadScreen.__init__(self)
        self.next = 'main_menu'
        self.duration = 4000
        self.timer = 0
        self.info = info.Info('game_over')

class LevelComplete(LoadScreen):
    def __init__(self):
        LoadScreen.__init__(self)
        self.next = 'main_menu'
        self.duration = 2500
        self.timer = 0
        self.info = info.Info('level_complete')
