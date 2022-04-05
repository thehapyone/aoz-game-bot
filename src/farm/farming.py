"""Responsible for different farming activities"""
import time
from typing import Tuple, Optional

import cv2
import numpy as np

from src.constants import INSIDE_VIEW, OUTSIDE_VIEW, BOTTOM_IMAGE, TOP_IMAGE, \
    RIGHT_IMAGE, LEFT_IMAGE
from src.exceptions import FarmingException, RadarException
from src.game_launcher import GameLauncher
from src.helper import GameHelper, Coordinates, retry
from src.ocr import get_text_from_image
from src.radar import Radar


class Farm:
    """
    The farming class.

    In order to be able to send troops to go farm,
    the below are thing things that needs to be sorted out:

     - Get max fleet size
     - Get current no of fleets used and available.
     - Ability to switch to outside city
     - Find and click on the radar button
     - Select a particular farming type
     - Increase and decrease the farming level
     - Get the current farming level
     - Click on the go to find the next available farm.
     - Detect the gather button and click on it to go gather.
     - Set out troops if any troops are available (atleast 10% of the max
     troops is needed to gather effectively)
     - Ability to find lower farm if current level not available.
     - Set out with the default formation
    """

    def __init__(self,
                 farm_type: int,
                 farm_level: int,
                 launcher: GameLauncher):
        self._farm_type = farm_type
        self.level = farm_level
        self.launcher = launcher
        self._max_fleet, self._current_fleet = None, None
        self._wounded_count = None
        self._total_units, self._idle_units = None, None
        self.radar = Radar(self.launcher)

    @property
    def max_fleet(self) -> int:
        """
        Returns the max fleet possible
        :return: Max fleet
        """
        if not self._max_fleet:
            self.get_fleet_count()
        return self._max_fleet

    @property
    def current_fleet(self) -> int:
        """
        Returns the current fleet
        :return: Current fleet value
        """
        if self._current_fleet is None:
            self.get_fleet_count()
        return self._current_fleet

    def find_garage(self) -> Coordinates:
        """
        Finds the garage location in the city and return the center position.
        Returns None if it could find it.

        :returns: The garage screen coordinates
        """
        self.launcher.set_view(OUTSIDE_VIEW)
        # then set back to city view to reset the city view position
        self.launcher.set_view(INSIDE_VIEW)
        # Now set the cursor to the center of the game screen
        center = GameHelper.get_center(self.launcher.app_coordinates)
        # Move the mouse to the center
        self.launcher.mouse.set_position(self.launcher.app_coordinates.start_x,
                                         self.launcher.app_coordinates.start_y)
        self.launcher.mouse.move(center[0] - 100, center[1] - 150)
        center_position = self.launcher.mouse.position
        count = 4
        self.launcher.log_message(
            '------- Dragging mouse to garage view -------')
        # Drag the mouse left three times
        for i in range(count):
            self.launcher.mouse.drag(200, 0)
            time.sleep(0.5)
            self.launcher.mouse.set_position(center_position.x,
                                             center_position.y)
            time.sleep(0.3)
        self.launcher.mouse.drag(0, -150)
        # Now we should be in the garage view.
        garage_image, garage_area_cords_relative = \
            self.launcher.get_screen_section(50, BOTTOM_IMAGE)

        cords = self.launcher.find_target(
            garage_image,
            self.launcher.target_templates('garage'),
            threshold=0.2
        )
        if not cords:
            raise FarmingException("Unable to find the Garage")
        cords_relative = GameHelper.get_relative_coordinates(
            garage_area_cords_relative, cords)
        return cords_relative

    def extract_fleet_values(self):
        """
        Find the fleet queue section and other troop information.
        The information returned contains data about the current fleet count,
        max fleet, the current wounded count, total units, and lastly the
        number of idle units.
        """
        fleet_image, area_cords_relative = self.launcher. \
            get_screen_section(25, TOP_IMAGE)
        fleet_image, area_cords_relative = self.launcher. \
            get_screen_section(46, BOTTOM_IMAGE, source=fleet_image,
                               reference_coords=area_cords_relative)

        fleet_image_1, area_cords_relative = self.launcher. \
            get_screen_section(45, LEFT_IMAGE, source=fleet_image,
                               reference_coords=area_cords_relative)

        fleet_image_2, area_cords_relative = self.launcher. \
            get_screen_section(40, RIGHT_IMAGE, source=fleet_image,
                               reference_coords=area_cords_relative)

        # send to ocr for analysis.
        white_min = (110, 110, 110)
        white_max = (255, 255, 255)

        custom_config = r'--oem 3 --psm 6'
        # Process the fleet queues and wounded data
        white_channel = cv2.inRange(fleet_image_2, white_min, white_max)
        fleet_wounded_data = self._process_queues_and_wounded_data(
            custom_config, white_channel)

        # Process the total and idle units data
        white_channel = cv2.inRange(fleet_image_1, white_min, white_max)
        total_and_idle_data = self._process_total_and_idle_data(
            custom_config, white_channel)

        return fleet_wounded_data, total_and_idle_data

    @staticmethod
    def _extract_separator_values(separator_data: str):
        """An helper function for separator extraction"""
        if not separator_data:
            return None, None
        pre_separator = separator_data.split(' ')[-1]
        separator_values = pre_separator.split('/')
        return int(separator_values[0].replace(",", "")), \
               int(separator_values[1].replace(",", ""))

    def _process_queues_and_wounded_data(
            self, custom_config, image) -> Tuple[int, int, Optional[int]]:
        """Process and the Fleet queue and Wounded data information"""
        # extract the text
        image_ocr = get_text_from_image(
            image, custom_config).lower().strip()
        if not image_ocr:
            raise FarmingException("Fleet Queues could not be fetched")
        fleets_data = None
        wounded_data = None
        for data in image_ocr.splitlines():
            if not data.strip():
                continue
            if "fleet" in data or "queues" in data:
                fleets_data = data.strip()
                continue
            if "wounded" in data or "units" in data:
                wounded_data = data.strip()
        if not fleets_data:
            raise FarmingException("Fleet Queues section not in OCR result. "
                                   f"Response - {image_ocr}")
        # extracts out the fleet values
        try:
            current_fleet, max_fleet = self._extract_separator_values(
                fleets_data)
        except ValueError:
            raise FarmingException(
                f"Fleet Queues values is invalid: {fleets_data}")
        # extracts out the wounded values
        try:
            current_wounded, _ = self._extract_separator_values(wounded_data)
        except Exception as error:
            self.launcher.log_message(
                f"Invalid wounded values detected - {wounded_data}. Error: "
                f"{str(error)}")
            current_wounded = None
        return current_fleet, max_fleet, current_wounded

    def _process_total_and_idle_data(
            self, custom_config, image) -> Tuple[Optional[int], Optional[int]]:
        """Process the total units and idle units data"""
        # extract the text
        image_ocr = get_text_from_image(
            image, custom_config).lower().strip()
        if not image_ocr:
            self.launcher.log_message(
                "Total and idle units data not fetched")
            return None, None
        total_units_data = None
        idle_units_data = None
        for data in image_ocr.splitlines():
            if not data.strip():
                continue
            if "total" in data:
                total_units_data = data.strip()
                continue
            if "idle" in data:
                idle_units_data = data.strip()

        def get_units_value(units_data: Optional[str]):
            if not units_data:
                return None
            value = units_data.split(" ")[-1]
            try:
                return int(value.replace(",", ""))
            except Exception as error:
                self.launcher.log_message(
                    f"Invalid value detected - {units_data}. Error: "
                    f"{str(error)}")
            return None

        return get_units_value(total_units_data), \
               get_units_value(idle_units_data)

    def get_fleet_count(self):
        """
        Fetches and get the current game max fleet. It can
        also return the game current fleet as well if available.

        The max fleet size can be gotten from the garage under
        the troops management.
        :return: Int
        """
        # get the garage
        garage_cords = self.find_garage()
        garage_center = GameHelper.get_center(garage_cords)
        # click on garage
        self.launcher.mouse.set_position(garage_cords.start_x,
                                         garage_cords.start_y)
        self.launcher.mouse.move(garage_center)
        self.launcher.mouse.click()
        time.sleep(1)
        # now find the fleet army button
        garage_image, garage_area_cords_relative = \
            self.launcher.get_screen_section(50, BOTTOM_IMAGE)
        cords = self.launcher.find_target(
            garage_image,
            self.launcher.target_templates('garage-fleet'),
            threshold=0.2
        )
        if not cords:
            raise FarmingException("Unable to find the Garage Fleet button")
        cords_relative = GameHelper.get_relative_coordinates(
            garage_area_cords_relative, cords)
        fleet_center = GameHelper.get_center(garage_cords)

        # click on the fleet button
        self.launcher.mouse.set_position(cords_relative.start_x,
                                         cords_relative.start_y)
        self.launcher.mouse.move(fleet_center)
        self.launcher.mouse.click()
        time.sleep(1)

        # now we should have the fleet screen.
        fleet_wounded_data, units_data = self.extract_fleet_values()
        self._current_fleet, self._max_fleet, self._wounded_count = \
            fleet_wounded_data
        self._total_units, self._idle_units = units_data

        # reset view back
        self.launcher.keyboard.back()

    @retry(exception=FarmingException,
           message="No farm gather button found",
           attempts=4)
    def find_farm(self):
        """
        Find a particular farm of a given level.

        :returns: true or false if farming conflict
        """
        self.radar.set_level(self.level, 6)
        button = self.radar.go_button
        self.launcher.mouse.set_position(button.start_x, button.start_y)
        center = GameHelper.get_center(button)
        self.launcher.mouse.move(*center)
        time.sleep(0.5)
        self.launcher.mouse.click()
        time.sleep(1)
        self.launcher.mouse.click()
        time.sleep(2)

        # take 3 different snapshots
        snapshot_data = []
        gather_area_image = None
        for i in range(3):
            gather_area_image, area_cords_relative = \
                self.launcher.get_screen_section(60, TOP_IMAGE)
            gather_area_image, area_cords_relative = \
                self.launcher.get_screen_section(45, BOTTOM_IMAGE,
                                                 gather_area_image,
                                                 area_cords_relative)
            gather_data = (gather_area_image, area_cords_relative)
            snapshot_data.append(gather_data)
            time.sleep(0.5)
        zeros = np.zeros_like(gather_area_image)
        t_h, t_w, _ = gather_area_image.shape
        # now iterate through and find the best match
        for gather_image, area_cords in snapshot_data:
            target_area = gather_image[:,
                          int(0.5 * t_w):int(0.9 * t_w)
                          ]
            zeros[:, int(0.5 * t_w):int(0.9 * t_w)] = target_area
            self.launcher.log_message(
                '-------- Finding the farm gather button --------')
            cords = self.launcher.find_target(
                zeros,
                self.launcher.target_templates('farming'),
                threshold=0.2
            )
            if cords:
                break
        else:
            cv2.imwrite('../farming-gather-error.png', zeros)
            raise FarmingException("No farm gather button found")

        cords_relative = GameHelper. \
            get_relative_coordinates(area_cords, cords)
        self.launcher.mouse.set_position(cords_relative.start_x,
                                         cords_relative.start_y)
        center = GameHelper.get_center(cords_relative)
        self.launcher.mouse.move(center)
        self.launcher.mouse.click()
        time.sleep(1)
        self.launcher.mouse.click()
        time.sleep(1)

        # We check for potential conflict
        # if conflict - cancel my fleet action.
        fleet_conflict = self.radar.check_fleet_conflict(0)
        if fleet_conflict:
            self.launcher.log_message('Current target is already taken by '
                                      'someone else.')
        return fleet_conflict

    def deploy_troops(self) -> int:
        """
        Deploy the troops to go farm.

        :return: The set out time.
        """
        try:
            time_out = self.radar.send_fleet()
        except RadarException as error:
            if str(error) == "Can not extract set out time":
                time_out = 0
            else:
                raise error

        if not time_out:
            # no available troops left to deploy. Signal end of farming mode.
            self.launcher.log_message("no more troops to deploy")
        self.launcher.log_message(f'----- time to target ----- {time_out}')
        return time_out

    @retry(exception=FarmingException,
           message="Out of levels for farming",
           attempts=2)
    def gather_farm(self) -> None:
        """
        Function responsible for going to gather farm.
        
        :return: None
        """
        # set to the radar view
        self.radar.select_radar_menu(self._farm_type)
        while self.level:
            try:
                conflict = self.find_farm()
                if not conflict:
                    break
            except FarmingException as error:
                if str(error) == "No farm gather button found":
                    # try again with a lower level
                    self.level = self.level - 1
                    if not self.level:
                        raise error
                else:
                    raise error

        if not self.level:
            self.level = 6
            raise FarmingException("Out of levels for farming")

        # now we deploy the troops to go farm
        set_time = self.deploy_troops()
        if not set_time:
            # go back to the main screen.
            self.launcher.keyboard.back()
            raise FarmingException("Out of troops")

    def all_out_farming(self):
        """
        Sends all the available troops to go farm

        :return:
        """
        # get current and max fleet
        self.get_fleet_count()
        # set farming view
        self.launcher.set_view(OUTSIDE_VIEW)

        self.launcher.log_message(
            f"------ Farming with a max fleet of {self.max_fleet} fleets"
            f" and current fleet of {self.current_fleet} fleets --------")

        min_time = 2

        def commence_farming():
            current_fleet = self.current_fleet
            while True:
                if current_fleet < self.max_fleet:
                    try:
                        self.gather_farm()
                        # increase the current fleet by 1
                        current_fleet = current_fleet + 1
                    except FarmingException as error:
                        if str(error) in ["Out of troops",
                                          "Out of levels for farming"]:
                            break
                        raise error
                else:
                    break
                time.sleep(min_time)

        # Go farming only when we have available troops in the first place
        if self._idle_units and self._idle_units > 2000:
            self.launcher.log_message(
                f"------ City has a total of {self._idle_units} idle units "
                f"----------")
            commence_farming()
        # go farming if idle units not available
        elif self._idle_units is None:
            commence_farming()

        self.launcher.log_message(
            '------ All troops deployed for farming -------')
