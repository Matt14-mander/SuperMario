import os

import pygame
import random


class Game:
    def __init__(self, state_dict, start_state):
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.keys = pygame.key.get_pressed()
        # print("Current Keys:", self.keys)
        self.key_states = {
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_RETURN: False,
        }
        self.state_dict = state_dict
        self.state = self.state_dict[start_state]

    def update(self):
        if self.state.finished:
            next_state = self.state.next
            self.state.finished = False
            self.state = self.state_dict[next_state]

        # if self.state is not None:
        self.state.update(self.screen, self.keys)

    def run(self, state):
        while True:
            # print("Inside game loop")
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        # print("UP key pressed")
                        self.key_states[pygame.K_UP] = True
                    elif event.key == pygame.K_DOWN:
                        # print("DOWN key pressed")
                        self.key_states[pygame.K_DOWN] = True
                    elif event.key == pygame.K_RETURN:
                        # print("RETURN key pressed")
                        self.key_states[pygame.K_RETURN] = True
                        self.state.finished = True

                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        self.key_states[pygame.K_UP] = False
                    elif event.key == pygame.K_DOWN:
                        self.key_states[pygame.K_DOWN] = False
                    elif event.key == pygame.K_RETURN:
                        self.key_states[pygame.K_RETURN] = False
                        self.state.finished = False
                    # print("Current State:", self.state.__class__.__name__)

            if self.state.finished:
                next_state = self.state.next
                self.state.finished = False
                print("Switching to next state:", next_state)
                self.state = self.state_dict[next_state]

            self.update()
            # self.state.update(self.screen, self.key_states)
            pygame.display.update()
            self.clock.tick(60)


def load_graphics(path, accept=('.jpg', '.png', '.bmp', '.gif')):
    graphics = {}
    for pic in os.listdir(path):
        name, ext = os.path.splitext(pic)
        if ext.lower() in accept:
            img = pygame.image.load(os.path.join(path, pic))
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
            graphics[name] = img
    return graphics


def get_image(sheet, x, y, width, height, colorkey, scale):
    image = pygame.Surface((width, height))
    image.blit(sheet, (0, 0), (x, y, width, height))
    image.set_colorkey(colorkey)
    image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
    return image
