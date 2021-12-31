"""Responsible for killing zombies in the Game event"""
import time
from typing import Optional

import cv2
import numpy as np

from src.constants import OUTSIDE_VIEW, BOTTOM_IMAGE, LEFT_IMAGE, RIGHT_IMAGE
from src.exceptions import ZombieException
from src.game_launcher import GameLauncher
from src.helper import GameHelper, Coordinates
from src.ocr import get_text_from_image, ocr_from_contour
from src.radar import Radar


class Zombies:
    """
    Zombies killing class.

    In order to be able to kill zombies in the game,
    some of this things need to be sorted out:
     - Get current mobility --- done
     - Ability to switch to outside city screen --- done
     - find and click on the green radar button --- done
     - find and click on the find zombie radar ---- done
     - get the current level of zombie for the user --- done
     - increase and decrease the zombie level. -- done
     - get the current zombie level --- done
     - click on go to find any available zombie
     - search and find the arrow that shows for about 6 secs before disappearing
     - click on the given zombie (confirm it is the right zombie level)
     - attack the zombie
     - set out with the default formation
     How do I know the zombie has been killed?
     - check the coordinate of the zombie and confirm the zombie is no more?
     - wait for period of time

    How do I know my attack troops have returned?
     - I can get the duration time to the target during 'set out' and
     multiple it by two to know the amount of time to wait for before
     restarting the attack again.
     - I check if the 'attack en route' or 'attack withdraw' is no more showing.

     - continue attacks as far mobility is greater than given limit.

    """

    def __init__(self, launcher: GameLauncher):
        self._fuel = None
        self.launcher = launcher
        self._max_level = None
        self._decrease_btn_cords: Optional[Coordinates] = None
        self._increase_btn_cords: Optional[Coordinates] = None
        self.radar = Radar(self.launcher)

    @property
    def fuel(self):
        """Returns the current fuel"""
        self._fuel = self._get_latest_fuel()
        return self._fuel

    @property
    def max_level(self):
        """Returns the zombie max level allowed so far"""
        if not self._max_level:
            self._max_level = self.get_zombie_max()
        return self._max_level

    @staticmethod
    def get_fuel_screen(image: np.ndarray) -> np.ndarray:
        """Returns an area of the screen where fuel is usually located"""
        t_h, t_w, _ = image.shape
        # new height = 8% of image height
        new_th = int(0.08 * t_h)
        # new width = 26% of the image width
        new_tw = int(0.26 * t_w)
        fuel_screen = image[0:new_th, 0:new_tw]
        return fuel_screen

    @staticmethod
    def process_fuel_image(image: np.ndarray) -> np.ndarray:
        """
        Pre process the fuel image for OCR
        :param image: A BGR image.
        :return: A threshold binary image
        """
        green_min = (0, 105, 10)
        green_max = (16, 255, 75)
        white_min = (100, 100, 100)
        white_max = (255, 255, 255)

        green_channel = cv2.inRange(image, green_min, green_max)
        white_channel = cv2.inRange(image, white_min, white_max)

        green_sum = sum(sum(green_channel))
        white_sum = sum(sum(white_channel))
        if green_sum > white_sum:
            return green_channel
        return white_channel

    def _get_latest_fuel(self):
        """Get the current fuel value"""
        game_screen = self.launcher.get_game_screen()
        fuel_screen = self.get_fuel_screen(game_screen)
        # search fuel target to extract fuel area
        fuel_cords = self.launcher.find_target(
            fuel_screen, self.launcher.target_templates('mobility'))
        new_x = fuel_cords.end_x + 5
        end_x = fuel_screen.shape[1] - 5
        fuel_image = fuel_screen[
                     fuel_cords.start_y + 5:fuel_cords.end_y - 5,
                     new_x:end_x,
                     ]
        processed_image = self.process_fuel_image(fuel_image)
        custom_config = r'-c tessedit_char_blacklist=-/\| --oem 3 --psm 6 ' \
                        r'outputbase digits'

        # extract the fuel value
        fuel_value = get_text_from_image(processed_image, custom_config)
        self.launcher.log_message(f"Current fuel - {fuel_value}")
        if fuel_value:
            return int(fuel_value.strip())
        raise ZombieException("Fuel value not readable")

    def get_zombie_max(self) -> int:
        """
        Gets the current max level of zombie
        :return: Current zombie max level
        """
        zombie_section, _ = self.launcher. \
            get_screen_section(4, BOTTOM_IMAGE)
        t_h, t_w, _ = zombie_section.shape
        zombie_level_img = zombie_section[0:t_h,
                           int(0.30 * t_w):t_w - int(0.30 * t_w)]
        cv2.imwrite('zombie5.png', zombie_level_img)
        black_min = (2, 2, 2)
        black_max = (65, 65, 65)
        image_processed = cv2.inRange(zombie_level_img, black_min, black_max)
        custom_config = r'-c tessedit_char_blacklist=-/\| --oem 3 --psm 6'
        zombie_level = get_text_from_image(image_processed, custom_config)

        if zombie_level:
            digits = "".join([char for char in zombie_level.strip()
                              if char.isdigit()])
            self.launcher.log_message(f"Current zombie max - {digits}")
            return int(digits)
        raise ZombieException("Zombie Max level can not be extracted")

    def get_zombie_increment_position(self):
        """
        Fetches the zombie level increment button position
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
            raise ZombieException("Zombie decrease button not found")
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
            raise ZombieException("Zombie increase button not found")
        self._increase_btn_cords = GameHelper.get_relative_coordinates(
            increase_relative,
            increase_cords)
        increase_center = GameHelper.get_center(self._increase_btn_cords)
        self.launcher.mouse.set_position(self._increase_btn_cords.start_x,
                                         self._increase_btn_cords.start_y)
        self.launcher.mouse.move(*increase_center)

    def initialize_zombie(self):
        """Initialize zombie buttons"""
        # Set to the zombie radar screen
        self.radar.select_radar_menu(6)
        self.get_zombie_increment_position()
        self._max_level = self.get_zombie_max()

    def get_zombie_current_level(self):
        """
        Fetches the current zombie level.
        :return:
        """
        bottom_section, _ = self.launcher. \
            get_screen_section(13, BOTTOM_IMAGE)

        t_h, t_w, _ = bottom_section.shape

        level_section = bottom_section[
                        0:t_h - int(0.52 * t_h),
                        int(0.35 * t_w): t_w - int(0.35 * t_w)
                        ]

        cv2.imwrite('zombie-level3.png', level_section)
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
                f"Current zombie level - {zombie_level_val}")
            return int(zombie_level_val.strip())

        raise ZombieException("Zombie current level can not be extracted")

    def zombie_go(self):
        """
        Activates the zombie go button to find the next available zombie.
        :return:
        """
        self.launcher.mouse.set_position(self.radar.go_button)
        center = GameHelper.get_center(self.radar.go_button)
        self.launcher.mouse.move(*center)

    def _adjust_level(self, level_type: str, increase_count: int):
        """
        Adjust the current zombie level to match the expected level
        :return:
        """
        self.launcher.log_message(f'Adjusting zombie level - {level_type}, '
                                  f'{increase_count}')
        if level_type == 'INCREASE':
            self.launcher.mouse.set_position(
                self._increase_btn_cords.start_x,
                self._increase_btn_cords.start_y)
            center = GameHelper.get_center(self._increase_btn_cords)
            self.launcher.mouse.move(*center)
        elif level_type == 'DECREASE':
            self.launcher.mouse.set_position(
                self._decrease_btn_cords.start_x,
                self._decrease_btn_cords.start_y)
            center = GameHelper.get_center(self._decrease_btn_cords)
            self.launcher.mouse.move(*center)
        else:
            raise ZombieException('Level type not supported')
        time.sleep(1)
        for _ in range(increase_count):
            self.launcher.mouse.click()
            time.sleep(1)

    def set_zombie_level(self, level: int):
        """
        Set the zombie level. If level is greater than max level.
        Set to max level - 1

        :param level: The expected level.
        :returns: None
        """
        new_level = self.max_level if level > self.max_level else level
        # enforces new level is a positive real number
        new_level = new_level if new_level > 0 else 1
        current_level = self.get_zombie_current_level()
        increase_count = abs(new_level - current_level)
        self.launcher.log_message(f'Adjusting zombie level - {new_level}')
        if new_level > current_level:
            level_type = 'INCREASE'
            self._adjust_level(level_type, increase_count)
        elif new_level < current_level:
            level_type = 'DECREASE'
            self._adjust_level(level_type, increase_count)

    def zombie_city(self):
        """
        Activates the zombie city mode. Sets the game view
        to outside view
        :return:
        """
        self.launcher.set_view(OUTSIDE_VIEW)
