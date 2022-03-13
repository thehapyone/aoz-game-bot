import time

from src.farm.farming import Farm
from src.game_launcher import GameLauncher
from src.helper import Coordinates
from src.listener import MouseController, KeyboardController
from src.profile import GameProfile
from src.radar import Radar
from src.zombies.zombies import Zombies


def run_zombies():
    # zombie
    time.sleep(5)
    zombie = Zombies(launcher)
    zombie.initialize_zombie()
    print('------------------------.-----------------')
    zombie.kill_zombies(29, fleets=[2, 3, 4])


def run_farming():
    # farming
    time.sleep(5)
    farm = Farm(
        farm_type=3,
        farm_level=5,
        launcher=launcher)
    print('-------------------------------------------')
    print(farm.all_out_farming())


def test_radar():
    radar = Radar(launcher)
    print(radar.get_fleets_menu())
    print(radar.find_set_out())


if __name__ == '__main__':
    testing_app_coordinates = Coordinates(start_x=2743, start_y=462,
                                          end_x=3498, end_y=1820)
    mouse = MouseController()
    keyboard = KeyboardController()
    # Run game launcher
    launcher = GameLauncher(mouse, keyboard, test_mode=True)
    launcher.start_game(testing_app_coordinates)

    profile = GameProfile(launcher)
    # profile.get_all_profiles()
    # target = "futuregamerayo08@gmail.com"
    # profile.go_to_profile(target)
    #profile_view = Profile(email="futuregamerayo08@gmail.com",
    #                       user_name="ShadowFarm8_1")

    #profile.load_profile(profile_view)
    run_zombies()