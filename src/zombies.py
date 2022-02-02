"""Responsible for killing zombies in the Game event"""
import threading
import time
from typing import Optional

import cv2
import numpy as np

from src.constants import OUTSIDE_VIEW, BOTTOM_IMAGE, LEFT_IMAGE, RIGHT_IMAGE, \
    TOP_IMAGE, ZOMBIE_MENU
from src.exceptions import ZombieException
from src.game_launcher import GameLauncher
from src.helper import GameHelper, Coordinates, retry
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
     - click on go to find any available zombie --- done
     - search and find the arrow that shows for about 6 secs
     before disappearing --- done
     - click on the given zombie (confirm it is the right zombie level) --- done
     - attack the zombie --- done
     - set out with the default formation --- done
     How do I know the zombie has been killed?
     - check the coordinate of the zombie and confirm the zombie is no more?
     - wait for period of time --- done

    How do I know my attack troops have returned?
     - I can get the duration time to the target during 'set out' and
     multiple it by two to know the amount of time to wait for before
     restarting the attack again.
     - I check if the 'attack en route' or 'attack withdraw' is no more showing.

     - continue attacks as far mobility is greater than given limit.

    """
    # time for an attack of a zombie in secs
    _attack_duration = 2

    def __init__(self, launcher: GameLauncher):
        self._fuel = None
        self.launcher = launcher
        self._max_level = None
        self._decrease_btn_cords: Optional[Coordinates] = None
        self._increase_btn_cords: Optional[Coordinates] = None
        self._attack_btn_cords: Optional[Coordinates] = None
        self._set_out_btn_cords: Optional[Coordinates] = None
        self.radar = Radar(self.launcher)
        self.fleets_data = {}

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
        green_min = (0, 140, 10)
        green_max = (7, 255, 75)
        white_min = (128, 128, 128)
        white_max = (255, 255, 255)

        green_channel = cv2.inRange(image, green_min, green_max)
        white_channel = cv2.inRange(image, white_min, white_max)

        green_sum = sum(sum(green_channel))
        white_sum = sum(sum(white_channel))
        if green_sum > white_sum:
            return green_channel
        return white_channel

    @retry(exception=ZombieException,
           message="Fuel value not readable",
           attempts=3)
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
        for ocr_settings in [6, 8]:
            custom_config = r'-c tessedit_char_whitelist=0123456789 ' \
                            fr'--oem 3 --psm {ocr_settings} '
            # extract the fuel value
            fuel_value = get_text_from_image(processed_image, custom_config)
            if fuel_value:
                break
        self.launcher.log_message(f"Current fuel - {fuel_value}")
        if fuel_value:
            return int(float(fuel_value.strip()))
        # Fuel value not readable error.
        cv2.imwrite('fuel-error2.png', fuel_image)
        cv2.imwrite('fuel-error-processed.png', processed_image)
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
        # clear radar screen
        self.launcher.mouse.set_position(
            self.launcher.app_coordinates.start_x,
            self.launcher.app_coordinates.start_y
        )
        center = GameHelper.get_center(
            self.launcher.app_coordinates)
        self.launcher.mouse.move(center)
        self.launcher.mouse.click()
        time.sleep(0.5)

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
            time.sleep(0.5)

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

    @retry(exception=ZombieException,
           message="No zombie arrow found",
           attempts=4)
    def find_zombie(self, level: int):
        """
        Find the a particular zombie of a given level.

        :param level: The target zombie level.
        :returns: None
        """
        self.set_zombie_level(level)
        button = self.radar.go_button
        self.launcher.mouse.set_position(button.start_x, button.start_y)
        center = GameHelper.get_center(button)
        self.launcher.mouse.move(*center)
        time.sleep(0.5)
        self.launcher.mouse.click()
        time.sleep(2)
        # take 3 different snapshots of the zombie and run through them all
        snapshot_data = []
        zombie_area_image = None
        for i in range(3):
            zombie_area_image, area_cords_relative = \
                self.launcher.get_screen_section(50, TOP_IMAGE)
            zombie_area_image, area_cords_relative = \
                self.launcher.get_screen_section(45, BOTTOM_IMAGE,
                                                 zombie_area_image,
                                                 area_cords_relative)
            zombie_data = (zombie_area_image, area_cords_relative)
            snapshot_data.append(zombie_data)
            time.sleep(1)

        zeros = np.zeros_like(zombie_area_image)
        t_h, t_w, _ = zombie_area_image.shape
        # now iterate through and find the best match
        for zombie_image, area_cords in snapshot_data:
            target_area = zombie_image[:,
                          int(0.3 * t_w):int(0.7 * t_w)
                          ]
            zeros[:, int(0.3 * t_w):int(0.7 * t_w)] = target_area
            self.launcher.log_message(
                '-------- Finding the zombie arrow --------')
            cords = self.launcher.find_target(
                zeros,
                self.launcher.target_templates('zombie-arrow'),
                threshold=0.1
            )
            if cords:
                zombie_area_cords_relative = area_cords
                break
        else:
            cv2.imwrite('zombie-arrow-error.png', zeros)
            raise ZombieException("No zombie arrow found")

        arrow = zeros[
                cords.start_y:cords.end_y,
                cords.start_x:cords.end_x
                ]
        cv2.imwrite('zombie-arrow-image1.png', zeros)
        cv2.imwrite('zombie-arrow-image2.png', arrow)

        cords_relative = GameHelper. \
            get_relative_coordinates(
            zombie_area_cords_relative, cords)
        self.launcher.mouse.set_position(cords_relative.start_x + 15,
                                         cords_relative.end_y + 150)
        time.sleep(0.2)
        self.launcher.mouse.move(1, 1)
        self.launcher.mouse.click()
        time.sleep(0.8)
        self.launcher.mouse.click()
        time.sleep(1)

    @retry(exception=ZombieException,
           message="No zombie attack button found",
           attempts=2)
    def attack_zombie(self) -> int:
        """
        Attack the current zombie shown on the display screen. It finds
        the zombie attack button and clicks on it.

        :return: The set out time.
        """
        self.launcher.log_message(
            '---------- Finding attack button --------------')
        if not self._attack_btn_cords:
            zombie_area_image, zombie_area_cords_relative = \
                self.launcher.get_screen_section(45, BOTTOM_IMAGE)
            zombie_area_image, zombie_area_cords_relative = \
                self.launcher.get_screen_section(50, TOP_IMAGE,
                                                 zombie_area_image,
                                                 zombie_area_cords_relative)
            cords = self.launcher.find_target(
                zombie_area_image,
                self.launcher.target_templates('zombie-attack'),
                threshold=0.2
            )
            if not cords:
                raise ZombieException("No zombie attack button found")

            cords_relative = GameHelper. \
                get_relative_coordinates(
                zombie_area_cords_relative, cords)
            self._attack_btn_cords = cords_relative

        self.launcher.mouse.set_position(self._attack_btn_cords.start_x,
                                         self._attack_btn_cords.start_y)
        center = GameHelper.get_center(self._attack_btn_cords)
        self.launcher.mouse.move(center)
        time.sleep(0.5)
        self.launcher.mouse.click()
        # send out fleet to the zombies
        time.sleep(3)
        time_out = self.send_fleet()
        self.launcher.log_message(f'----- time to target ----- {time_out}')
        return time_out

    def send_fleet(self) -> int:
        """
        Sends out a troop fleet out to the target and also returns their set
        out time.

        :return: The troop set out time.
        """
        position, time_out = self.find_set_out()
        self.launcher.mouse.set_position(position.start_x,
                                         position.start_y)
        time.sleep(0.8)
        self.launcher.mouse.move(GameHelper.get_center(position))
        self.launcher.mouse.click()
        return time_out

    @retry(exception=ZombieException,
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
                raise ZombieException("No set-out button found")
            cords_relative = GameHelper. \
                get_relative_coordinates(
                cords_relative, cords)
            self._set_out_btn_cords = cords_relative
        time_section = self.launcher.get_screenshot()[
                       self._set_out_btn_cords.start_y - 35:
                       self._set_out_btn_cords.start_y,
                       self._set_out_btn_cords.start_x:
                       self._set_out_btn_cords.end_x - 20]
        set_time = self.radar.get_set_out_time(time_section)
        return self._set_out_btn_cords, set_time

    def _kill_zombie(self, level: int):
        """
        Function responsible for killing zombie
        :param level:
        :return: The waiting time before calling again
        """
        # set to the radar view
        self.radar.select_radar_menu(ZOMBIE_MENU)
        self.find_zombie(level)
        set_time = self.attack_zombie()
        waiting_time = (set_time * 2) + self._attack_duration
        return waiting_time

    def _chech_mobility_limit(self, target: int,
                              current_fuel: int = None) -> bool:
        """
        Checks the fuel mobility is above the target
        :param target: The minimum allowed fuel value
        :return: True if there is still enough fuel
        """
        current_fuel = current_fuel if current_fuel else self.fuel
        if current_fuel < 10:
            # get the latest fuel value just in case
            current_fuel = self.fuel
        return current_fuel >= target

    def _initialize_fleet_data(self, size: int):
        """
        Initialize the fleet data structure
        :param size:
        :return:
        """
        for fleet_id in range(size):
            self.fleets_data[fleet_id] = None

    def _fleet_wait(self, fleet_id: int):
        """
        The Fleet thread used for waiting for the fleet to finish.
        :param fleet_id:
        :return:
        """
        # get the waiting time for the fleet
        waiting_time = self.fleets_data.get(fleet_id)
        if not waiting_time:
            return None
        # sleep for the waiting duration
        time.sleep(waiting_time)
        # reset the fleet data
        self.fleets_data[fleet_id] = None

    def kill_zombies(self, level: int,
                     min_mobility: int = 10,
                     fleet: int = 1):
        """
        Function responsible for killing zombies in the map

        :param fleet: The number of fleet to deploy. Defaults is 1
        :param level: The zombie level to target
        :param min_mobility: The min mobility to stop killing zombie
        :return:
        """
        self.zombie_city()
        min_mobility = min_mobility if min_mobility > 10 else 10
        self.launcher.log_message(
            f"------ Killing zombies at level {level} using {fleet} "
            "Fleets--------")
        self._initialize_fleet_data(fleet)
        global_stop = False
        min_time = 5
        fleet_threads = {}
        current_fuel = self.fuel
        while not global_stop:
            for fleet_id, fleet_time in self.fleets_data.items():
                if fleet_time:
                    continue
                if self._chech_mobility_limit(min_mobility, current_fuel):
                    waiting_time = self._kill_zombie(level)
                    min_time = waiting_time if \
                        waiting_time < min_time else min_time
                    # reduce the current fuel by 10
                    current_fuel = current_fuel - 10
                    self.fleets_data[fleet_id] = waiting_time
                    # activate the fleet_thread_waiting
                    fleet_thread = threading.Thread(
                        target=self._fleet_wait, args=(fleet_id,),
                        name=f"FleetWaitThread_{fleet_id}")
                    # save thread profile
                    fleet_threads[fleet_id] = fleet_thread
                    fleet_thread.start()
                else:
                    global_stop = True
                    break
            time.sleep(min_time)

        # make sure all threads have closed
        for fleet_thread in fleet_threads.values():
            fleet_thread.join()

        self.launcher.log_message(
            '------ Fuel is below minimum level -------')
