"""Code responsible for loading the Game profiles"""
from configparser import ConfigParser
from typing import List

from constants import CONFIG_PATH
from src.exceptions import ProfileException
from src.profile import PlayerProfile

# Initialize the config
config = ConfigParser()


def load_profile_configs():
    """
    Loads the configs and return a dictionary of all profile
    configurations.
    """
    loaded_configs = config.read(CONFIG_PATH)
    if not loaded_configs:
        raise FileNotFoundError(f"No config file found in path "
                                f"{str(CONFIG_PATH)}")
    # parses the configuration as a standard dictionary
    try:
        all_profiles = config.get("profiles", "all_profiles")
    except Exception as error:
        raise ProfileException("The 'profiles' section with key "
                               "'all_profiles' are required but not "
                               "available") from error
    # parse all profiles to list
    all_profiles = sorted(list({profile.strip().lower() for profile in
                                all_profiles.strip().split(',')}))

    # parse configs to a proper dictionary
    configs_dict = {section: {key: value
                              for key, value in config[section].items()}
                    for section in config.sections()}
    # update the all profiles
    configs_dict["profiles"]["all_profiles"] = all_profiles
    # validate all the mentioned profiles are included in the config
    error_profiles = [profile for profile in all_profiles if profile not in
                      configs_dict]
    if error_profiles:
        raise ProfileException("Config contains some invalid profiles. "
                               f"Details: {error_profiles}")
    return configs_dict


def load_profiles() -> List[PlayerProfile]:
    """
    Loads and parse the game config files as profile objects
    :return: A List of GameProfiles
    """
    loaded_configs = load_profile_configs()
    game_profiles = []
    for profile in loaded_configs["profiles"]["all_profiles"]:
        # parse the zombie fleet from str to list
        profile_config: dict = loaded_configs[profile]
        zombie_fleets = profile_config.get("zombie_fleets")
        zombie_fleets = [] if not zombie_fleets else \
            [fleet.strip().lower()
             for fleet in zombie_fleets.strip().split(',')]
        profile_config["zombie_fleets"] = zombie_fleets
        profile_config["farming_type"] = int(profile_config["farming_type"])
        profile_config["farming_level"] = int(profile_config["farming_level"])
        profile_config["zombie_level"] = int(profile_config["zombie_level"])

        # create the game profile object
        game_profile = PlayerProfile(**profile_config)
        game_profiles.append(game_profile)
    return game_profiles
