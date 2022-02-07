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

    #radar = Radar(launcher)
    #print(radar.get_current_level())

    # zombie
    time.sleep(5)
    zombie = Zombies(launcher)
    zombie.initialize_zombie()
    print('------------------------.-----------------')
    zombie.kill_zombies(30, fleet=2)

    '''
    # farming
    time.sleep(5)
    farm = Farm(1, launcher)
    print('-------------------------------------------')
    print(farm.max_fleet)
    print(farm.current_fleet)
    '''
