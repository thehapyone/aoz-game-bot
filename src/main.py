import logging
import time
from typing import List

from src.farm.farming import Farm
from src.game_launcher import GameLauncher
from src.helper import output_log, get_traceback
from src.listener import MouseController, KeyboardController
from src.profile import GameProfile, PlayerProfile
from src.profile_loader import load_profiles
from src.radar import Radar
from src.zombies.zombies import Zombies


def run_zombies(level: int, fleets: List[int]):
    # zombie
    zombie = Zombies(launcher)
    zombie.initialize_zombie()
    print('------------------------.-----------------')
    zombie.kill_zombies(level, fleets=fleets)


def run_farming(farm_type, level):
    # farming
    farm = Farm(
        farm_type=farm_type,
        farm_level=level,
        launcher=launcher)
    farm.all_out_farming()


def kill_elite_zombie(zombie: Zombies):
    """kills the elite zombie for the profile"""
    try:
        zombie.kill_elite_zombie()
    except Exception:
        pass
    # reset back to home
    zombie.launcher.reset_to_home()


def run_all_profiles(game_launcher: GameLauncher,
                     profile_launcher: GameProfile,
                     game_profiles: List[PlayerProfile]):
    """
    Run all game profiles available

    :return:
    """
    profile_errors = {}
    track_error_history = []

    flag_bot = False

    elite_zombie = Zombies(game_launcher)
    # run all game profiles
    for profile in game_profiles:
        game_launcher.log_message(
            f"######### Now launching profile {profile.name} ###########")
        try:
            profile_launcher.load_profile(profile)

            # now we click on the reward that popups on the game screen.
            game_launcher.get_rewards()
            # Reset the game screen
            game_launcher.reset_to_home()
            # shake to collect available resources
            game_launcher.keyboard.shake()
            time.sleep(3)
            # Kill the Elite zombie if available
            kill_elite_zombie(elite_zombie)

            # Now do something with the loaded profile
            if profile.attack_zombies:
                run_zombies(profile.zombie_level, profile.zombie_fleets)
            if profile.enable_farming:
                run_farming(profile.farming_type, profile.farming_level)
        except Exception as error:
            game_launcher.log_message(
                f"######### Error while processing profile {profile.name} "
                "###########")
            error_snapshot = game_launcher.get_game_screen()
            error_trace = get_traceback(error)
            error_mgs = str(error)
            profile_errors[profile.name] = [error_trace,error_mgs,
                                            error_snapshot]
            game_launcher.reset_to_home()

            # track error history - and flag continuous error pattern
            if not track_error_history:
                track_error_history.append(error_mgs)
            else:
                old_error = track_error_history[-1]
                if old_error == error_mgs:
                    track_error_history.append(error_mgs)
                else:
                    # reset the pattern history
                    track_error_history = [error_mgs]

            if len(track_error_history) >= 5:
                # flag current bot operation
                game_launcher.log_message(
                    f"######### Continuous Error Pattern detected "
                    "###########")
                flag_bot = True
                break

        game_launcher.log_message(
            f"######### Leaving profile {profile.name} ###########")

    return flag_bot, profile_errors


def log_errors(profile_game_errors: dict):
    """Logs all profile related errors"""

    try:
        if profile_game_errors:
            launcher.log_message("Bot session finished with errors. ERRORS: \n")
            log_history = []
            log_image_history = []
            for profile_name, error in profile_game_errors.items():
                error_trace, error_message, error_image = error
                message_trace = f'Profile {profile_name} ' \
                                f'generated error. \n {error_trace} \n'
                log_history.append(message_trace)
                snapshot_name = f"{profile_name.lower()}_log_image.png"
                log_image_history.append((error_image, snapshot_name))
                message = f'Profile {profile_name} ' \
                          f'generated error: \n "{error_message}" \n'
                launcher.log_message(message)

            # save all log messages
            output_log(launcher.cwd, log_history, log_image_history)
        else:
            launcher.log_message("Bot session finished")
    except Exception as error:
        logging.exception(f"Unknown error has occurred - {str(error)}")


if __name__ == '__main__':
    mouse = MouseController()
    keyboard = KeyboardController()

    clear_cache_counter = 0
    first_launch = True
    # wait for 1 hour before trying again
    reload_time = 3600

    # Run game launcher
    launcher = GameLauncher(mouse, keyboard,
                            cache=True, enable_debug=True)
    launcher.start_game()

    # Load the saved game profiles
    game_profiles = load_profiles()

    launcher.log_message(
        f"######### Loaded a total of {len(game_profiles)} profiles "
        "###########")

    # the profile launcher
    game_profile_launcher = GameProfile(launcher)

    while True:
        # run all the game profiles
        time.sleep(5)
        bot_error, game_errors = run_all_profiles(
            game_launcher=launcher,
            profile_launcher=game_profile_launcher,
            game_profiles=game_profiles)
        log_errors(game_errors)

        if bot_error:
            # reset the game launcher again.
            clear_cache_counter = clear_cache_counter + 1
            if clear_cache_counter >= 2 or first_launch:
                first_launch = False
                clear_cache_counter = 0
                launcher.clear_cache()

                # initialize a new launcher
                launcher = GameLauncher(mouse, keyboard,
                                        cache=True, enable_debug=True)
                # also reset the Radar instance.
                Radar.reset()
                # reset the profile launcher
                GameProfile.reset()
                game_profile_launcher = GameProfile(launcher)

            # relaunch game process again to fix issue
            launcher.start_game()

        else:
            clear_cache_counter = 0
            # now wait again for a period of time before continuing
            time.sleep(reload_time)
