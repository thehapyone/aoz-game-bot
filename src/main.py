import time

from src.farming import Farm
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
    time.sleep(5)
    zombie = Zombies(launcher)
    zombie.initialize_zombie()
    print('------------------------.-----------------')
    zombie.kill_zombies(20)
    #zombie.find_zombie(15)
    #zombie.find_set_out()

    # farming
    time.sleep(5)
    farm = Farm(1, launcher)
    print('-------------------------------------------')
    print(farm.get_max_fleet())
