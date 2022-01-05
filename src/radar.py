"""Responsible for managing the radar"""
import time
from datetime import timedelta

import cv2
import numpy as np

from src.constants import OUTSIDE_VIEW, BOTTOM_IMAGE, TOP_IMAGE, RIGHT_IMAGE
from src.exceptions import RadarException
from src.game_launcher import GameLauncher, display_image
from src.helper import Coordinates, GameHelper
from src.ocr import get_text_from_image


class Radar:
    """
    Radar handling class

    :param GameLauncher launcher: The game launcher instance
    """

    _instance = None

    def __new__(cls, launcher: GameLauncher):
        if not cls._instance:
            cls._instance = super(Radar, cls).__new__(cls)
            cls._instance.launcher = launcher
            cls._instance._activated = False
            cls._instance._radar_coordinates = None
            cls._instance._go_button = None
        return cls._instance

    @property
    def go_button(self) -> Coordinates:
        """Returns the go button coordinates"""
        if not self._go_button:
            self._go_button = self.get_go_button()
        return self._go_button

    @property
    def radar_coordinates(self) -> Coordinates:
        """Returns the radar button coordinates"""
        if not self._radar_coordinates:
            self._radar_coordinates = self.find_radar()
        return self._radar_coordinates

    def find_radar(self):
        """
        Finds the radar coordinates in the outside city
        :return: None
        """
        self.launcher.set_view(OUTSIDE_VIEW)
        self.launcher.log_message(
            "################ Finding the radar ################")
        radar_area_image, radar_area_cords_relative = \
            self.launcher.get_screen_section(23, BOTTOM_IMAGE)
        radar_area_image, radar_area_cords_relative = \
            self.launcher.get_screen_section(30, RIGHT_IMAGE,
                                             radar_area_image,
                                             radar_area_cords_relative)
        cords = self.launcher.find_target(
            radar_area_image,
            self.launcher.target_templates('radar'))

        if not cords:
            raise RadarException("Radar icon could not be found.")
        cords_relative = GameHelper. \
            get_relative_coordinates(
            radar_area_cords_relative, cords)
        return cords_relative

    def activate_radar(self):
        """
        Activates the radar in the outside city
        :return: None
        """
        self.launcher.set_view(OUTSIDE_VIEW)
        self.launcher.log_message(
            "################ Activating the radar screen ################")
        self.launcher.mouse.set_position(self.radar_coordinates.start_x,
                                         self.radar_coordinates.start_y)
        time.sleep(1)
        self.launcher.mouse.move(GameHelper.get_center(
            self.radar_coordinates))
        self.launcher.mouse.click()
        time.sleep(2)

    def select_radar_menu(self, menu: int):
        """
        Selects and activates one of the radar menu.

        :param menu: The 6 Menus supported are:
            1 - Grain Farming
            2 - Oil Farming
            3 - Steel Farming
            4 - Mineral Farming
            5 - Gold Farming
            6 - Zombies killing
        :returns: None
        """
        self.activate_radar()
        radar_section, radar_area_cords_relative = \
            self.launcher.get_screen_section(23, BOTTOM_IMAGE)
        menu_section, _ = self.launcher.get_screen_section(45,
                                                           TOP_IMAGE,
                                                           radar_section)
        t_h, t_w, _ = menu_section.shape
        radar_options = {}
        icon_width = int(0.1666 * t_w)
        end_width = 0
        for count in range(1, 7):
            start_width = end_width
            end_width = start_width + icon_width
            if end_width > t_w:
                end_width = t_w
            cords_relative = GameHelper.get_relative_coordinates(
                radar_area_cords_relative,
                Coordinates(start_width, 0, end_width, t_h))
            radar_options[count] = cords_relative

        # Now activate the selected menu
        current_cords = radar_options[menu]
        center = GameHelper.get_center(current_cords)
        self.launcher.mouse.set_position(
            current_cords.start_x, current_cords.start_y)
        self.launcher.mouse.move(*center)
        self.launcher.mouse.click()
        time.sleep(2)

    def get_go_button(self) -> Coordinates:
        """
        Returns the go button for the display radar menu.
        :returns: Coordinates of the go button.
        """
        go_section, go_relative = self.launcher. \
            get_screen_section(13, BOTTOM_IMAGE)
        go_cords = self.launcher.find_target(
            go_section,
            self.launcher.target_templates('go-button'))
        if not go_cords:
            raise RadarException("Radar go button not found")
        go_btn_cords = GameHelper.get_relative_coordinates(
            go_relative, go_cords)
        return go_btn_cords

    @staticmethod
    def get_set_out_time(image: np.ndarray) -> int:
        """
        Extracts the set out time from the given image.

        :param image: Input image containing the set out time section
        :return: The set out time in seconds.
        """
        white_min = (130, 130, 130)
        white_max = (220, 220, 220)
        white_channel = cv2.inRange(image, white_min, white_max)
        custom_config = r'-c tessedit_char_whitelist=:0123456789 ' \
                        r'--oem 3 --psm 6 '
        result = get_text_from_image(white_channel, custom_config)

        if not result:
            rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 5))
            top_hat = cv2.morphologyEx(cv2.cvtColor(image,
                                                    cv2.COLOR_BGR2GRAY),
                                       cv2.MORPH_TOPHAT,
                                       rect_kernel)
            display_image(top_hat)

            result = get_text_from_image(top_hat, custom_config)
            print(f'----- result ----- raw = {result}')

            if not result:
                raise RadarException("Can not extract set out time")
        # parse to date time
        timestamp = result.strip().split(":")
        timestamp = [int(value) for value in timestamp]
        print(f'----- timestamp ----- raw = {result}')
        if len(timestamp) == 3:
            delta = timedelta(
                hours=timestamp[0],
                minutes=timestamp[1],
                seconds=timestamp[2])
        else:
            delta = timedelta(
                minutes=timestamp[0],
                seconds=timestamp[1])
        return int(delta.total_seconds())
