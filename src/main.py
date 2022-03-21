import time

from src.farm.farming import Farm
from src.game_launcher import GameLauncher
from src.helper import Coordinates
from src.listener import MouseController, KeyboardController
from src.profile import GameProfile
from src.profile_loader import load_profiles
from src.zombies.zombies import Zombies


def run_zombies():
    # zombie
    time.sleep(5)
    zombie = Zombies(launcher)
    zombie.initialize_zombie()
    print('------------------------.-----------------')
    zombie.kill_zombies(29, fleets=[2, 3, 4])


def run_farming(farm_type, level):
    # farming
    farm = Farm(
        farm_type=farm_type,
        farm_level=level,
        launcher=launcher)
    farm.all_out_farming()


if __name__ == '__main__':
    testing_app_coordinates = Coordinates(start_x=2743, start_y=462,
                                          end_x=3498, end_y=1820)
    mouse = MouseController()
    keyboard = KeyboardController()

    # Run game launcher
    launcher = GameLauncher(mouse, keyboard, test_mode=True)
    launcher.start_game(testing_app_coordinates)

    # Load the saved game profiles
    game_profiles = load_profiles()

    launcher.log_message(
        f"######### Loaded a total of {len(game_profiles)} profiles "
        "###########")

    # the profile launcher
    profile_launcher = GameProfile(launcher)

    time.sleep(5)

    profile_errors = {}
    # run all game profiles
    for profile in game_profiles:
        launcher.log_message(
            f"######### Now launching profile {profile.name} ###########")
        try:
            profile_launcher.load_profile(profile)

            # now we click on the reward that popups on the game screen.
            launcher.get_rewards()
            # Reset the game screen
            launcher.reset_to_home()
            # shake to collect available resources
            launcher.keyboard.shake()
            time.sleep(3)
            # Now do something with the loaded profile
            run_farming(profile.farming_type, profile.farming_level)
        except Exception as error:
            launcher.log_message(
                f"######### Error while processing profile {profile.name} "
                "###########")
            profile_errors[profile.name] = str(error)
            launcher.reset_to_home()

        launcher.log_message(
            f"######### Leaving profile {profile.name} ###########")
        time.sleep(2)

    if profile_errors:
        launcher.log_message("Bot session finished with errors. ERRORS: \n")
        for name, error in profile_errors.items():
            launcher.log_message(f'Profile {name} generated error {error} \n')
    else:
        launcher.log_message("Bot session finished")
