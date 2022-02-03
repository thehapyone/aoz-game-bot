"""Responsible for managing the radar"""
import time
from datetime import timedelta

import cv2
import numpy as np

from src.constants import OUTSIDE_VIEW, BOTTOM_IMAGE, TOP_IMAGE, RIGHT_IMAGE, \
    LEFT_IMAGE
from src.exceptions import RadarException
from src.game_launcher import GameLauncher
from src.helper import Coordinates, GameHelper, retry
from src.ocr import get_text_from_image, ocr_from_contour


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
            cls._decrease_btn_cords = None
            cls._increase_btn_cords = None
            cls._set_out_btn_cords = None
        return cls._instance

    @property
    def decrease_btn_cords(self) -> Coordinates:
        """
        Returns the decrease btn coordinates.

        :return: Coordinates of the button
        """
        if not self._decrease_btn_cords:
            self.get_increase_decrease_btn_positions()
        return self._decrease_btn_cords

    @property
    def increase_btn_cords(self) -> Coordinates:
        """
        Returns the increase btn coordinates.

        :return: Coordinates of the button
        """
        if not self._increase_btn_cords:
            self.get_increase_decrease_btn_positions()
        return self._increase_btn_cords

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

    @retry(exception=RadarException,
           message="Radar icon could not be found.",
           attempts=2)
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
        t_h, t_w, _ = image.shape
        target_area = image[:,
                      int(0.22 * t_w):int(0.75 * t_w)
                      ]
        image_with_zeros = np.zeros_like(image)
        image_with_zeros[:, int(0.22 * t_w):int(0.75 * t_w)] = target_area

        white_channel = cv2.inRange(image_with_zeros, white_min, white_max)
        custom_config = r'-c tessedit_char_whitelist=:0123456789 ' \
                        r'--oem 3 --psm 6 '
        result = get_text_from_image(white_channel, custom_config).strip()
        if not result or ':' not in result:
            rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 5))
            top_hat = cv2.morphologyEx(cv2.cvtColor(image_with_zeros,
                                                    cv2.COLOR_BGR2GRAY),
                                       cv2.MORPH_TOPHAT,
                                       rect_kernel)
            result = get_text_from_image(top_hat, custom_config).strip()
            print(f'----- result ----- raw top hat = {result}')

            if not result:
                raise RadarException("Can not extract set out time")
        # parse to date time
        timestamp = result.split(":")
        timestamp = [int(value) for value in timestamp]
        print(f'----- timestamp ----- raw = {result}')
        if len(timestamp) == 3:
            delta = timedelta(
                hours=timestamp[0],
                minutes=timestamp[1],
                seconds=timestamp[2])
        elif len(timestamp) == 2:
            delta = timedelta(
                minutes=timestamp[0],
                seconds=timestamp[1])
        else:
            # we try to extract it out manually
            if len(result) == 6:
                delta = timedelta(
                    hours=int(result[0:2]),
                    minutes=int(result[2:4]),
                    seconds=int(result[4:6]))
            elif len(result) == 4:
                delta = timedelta(
                    minutes=int(result[0:2]),
                    seconds=int(result[2:4]))
            else:
                cv2.imwrite('time-error.png', image)
                raise RadarException(
                    "Could not extract set out time."
                    f"Invalid time detected - {result}")
        return int(delta.total_seconds())

    def get_increase_decrease_btn_positions(self):
        """
        Fetches the positions for the increase and decrease buttons
        :return:
        """
        button_section, cords_relative = self.launcher. \
            get_screen_section(10, BOTTOM_IMAGE)
        # get the decrease button
        decrease_section, decrease_relative = self.launcher. \
            get_screen_section(30, LEFT_IMAGE,
                               button_section, cords_relative)
        decrease_cords = self.launcher.find_target(
            decrease_section,
            self.launcher.target_templates('zombie-decrease'))
        if not decrease_cords:
            raise RadarException("Decrease button not found")
        self._decrease_btn_cords = GameHelper.get_relative_coordinates(
            decrease_relative,
            decrease_cords)
        # get the increase button
        increase_section, increase_relative = self.launcher. \
            get_screen_section(40, RIGHT_IMAGE,
                               button_section, cords_relative)
        increase_cords = self.launcher.find_target(
            increase_section,
            self.launcher.target_templates('zombie-increase'))
        if not increase_cords:
            raise RadarException("Increase button not found")
        self._increase_btn_cords = GameHelper.get_relative_coordinates(
            increase_relative,
            increase_cords)

    def adjust_level(self, level_type: str, increase_count: int):
        """
        Adjust the current level to match the expected level
        :return:
        """
        self.launcher.log_message(f'Adjusting level - {level_type}, '
                                  f'{increase_count}')
        if level_type == 'INCREASE':
            self.launcher.mouse.set_position(
                self.increase_btn_cords.start_x,
                self.increase_btn_cords.start_y)
            center = GameHelper.get_center(self.increase_btn_cords)
            self.launcher.mouse.move(*center)
        elif level_type == 'DECREASE':
            self.launcher.mouse.set_position(
                self.decrease_btn_cords.start_x,
                self.decrease_btn_cords.start_y)
            center = GameHelper.get_center(self.decrease_btn_cords)
            self.launcher.mouse.move(*center)
        else:
            raise RadarException('Level type not supported')
        time.sleep(1)
        for _ in range(increase_count):
            self.launcher.mouse.click()
            time.sleep(0.5)

    def set_level(self, level: int, max_level: int):
        """
        Set the level. If level is greater than max level.
        Set to max level - 1

        :param max_level: The max level
        :param level: The expected level.
        :returns: None
        """
        new_level = max_level if level > max_level else level
        # enforces new level is a positive real number
        new_level = new_level if new_level > 0 else 1
        current_level = self._get_current_level()
        increase_count = abs(new_level - current_level)
        self.launcher.log_message(f'Adjusting level - {new_level}')
        if new_level > current_level:
            level_type = 'INCREASE'
            self.adjust_level(level_type, increase_count)
        elif new_level < current_level:
            level_type = 'DECREASE'
            self.adjust_level(level_type, increase_count)

    def _get_current_level(self):
        """
        Fetches the current level.
        :return:
        """
        bottom_section, _ = self.launcher. \
            get_screen_section(13, BOTTOM_IMAGE)

        t_h, t_w, _ = bottom_section.shape

        level_section = bottom_section[
                        0:t_h - int(0.52 * t_h),
                        int(0.35 * t_w): t_w - int(0.35 * t_w)
                        ]

        white_min = (180, 180, 180)
        white_max = (255, 255, 255)
        image_processed = cv2.inRange(level_section, white_min, white_max)
        custom_config = r'-c tessedit_char_whitelist=0123456789 ' \
                        r'--oem 3 --psm 6'
        custom_config2 = r'-c tessedit_char_whitelist=0123456789 ' \
                         r'--oem 3 --psm 10'
        zombie_level_val = get_text_from_image(image_processed,
                                               custom_config)
        zombie_level_val = zombie_level_val if zombie_level_val else \
            ocr_from_contour(image_processed, custom_config2)
        if zombie_level_val:
            self.launcher.log_message(
                f"Current level - {zombie_level_val}")
            return int(zombie_level_val.strip())

        raise RadarException("Current level can not be extracted")

    @retry(exception=RadarException,
           message="No set-out button found",
           attempts=2)
    def find_set_out(self) -> tuple[Coordinates, int]:
        """
        Finds out the set out button and also extract the time of trip.

        :return: The set out button coordinates and the set out time.
        """
        if not self._set_out_btn_cords:
            bottom_section, cords_relative = self.launcher. \
                get_screen_section(13, BOTTOM_IMAGE)

            bottom_section, cords_relative = self.launcher. \
                get_screen_section(45, RIGHT_IMAGE,
                                   bottom_section, cords_relative)
            cords = self.launcher.find_target(
                bottom_section,
                self.launcher.target_templates('setout'))
            if not cords:
                raise RadarException("No set-out button found")
            cords_relative = GameHelper. \
                get_relative_coordinates(
                cords_relative, cords)
            self._set_out_btn_cords = cords_relative
        time_section = self.launcher.get_screenshot()[
                       self._set_out_btn_cords.start_y - 35:
                       self._set_out_btn_cords.start_y,
                       self._set_out_btn_cords.start_x:
                       self._set_out_btn_cords.end_x - 20]
        set_time = self.get_set_out_time(time_section)
        return self._set_out_btn_cords, set_time

    def send_fleet(self) -> int:
        """
        Sends out a troop fleet out to the target and also returns their set
        out time.

        :return: The troop set out time.
        """
        position, time_out = self.find_set_out()
        if time_out:
            self.launcher.mouse.set_position(position.start_x,
                                             position.start_y)
            self.launcher.mouse.move(GameHelper.get_center(position))
            self.launcher.mouse.click()
        return time_out
