"""The Game Profile is responsible for launching and managing all game
profiles"""
import time
from dataclasses import dataclass
from typing import List

import cv2

from src.constants import BOTTOM_IMAGE, TOP_IMAGE
from src.exceptions import ProfileException
from src.game_launcher import GameLauncher
from src.helper import GameHelper, Coordinates, click_on_target, retry


@dataclass
class PlayerProfile:
    """
    A class for storing game profile user details
    """
    name: str
    email: str
    nickname: str
    farming_type: int
    farming_level: int
    zombie_level: int
    zombie_fleets: List[int]
    attack_zombies: int
    enable_farming: int


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

    @classmethod
    def reset(cls):
        """Reset the class instance"""
        cls._instance = None

    @staticmethod
    def activate_menu_screen(launcher: GameLauncher, menu: int):
        """
        Activates the my info menu screen.

        :return: None
        """
        _, menu_dict, _ = launcher.bottom_menu()
        account_cords = menu_dict[menu]
        center = GameHelper.get_center(account_cords)
        launcher.mouse.set_position(account_cords.start_x,
                                    account_cords.start_y)
        launcher.mouse.move(center)
        launcher.mouse.click()
        time.sleep(2)

    @retry(exception=ProfileException,
           message="Switch account button not found",
           attempts=3)
    def activate_switch_account(self):
        """
        Activates the switch account screen.

        :return: None
        """
        image_section, area_cords_relative = \
            self.launcher.get_screen_section(40, BOTTOM_IMAGE)
        area_cords = self.launcher.find_ocr_target('switch',
                                                   image_section,
                                                   r'--oem 3 --psm 6')
        if not area_cords:
            raise ProfileException("Switch account button not found")
        area_cords_relative = GameHelper.get_relative_coordinates(
            area_cords_relative, area_cords)
        center = GameHelper.get_center(area_cords_relative)
        self.launcher.mouse.set_position(area_cords_relative.start_x,
                                         area_cords_relative.start_y)
        self.launcher.mouse.move(center)
        self.launcher.mouse.click()
        time.sleep(2)
        # finding the login button
        self._activate_login_in_switch()

    @retry(exception=ProfileException,
           message="Switch account login button not found",
           attempts=3)
    def _activate_login_in_switch(self):
        """Activates the login button in the switch account screen"""

        login_area_image, login_cords_relative = \
            self.launcher.get_screen_section(50, BOTTOM_IMAGE)
        login_area_image, login_cords_relative = \
            self.launcher.get_screen_section(50, TOP_IMAGE,
                                             login_area_image,
                                             login_cords_relative)

        white_min = (128, 128, 128)
        white_max = (255, 255, 255)
        white_channel = cv2.inRange(login_area_image, white_min, white_max)

        login_cords = self.launcher.find_ocr_target('login',
                                                    white_channel,
                                                    r'--oem 3 --psm 6')

        if not login_cords:
            raise ProfileException("Switch account login button not found")

        click_on_target(
            login_cords, login_cords_relative, self.launcher.mouse
        )
        time.sleep(5)

    @retry(exception=ProfileException,
           message="Profile not found",
           attempts=4)
    def go_to_profile(self, profile: PlayerProfile):
        """
        Takes a snapshot of the profile and performs OCR on it. Afterwards,
        go to the profile mini screen.

        :return: None
        """

        profile_area_image, profile_cords_relative = \
            self.launcher.get_screen_section(85, TOP_IMAGE)
        # find the target and click on it.
        targets = [profile.email.lower().strip(),
                   profile.nickname.lower().strip()]
        location = self.launcher.find_ocr_target(
            targets, profile_area_image)

        if not location:
            self.launcher.log_message(f"Profile target {targets} not found")
            raise ProfileException("Profile not found")

        click_on_target(location,
                        profile_cords_relative,
                        self.launcher.mouse)
        time.sleep(2)
        self._activate_continue_on_profile(targets[0])

    @retry(exception=ProfileException,
           message="Continue as button not found",
           attempts=3)
    def _activate_continue_on_profile(self, target):
        # click on the continue button for the profile
        continue_area_image, continue_cords_relative = \
            self.launcher.get_screen_section(15, BOTTOM_IMAGE)
        custom_config = r'--oem 3 --psm 6'
        location = self.launcher.find_ocr_target("Continue",
                                                 continue_area_image,
                                                 custom_config)
        if not location:
            self.launcher.log_message(f"Continue as {target} not found")
            raise ProfileException("Continue as button not found")
        click_on_target(location,
                        continue_cords_relative,
                        self.launcher.mouse)
        time.sleep(5)

    def get_all_profiles(self):
        """
        Function responsible for getting all available game
        profiles.
        :return:
        """
        self.activate_menu_screen(self.launcher, menu=5)
        account_menu = self.launcher.get_account_menu
        account_cords = account_menu[3]
        center = GameHelper.get_center(account_cords)
        self.launcher.mouse.set_position(account_cords.start_x,
                                         account_cords.start_y)
        self.launcher.mouse.move(center)
        self.launcher.mouse.click()
        time.sleep(2)
        # Activate the account switching mode
        self.activate_switch_account()
        # Show the complete profile
        self._show_complete_profile()
        time.sleep(2)

    def _show_complete_profile(self):
        """
        Show the full game profiles from the mini view.

        :return: None
        """
        profile_area_image, profile_cords_relative = \
            self.launcher.get_screen_section(18, BOTTOM_IMAGE)

        t_h, t_w, _ = profile_area_image.shape
        target_cords = Coordinates(
            start_x=0, start_y=0, end_x=t_w, end_y=int(0.40 * t_h)
        )
        target_cords_relative = GameHelper.get_relative_coordinates(
            profile_cords_relative, target_cords
        )

        center = GameHelper.get_center(target_cords_relative)
        self.launcher.mouse.set_position(target_cords_relative.start_x,
                                         target_cords_relative.start_y)
        self.launcher.mouse.move(center)
        self.launcher.mouse.click()

    @retry(exception=ProfileException,
           message="Account not found",
           attempts=5)
    def activate_target_in_profile(self, target: str):
        """
        Clicks on a target in the account mini profile view thereby
        activating that profile not already activate before.

        :return: None
        """

        profile_area_image, profile_cords_relative = \
            self.launcher.get_screen_section(65, TOP_IMAGE)
        profile_area_image, profile_cords_relative = \
            self.launcher.get_screen_section(53, BOTTOM_IMAGE,
                                             profile_area_image,
                                             profile_cords_relative)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))

        gray = cv2.cvtColor(profile_area_image, cv2.COLOR_BGR2GRAY)
        gradient = cv2.morphologyEx(gray,
                                    cv2.MORPH_TOPHAT, kernel)

        images = (profile_area_image, gray, gradient)

        ocr_settings = (3, 4, 6)
        found = False
        location = None
        for image in images:
            for psm in ocr_settings:
                config = fr'-c tessedit_char_blacklist=_ --oem 3 --psm {psm}'

                location = self.launcher.find_ocr_target(target,
                                                         image,
                                                         config)
                if location:
                    found = True
                    break
            if found:
                break
        else:
            self.launcher.log_message(f"Account target {target} not found")
            raise ProfileException("Account not found")

        click_on_target(location,
                        profile_cords_relative,
                        self.launcher.mouse)

        time.sleep(2)
        # search for the confirm screen mode
        confirm_area_image, area_cords_relative = self.launcher. \
            get_confirm_view()
        # find the target and click on it.
        custom_config = r'--oem 3 --psm 6'

        white_min = (128, 128, 128)
        white_max = (255, 255, 255)
        white_channel = cv2.inRange(confirm_area_image, white_min, white_max)

        location = self.launcher.find_ocr_target("Confirm", white_channel,
                                                 custom_config)
        if not location:
            # means we are in the right profile. So go back to home screen.
            for _ in range(3):
                self.launcher.keyboard.back()
        else:
            click_on_target(location,
                            area_cords_relative,
                            self.launcher.mouse)

    def load_profile(self, profile: PlayerProfile):
        """
        Responsible for loading a profile. If not successful, an exception
        will be raised.
        :return:
        """
        self.get_all_profiles()
        # go to the full profile screen and click target
        self.go_to_profile(profile)
        # now activate the profile
        self.activate_target_in_profile(profile.name)
        # now wait for some time for the profile to load fully
        time.sleep(30)
