import subprocess
import time
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Optional, List, Union

import cv2 as cv
import imutils
import numpy as np
from mss import mss
from numpy import ndarray

from src.constants import BOTTOM_IMAGE, TOP_IMAGE, LEFT_IMAGE, INSIDE_VIEW, \
    OUTSIDE_VIEW
from src.exceptions import LauncherException
from src.helper import Coordinates, GameHelper, retry, click_on_target
from src.listener import MouseController, KeyboardController
from src.ocr import get_box_from_image


class GameLauncher:
    """
    The Game Launcher class. This class is responsible for the following:
     - Start the game app if not started already.
     - launch the AoZ app
    """
    instance = None
    game_path = 'C:\Program Files\BlueStacks_nxt\HD-Player.exe'
    cwd = Path(__file__).cwd()

    cache_file = cwd.joinpath("data", "game_cache.txt")

    _templates_path = {
        "app": str(cwd.joinpath("data", "app")),
        "game": str(cwd.joinpath("data", "game", "app_icon")),
        "rewards": str(cwd.joinpath("data", "game", "rewards")),
        "mobility": str(cwd.joinpath("data", "game", "mobility")),
        "city-icon": str(cwd.joinpath("data", "game", "city_icon")),
        "outside-icon": str(cwd.joinpath("data", "game", "outside_icon")),
        "radar": str(cwd.joinpath("data", "game", "radar")),
        "go-button": str(cwd.joinpath("data", "game", "go_button")),
        "setout": str(cwd.joinpath("data", "game", "setout")),
        "zombie-arrow": str(cwd.joinpath("data", "game",
                                         "zombie_arrow")),
        "zombie-attack": str(cwd.joinpath("data", "game",
                                          "zombie_attack")),
        "zombie-decrease": str(cwd.joinpath("data", "game",
                                            "zombie_decrease")),
        "zombie-increase": str(cwd.joinpath("data", "game",
                                            "zombie_increase")),
        "garage": str(cwd.joinpath("data", "game",
                                   "garage")),
        "garage-fleet": str(cwd.joinpath("data", "game",
                                         "garage_fleet")),
        "fleet-conflict": str(cwd.joinpath("data", "game",
                                           "fleet_conflict")),
        "fleets": str(cwd.joinpath("data", "game",
                                   "fleets")),
        "farming": str(cwd.joinpath("data", "game",
                                    "farming")),
        "switch-account": str(cwd.joinpath("data", "game",
                                           "switch_account")),
        "switch-account-login": str(cwd.joinpath("data", "game",
                                                 "switch_account_login")),
        "location-finder": str(cwd.joinpath("data", "game",
                                            "location_finder")),
        "battle_button": str(cwd.joinpath("data", "game",
                                          "battle_button")),
        "elite_zombie_skip": str(cwd.joinpath("data", "game",
                                              "elite_zombie_skip")),
    }
    IMG_COLOR = cv.IMREAD_COLOR

    location_finder_btn = None
    location_cords_relative = None

    def __init__(self, mouse: MouseController,
                 keyboard: KeyboardController,
                 enable_debug=True, cache: bool = False):
        self._app_templates = None
        self.app_pid = None
        self._mss = mss()
        self._debug = enable_debug
        self._app_coordinates: Optional[Coordinates] = None
        self._game_coordinates: Optional[Coordinates] = None
        self._aoz_launched = None
        self._mouse = mouse
        self._keyboard = keyboard
        self._cache = cache

    @property
    def mouse(self):
        """Returns the mouse object"""
        return self._mouse

    @property
    def keyboard(self):
        """Returns the keyboard object"""
        return self._keyboard

    def _load_cache_coordinates(self) -> bool:
        """Loads the saved cached coordinates and returns True or False"""
        try:
            with open(self.cache_file, 'r') as file:
                cache_data = file.readlines()
                location_data = cache_data[0].strip().split(':')[-1].split(',')
                cords = Coordinates(
                    start_x=int(location_data[0]),
                    start_y=int(location_data[1]),
                    end_x=int(location_data[2]),
                    end_y=int(location_data[3])
                )
            self._app_coordinates = cords
            return True
        except Exception:
            return False

    def clear_cache(self):
        """Clear the cache data"""
        with open(self.cache_file, 'w') as file:
            file.write("")

    def start_game(self):
        """
        Starts and prep the AoZ game app
        :return:
        """
        self.log_message(
            "############## Launching Bluestack App now ##############")
        self.launch_app()

        if self._cache and self._load_cache_coordinates():
            self.log_message(
                "############## Using cached coordinates for app "
                "##############")
        else:
            self.log_message("############## Finding the app screen "
                             "##############")
            self.find_app()

        # check if the game app is loaded or not.
        self.log_message(
            "############# Finding the game app ##############")
        self.find_game()

        self.log_message("############# Launching game now ##############")
        self.launch_aoz()

    def launch_app(self):
        """Launches the main android bluestack app"""
        self.app_pid = GameHelper.is_app_running()
        if self.app_pid is None:
            pid = subprocess.Popen(self.game_path, shell=False,
                                   stderr=None, stdout=None,
                                   stdin=None).pid
            if pid:
                self.app_pid = pid
            else:
                raise LauncherException("Error launching bluestack app")
            # wait for the app to be ready.
            time.sleep(20)

    def reset_to_home(self):
        """Use for resetting the game screen back to city home"""
        attempts = 10
        # click and set view to game screen
        self.mouse.set_position(self._app_coordinates.start_x + 50,
                                self._app_coordinates.start_y + 50)
        self.mouse.click()
        time.sleep(2)

        # First we check for a case were either the Confirm or Cancel popup
        # shows blocking the use of 'esc' keyword
        confirm_area_image, area_cords_relative = self.get_confirm_view()
        # find the target and click on it.
        custom_config = r'--oem 3 --psm 6'

        white_min = (128, 128, 128)
        white_max = (255, 255, 255)
        white_channel = cv.inRange(confirm_area_image, white_min, white_max)

        special_case = self.find_ocr_target("Cancel", white_channel,
                                            custom_config)

        if special_case:
            # TODO : Remove this after successful debugging
            file_name = "special_case_" + datetime.now().strftime(" \
                        ""%d-%m-%yT%H-%M-%S") + ".png"
            cv.imwrite(file_name, self.get_game_screen())
            click_on_target(special_case,
                            area_cords_relative,
                            self.mouse)

        while attempts:
            # go back one view
            self.keyboard.back()
            time.sleep(2)
            exit_area_image, area_cords_relative = \
                self.get_screen_section(60, BOTTOM_IMAGE)
            exit_area_image, area_cords_relative = \
                self.get_screen_section(30, TOP_IMAGE,
                                        exit_area_image,
                                        area_cords_relative)
            # search for target
            custom_config = r'--oem 3 --psm 3'
            white_min = (193, 193, 193)
            white_max = (255, 255, 255)
            white_channel = cv.inRange(exit_area_image, white_min,
                                       white_max)
            location = self.find_ocr_target("Exit", white_channel,
                                            custom_config)
            if location:
                # now in exit view
                self.keyboard.back()
                self.log_message(
                    "------- View now back to home ---------")
                break
            attempts = attempts - 1

    def get_rewards(self):
        """Get the rewards that shows on the home screen"""
        rewards_area_image, area_cords_relative = \
            self.get_screen_section(35, BOTTOM_IMAGE)

        self.log_message("Finding the available rewards button.")

        rewards_location = self.find_target(
            rewards_area_image,
            self.target_templates('rewards'),
            threshold=0.2)

        if rewards_location:
            click_on_target(rewards_location,
                            area_cords_relative,
                            self.mouse)
            time.sleep(1)
            # click again to remove the notification of the rewards collected
            self._mouse.click()
            time.sleep(5)

    def launch_aoz(self):
        """Launch the AOZ app if not already launched"""
        if not self._aoz_launched:
            # find center of the game app
            start_x, start_y, end_x, end_y = self._game_coordinates
            center_x, center_y = (int((end_x - start_x) / 2.0),
                                  int((end_y - start_y) / 2.0))
            self._mouse.set_position(start_x, start_y)
            self._mouse.move(center_x, center_y)
            self._mouse.click()
            # wait for the game to load
            time.sleep(45)
            # now we click on the reward that popups on the game screen.
            self.get_rewards()
            # Reset the game scree and reset any displayed offers
            self.reset_to_home()

            # self game is alive now.
            self.log_message("Game now active")
            # shake to collect available resources
            self._keyboard.shake()
            time.sleep(5)

    @property
    def screen_image_path(self) -> str:
        """Returns te path for the screenshot"""
        return str(self.cwd.joinpath("data", "screenshot.png"))

    def get_screenshot(self) -> np.ndarray:
        """Takes a screenshot of the current monitor screen"""
        self._mss.shot(mon=1, output=self.screen_image_path)
        self._mss.close()
        screen_image = cv.imread(self.screen_image_path, self.IMG_COLOR)
        return screen_image

    def get_game_screen(self) -> np.ndarray:
        """
        Returns the current game screen. Used when the game screen has
        been updated.

        :returns: The current game screen.
        """
        screen_image = self.get_screenshot()
        start_x, start_y, end_x, end_y = self._app_coordinates
        game_screen = screen_image[start_y:end_y, start_x:end_x]
        return game_screen

    def get_screen_section(self,
                           percentage: float,
                           position: int,
                           source: np.ndarray = None,
                           reference_coords: Coordinates = None) \
            -> tuple[np.ndarray, Coordinates]:
        """
        Gets a percentage of the game screen and return that section only.

        :param reference_coords: An alternate reference coordinates
        :param source: Input image to extract section from.
        :param percentage: Percentage of the screen
        :param position: Whether it's top - 0, bottom - 1, left - 2 or right
            - 3 of the screen.
        :return: Returns an image section
        """
        screen = self.get_game_screen() if source is None else source
        t_h, t_w, _ = screen.shape
        new_th = int((percentage / 100) * t_h)
        new_tw = int((percentage / 100) * t_w)
        if position == TOP_IMAGE:
            section_coordinates = Coordinates(
                start_x=0,
                start_y=0,
                end_x=t_w,
                end_y=new_th
            )
        elif position == BOTTOM_IMAGE:
            section_coordinates = Coordinates(
                start_x=0,
                start_y=t_h - new_th,
                end_x=t_w,
                end_y=t_h
            )
        elif position == LEFT_IMAGE:
            section_coordinates = Coordinates(
                start_x=0,
                start_y=0,
                end_x=new_tw,
                end_y=t_h
            )
        else:
            section_coordinates = Coordinates(
                start_x=t_w - new_tw,
                start_y=0,
                end_x=t_w,
                end_y=t_h
            )

        section_coordinates_relative = GameHelper. \
            get_relative_coordinates(
            self._app_coordinates if not reference_coords else reference_coords,
            section_coordinates)
        section_image = screen[
                        section_coordinates.start_y:section_coordinates.end_y,
                        section_coordinates.start_x:section_coordinates.end_x]
        return section_image, section_coordinates_relative

    def bottom_menu(self) -> tuple[np.ndarray, dict[int, Coordinates],
                                   Coordinates]:
        """
        Gets the game button menu.

        :return: An enum of the game menu.
        """
        bottom_menu, bottom_coordinates_relative = \
            self.get_screen_section(10, BOTTOM_IMAGE)
        # extract and categorizes all bottom menu.
        # first menu is about 20% and the others share 16%
        t_h, t_w, _ = bottom_menu.shape
        city_icon_end_width = int(0.20 * t_w)
        city_cords = Coordinates(start_x=0, end_x=city_icon_end_width,
                                 start_y=0, end_y=t_h)
        city_cords_relative = GameHelper.get_relative_coordinates(
            bottom_coordinates_relative, city_cords
        )
        menu_dict = {0: city_cords_relative}

        icon_width = int(0.16 * t_w)
        end_width = city_icon_end_width
        for count in range(1, 6):
            start_width = end_width
            end_width = start_width + icon_width
            if end_width > t_w:
                end_width = t_w
            menu_icon_cords = Coordinates(start_x=start_width, end_x=end_width,
                                          start_y=0, end_y=t_h)
            menu_icon_cords_relative = GameHelper.get_relative_coordinates(
                bottom_coordinates_relative, menu_icon_cords
            )
            menu_dict[count] = menu_icon_cords_relative
        return bottom_menu, menu_dict, bottom_coordinates_relative

    def set_view(self, view: int):
        """
        Set the game view from with inside city or outside the city
        :param view: Either activate the inside city or outside city view.
        Possible values are - 1 for inside city and 2 for outside city.
        :return: None
        """
        bottom_image, _, coordinates = self.bottom_menu()
        cords = self.find_target(
            bottom_image,
            self.target_templates('city-icon'),
            threshold=0.2
        )
        if view == INSIDE_VIEW:
            # go to inside city view
            if cords:
                self.log_message(
                    "------ Now in city view mode ------")
                return
            cords = self.find_target(
                bottom_image,
                self.target_templates('outside-icon'))
            if not cords:
                raise LauncherException(
                    "View changing could not be completed.")
            center = GameHelper.get_center(cords)
            self._mouse.set_position(coordinates.start_x,
                                     coordinates.start_y)
            self._mouse.move(center)
            self._mouse.click()
            time.sleep(10)
            self.log_message(
                "------ Now in city view mode ------")
            return
        if view == OUTSIDE_VIEW:
            # go to outside city view
            if not cords:
                self.log_message(
                    "------ Now in outside city view mode ------")
                return
            center = GameHelper.get_center(cords)
            self._mouse.set_position(coordinates.start_x,
                                     coordinates.start_y)
            self._mouse.move(*center)
            self._mouse.click()
            time.sleep(15)
            self.log_message(
                "------ Now in outside city view mode ------")
            return
        raise LauncherException(f"View mode {view} not supported")

    @retry(exception=LauncherException,
           message="Game app not detected. Bot can't proceed",
           attempts=2)
    def find_game(self):
        """
        Helper function for finding the coordinates of the AoZ game app
        :return:
        """
        location = self.find_target(self.get_game_screen(),
                                    self.target_templates('game'))

        if location:
            self._aoz_launched = False
            # extract the coordinates in reference to the main screen
            self._game_coordinates = GameHelper.get_relative_coordinates(
                self._app_coordinates, location)
            time.sleep(1)
            return

        # otherwise, check if the game has already launched
        game_launched = self.find_target(self.get_screenshot(),
                                         self.target_templates('app'))

        if not game_launched:
            # set back to home screen
            self.keyboard.home()
            time.sleep(1)
            raise LauncherException(
                "Game app not detected. Bot can't proceed")

        # aoz already launched
        self._aoz_launched = True

    @retry(exception=LauncherException,
           message="Bluestack screen not detected. Bot can't proceed",
           attempts=2)
    def find_app(self):
        """
        Helper function for finding the coordinates of the bluestack android
        emulator app. It returns the bound box location of the screen
        :return:
        """
        # go home first
        self.keyboard.home()
        time.sleep(2)
        # take the screenshot
        screen_image = self.get_screenshot()
        location = self.find_target(screen_image,
                                    self.target_templates('app'))
        if not location:
            raise LauncherException(
                "Bluestack screen not detected. Bot can't proceed")
        self._app_coordinates = location
        self.log_message(f"App Coordinates - {self._app_coordinates}")

        # save the latest coordinates to the cache directory
        with open(self.cache_file, 'w') as file:
            cords_data = f"Location:{self._app_coordinates.start_x}," \
                         f"{self._app_coordinates.start_y}," \
                         f"{self._app_coordinates.end_x}," \
                         f"{self._app_coordinates.end_y}\n"
            file.write(cords_data)

    def find_target(self, reference: np.ndarray,
                    target: List[np.ndarray],
                    threshold: float = None) \
            -> Optional[Coordinates]:
        """
        Helper function for finding the coordinates of the
        of a given target in a reference image. It returns the bounding box
        location of the game app.

        :param reference: The reference input image.
        :param target: The template target.
        :param threshold: The target threshold for detection.
        :returns: Returns the coordinates of the target.
        """
        rgb_channel = True if len(reference.shape) == 3 else False
        # track matching history
        found = None
        # loop over for the best template match from a series of templates
        for template in target:
            for scale in np.linspace(0.05, 1.0, 20)[::-1]:
                # resize the image according to the scale, and keep track
                # of the ratio of the resizing
                resized = imutils.resize(
                    reference.copy(),
                    width=int(reference.shape[1] * scale))
                # if the resized image is smaller than the template, then break
                # from the loop
                t_w, t_h = template.shape[1], template.shape[0]

                if resized.shape[0] < t_h or resized.shape[1] < t_w:
                    break
                # Apply template Matching
                res = cv.matchTemplate(resized, template,
                                       method=cv.TM_SQDIFF_NORMED)
                min_val, _, min_loc, _ = cv.minMaxLoc(res)
                if found is None or min_val < found[1]:
                    r = reference.shape[1] / float(resized.shape[1])
                    found = (template, min_val, min_loc, r)

        (template, min_val, min_loc, r) = found
        self.log_message(f'Matching min value: {min_val}')
        if min_val == 1:
            self.log_message("Target image not found")
            return None
        # unpack the bookkeeping variable and compute the (x, y) coordinates
        # of the bounding box based on the resized ratio
        t_w, t_h = template.shape[1], template.shape[0]

        start_x, start_y = (int(min_loc[0] * r), int(min_loc[1] * r))
        end_x, end_y = (int((min_loc[0] + t_w) * r),
                        int((min_loc[1] + t_h) * r))
        found_template = reference[start_y:end_y, start_x:end_x]
        resize_found_template = cv.resize(found_template, (t_h, t_w))

        # calculate the HOG vector representation
        feature_vec_template, _ = GameHelper.calculate_hog(
            template,
            rgb_channel)
        feature_vec_match, _ = GameHelper.calculate_hog(
            resize_found_template,
            rgb_channel)

        # calculate Cosine Similarity python
        cosine_score = GameHelper.cosine_similarity(
            feature_vec_template, feature_vec_match)
        self.log_message(f"Cosine score: {cosine_score}")

        threshold = threshold if threshold else 0.55
        if min_val < threshold and cosine_score > 0.50:
            self.log_message(
                f"Region is TopLeft: ({start_x}, {start_y}) and "
                f"bottomLeft: ({end_x}, {end_y})")
            return Coordinates(start_x, start_y, end_x, end_y)
        else:
            self.log_message("Target image not found")
        return None

    def _load_all_templates(self, templates_dir: str) -> List[np.ndarray]:
        """Loads all the target template files found in the path folder"""
        templates_path = Path(templates_dir)
        if not templates_path.is_dir():
            raise Exception("Only directory are allowed")
        template_images = []
        for image_path in templates_path.glob('template_*.png'):
            template_images.append(cv.imread(str(image_path),
                                             self.IMG_COLOR))
        if not template_images:
            raise Exception("No template image found.")
        return template_images

    def target_templates(self, target: str) -> List[np.ndarray]:
        """Return all the target specified templates"""
        try:
            directory = self._templates_path[target.lower()]
        except KeyError:
            raise Exception(f"Target {target} is not recognized")
        return self._load_all_templates(directory)

    def log_message(self, message: str):
        """Prints to log if enabled"""
        if self._debug:
            print(message)

    @property
    def app_coordinates(self):
        return self._app_coordinates

    @cached_property
    def get_account_menu(self):
        """
        Returns the account menu coordinates.
        :return:
        """
        account_section, account_cords_relative = \
            self.get_screen_section(10, BOTTOM_IMAGE)

        t_h, t_w, _ = account_section.shape

        account_options = {}
        icon_width = int(0.25 * t_w)
        end_width = 0
        for count in range(4):
            start_width = end_width
            end_width = start_width + icon_width
            if end_width > t_w:
                end_width = t_w
            cords_relative = GameHelper.get_relative_coordinates(
                account_cords_relative,
                Coordinates(start_width, 0, end_width, t_h))
            account_options[count] = cords_relative
        return account_options

    @staticmethod
    def find_ocr_target(target: Union[str, List[str]],
                        image, config: str = "", partial: bool = False) -> \
            Optional[Coordinates]:
        """
        Finds the location of a target text
        and returns the first match of the bounding box
        """
        location = get_box_from_image(target, image, config=config,
                                      partial=partial)
        if not location:
            return None
        return location

    def get_confirm_view(self) -> tuple[ndarray, Coordinates]:
        """Returns an image of the confirm and cancel area"""
        confirm_area_image, area_cords_relative = \
            self.get_screen_section(50, BOTTOM_IMAGE)
        confirm_area_image, area_cords_relative = \
            self.get_screen_section(20, TOP_IMAGE,
                                    confirm_area_image,
                                    area_cords_relative)
        return confirm_area_image, area_cords_relative

    def find_a_city(self, name: str):
        """
        Finds a city in the map and take a snapshot of the location.
        :param name:
        :return:
        """

        def click_location_finder():
            if not self.location_finder_btn:
                location_area_image, self.location_cords_relative = \
                    self.get_screen_section(30, BOTTOM_IMAGE)

                self.location_finder_btn = self.find_target(
                    location_area_image,
                    self.target_templates('location-finder'),
                    threshold=0.25
                )
                if not self.location_finder_btn:
                    raise LauncherException("Location position not found")

            click_on_target(self.location_finder_btn,
                            self.location_cords_relative,
                            self.mouse, center=True)

        def find_x_y_input():
            area_image, area_cords_relative = \
                self.get_screen_section(55, BOTTOM_IMAGE)
            area_image, area_cords_relative = \
                self.get_screen_section(10, TOP_IMAGE,
                                        area_image,
                                        area_cords_relative)
            # find position X and position Y
            width = area_cords_relative.end_x - area_cords_relative.start_x
            mid_width = int(0.5 * width)
            x_btn = Coordinates(
                start_y=area_cords_relative.start_y,
                end_y=area_cords_relative.end_y,
                start_x=int((area_cords_relative.start_x + mid_width) *
                            0.5),
                end_x=int((area_cords_relative.start_x + mid_width) * 0.9)
            )

            y_btn = Coordinates(
                start_y=area_cords_relative.start_y,
                end_y=area_cords_relative.end_y,
                start_x=int(area_cords_relative.end_x * 0.6),
                end_x=int(area_cords_relative.end_x * 0.8),
            )
            return (x_btn, y_btn)

        def find_go_btn():
            area_image, area_cords_relative = \
                self.get_screen_section(50, BOTTOM_IMAGE)
            area_image, area_cords_relative = \
                self.get_screen_section(30, TOP_IMAGE,
                                        area_image,
                                        area_cords_relative)

            # Find the go button
            go_button_cords = self.find_target(
                area_image,
                self.target_templates('go-button'),
                threshold=0.25
            )
            if not go_button_cords:
                raise LauncherException("Go btn position not found")

            return GameHelper.get_relative_coordinates(
                area_cords_relative, go_button_cords)

        def input_x_y_position(input_position: list, new_pos: tuple):
            for i in range(2):
                click_on_target(input_position[i], None, self.mouse, True)

                # add the input
                # first clear the current content
                for _ in range(5):
                    self.keyboard.clear()
                    time.sleep(0.1)

                pos = new_pos[i]
                # now enter the new content
                self.keyboard.write(str(pos))

                # save content written
                click_on_target(input_position[i], None, self.mouse, True)

                time.sleep(0.1)

        x_min, x_max = (0, 1199)
        y_min, y_max = (0, 1199)

        # variables of locations
        input_positions = [None, None]
        go_btn_cords = None

        custom_config = r'--oem 3 --psm 6'

        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                # first click on the location finder finder
                click_location_finder()
                time.sleep(1)
                # now input the x and y positions
                if not input_positions[0]:
                    input_positions = find_x_y_input()
                # write the contents
                input_x_y_position(input_positions, (x, y))
                time.sleep(1)
                # go the target
                if not go_btn_cords:
                    go_btn_cords = find_go_btn()
                # click on go btn
                click_on_target(go_btn_cords, None, self.mouse, True)
                time.sleep(2)
                # now search if target city is in view
                center_area_image, area_cords_relative = \
                    self.get_screen_section(60, TOP_IMAGE)
                center_area_image, area_cords_relative = \
                    self.get_screen_section(45, BOTTOM_IMAGE,
                                            center_area_image,
                                            area_cords_relative)

                gray = cv.cvtColor(center_area_image, cv.COLOR_BGR2GRAY)

                target_city = self.find_ocr_target(name, gray,
                                                   custom_config, partial=False)
                if target_city:
                    print(f"Found {name} at location - {x},{y}")

    def find_city(self):
        """Finds a cc32 city"""

        # Now set the cursor to the center of the game screen
        center = GameHelper.get_center(self.app_coordinates)
        # Move the mouse to the center
        self.mouse.set_position(self.app_coordinates.start_x,
                                self.app_coordinates.start_y)
        self.mouse.move(center[0], center[1])
        center_position = self.mouse.position

        count = 1
        x_range = 305
        y_range = 305

        templates_files = self.target_templates('lee')

        def move_left():
            for i in range(count):
                self.mouse.drag(-250, 178)
                self.mouse.set_position(center_position.x,
                                        center_position.y)

        def move_right():
            for i in range(count):
                self.mouse.drag(250, -178)
                self.mouse.set_position(center_position.x,
                                        center_position.y)

        def move_up():
            # now scroll up
            self.mouse.drag(300, 150)
            self.mouse.set_position(center_position.x,
                                    center_position.y)

        def find_lee():
            area_image, area_cords_relative = \
                self.get_screen_section(75, BOTTOM_IMAGE)

            lee_cords = self.find_target(
                area_image,
                templates_files,
                threshold=0.27
            )

            if lee_cords:
                print("############### found lee ###########")
                time_str = datetime.now(). \
                    strftime("%d-%m-%yT%H-%M-%S")
                file_name = f'lee/lee_{time_str}.png'
                cv.imwrite(file_name, area_image)

        for y_count in range(y_range):
            for _ in range(x_range):
                # move left
                find_lee()
                move_left()
                time.sleep(0.1)
            # move up
            move_up()
            for _ in range(x_range):
                find_lee()
                # move right
                move_right()
                time.sleep(0.1)

            # move up
            move_up()
            time.sleep(0.1)
