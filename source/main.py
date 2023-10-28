import pygame

from source import tools
from source.states import main_menu, load_screen, level

def main():

    state_dict = {
        'main_menu': main_menu.MainMenu(),
        'load_screen': load_screen.LoadScreen(),
        'level': level.Level()
    }
    game = tools.Game()
    game.run()

if __name__ == '__main__':
    main()