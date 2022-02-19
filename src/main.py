import time

from src.game_launcher import GameLauncher
from src.helper import Coordinates
from src.listener import MouseController, KeyboardController
from src.zombies import Zombies

if __name__ == '__main__':
    testing_app_coordinates = Coordinates(start_x=2641, start_y=304,
                                          end_x=3460, end_y=1776)
    mouse = MouseController()
    keyboard = KeyboardController()
    # Run game launcher
    launcher = GameLauncher(mouse, keyboard, test_mode=True)
    launcher.start_game(testing_app_coordinates)
    '''
    radar = Radar(launcher)
    print(radar.get_fleets_menu())
    '''

    # zombie
    time.sleep(5)
    zombie = Zombies(launcher)
    zombie.initialize_zombie()
    print('------------------------.-----------------')
    zombie.kill_zombies(30, fleets=[1, 2, 3, 4, 5])

    '''
    # farming
    time.sleep(5)
    farm = Farm(1, launcher)
    print('-------------------------------------------')
    print(farm.max_fleet)
    print(farm.current_fleet)
    '''
