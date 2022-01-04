import time

from src.game_launcher import GameLauncher
from src.listener import MouseController, KeyboardController
from src.zombies import Zombies

if __name__ == '__main__':
    mouse = MouseController()
    keyboard = KeyboardController()
    # Run game launcher
    launcher = GameLauncher(mouse, keyboard)
    launcher.start_game()

    # zombie
    zombie = Zombies(launcher)
    #zombie.initialize_zombie()
    #zombie.find_zombie(12)
    print('-----------------------------------------')
    time.sleep(1)
    #zombie.attack_zombie()
    zombie.find_set_out()