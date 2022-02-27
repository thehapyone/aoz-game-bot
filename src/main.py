from src.game_launcher import GameLauncher
from src.helper import Coordinates
from src.listener import MouseController, KeyboardController
from src.profile import GameProfile

if __name__ == '__main__':
    testing_app_coordinates = Coordinates(start_x=2557, start_y=315,
                                          end_x=3424, end_y=1874)
    mouse = MouseController()
    keyboard = KeyboardController()
    # Run game launcher
    launcher = GameLauncher(mouse, keyboard, test_mode=True)
    launcher.start_game(testing_app_coordinates)

    # radar = Radar(launcher)
    # print(radar.get_fleets_menu())
    # print(radar.find_set_out())

    profile = GameProfile(launcher)
    profile.snapshot_profile()
    '''
    # zombie
    time.sleep(5)
    zombie = Zombies(launcher)
    zombie.initialize_zombie()
    print('------------------------.-----------------')
    zombie.kill_zombies(29, fleets=[2,3,4])
    '''
    '''
    # farming
    time.sleep(5)
    farm = Farm(
        farm_type=3,
        farm_level=5,
        launcher=launcher)
    print('-------------------------------------------')
    print(farm.all_out_farming())
    '''
