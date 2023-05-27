from . import scenes
from .game import game



def main():
    game.init_window()
    game.init_font()
    game.scene = 'home'
    game.loop()