"""The Game Profile is responsible for launching and managing all game
profiles"""
import time

from src.constants import BOTTOM_IMAGE, TOP_IMAGE, LEFT_IMAGE, \
    RIGHT_IMAGE
from src.exceptions import ProfileException
from src.game_launcher import GameLauncher, display_image
from src.helper import GameHelper
from src.ocr import get_text_from_image


class GameProfile:
    """
    The Class responsible for managing and loading
    various game profiles.

    """

    _instance = None

    def __new__(cls, launcher: GameLauncher):
        if cls._instance is None:
            cls._instance = super(GameProfile, cls).__new__(cls)
            cls._instance.launcher = launcher
            cls._profiles = None
            return cls._instance
        return cls._instance

    def activate_account_screen(self):
        """
        Activates the my info account screen.

        :return: None
        """
        _, menu_dict, _ = self.launcher.bottom_menu()
        account_cords = menu_dict[5]
        center = GameHelper.get_center(account_cords)
        self.launcher.mouse.set_position(account_cords.start_x,
                                         account_cords.start_y)
        self.launcher.mouse.move(center)
        self.launcher.mouse.click()
        time.sleep(2)

    def activate_switch_account(self):
        """
        Activates the switch account screen.

        :return: None
        """
        image_section, area_cords_relative = \
            self.launcher.get_screen_section(30, BOTTOM_IMAGE)

        area_cords = self.launcher.find_target(
            image_section,
            self.launcher.target_templates('switch-account'))
        if not area_cords:
            raise ProfileException("Switch account button not found")
        area_cords_relative = GameHelper.get_relative_coordinates(
            area_cords_relative, area_cords)
        center = GameHelper.get_center(area_cords_relative)
        self.launcher.mouse.set_position(area_cords_relative.start_x,
                                         area_cords_relative.start_y)
        self.launcher.mouse.move(center)
        self.launcher.mouse.click()
        time.sleep(1)

        # finding the login button
        login_area_image, login_cords_relative = \
            self.launcher.get_screen_section(65, BOTTOM_IMAGE)
        login_area_image, login_cords_relative = \
            self.launcher.get_screen_section(50, TOP_IMAGE,
                                             login_area_image,
                                             login_cords_relative)

        login_cords = self.launcher.find_target(
            login_area_image,
            self.launcher.target_templates('switch-account-login'))

        if not login_cords:
            raise ProfileException("Switch account login button not found")

        login_cords_relative = GameHelper.get_relative_coordinates(
            login_cords_relative, login_cords)
        center = GameHelper.get_center(login_cords_relative)
        self.launcher.mouse.set_position(login_cords_relative.start_x,
                                         login_cords_relative.start_y)
        self.launcher.mouse.move(center)
        self.launcher.mouse.click()
        time.sleep(5)
        # take profile snapshot and save for processing.

    def snapshot_profile(self):
        """
        Takes a snapshot of the profile and performs OCR on it.
        :return: None
        """
        profile_area_image, profile_cords_relative = \
            self.launcher.get_screen_section(80, BOTTOM_IMAGE)
        profile_area_image, profile_cords_relative = \
            self.launcher.get_screen_section(82, LEFT_IMAGE,
                                             profile_area_image,
                                             profile_cords_relative)
        profile_area_image, profile_cords_relative = \
            self.launcher.get_screen_section(82, RIGHT_IMAGE,
                                             profile_area_image,
                                             profile_cords_relative)

        result = get_text_from_image(profile_area_image)

        print(result)
        display_image(profile_area_image)
        #### #
        # - Idea: Iteerate through all returned text and the location.
        # See if target profile matches - then use that target.



    def get_all_profiles(self):
        """
        Function responsible for getting all available game
        profiles.
        :return:
        """
        self.activate_account_screen()
        account_menu = self.launcher.get_account_menu
        account_cords = account_menu[3]
        center = GameHelper.get_center(account_cords)
        self.launcher.mouse.set_position(account_cords.start_x,
                                         account_cords.start_y)
        self.launcher.mouse.move(center)
        self.launcher.mouse.click()
