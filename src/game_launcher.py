import subprocess
import time
from pathlib import Path
from typing import Optional, List

import cv2 as cv
import imutils
import numpy as np
from mss import mss

from src.constants import BOTTOM_IMAGE, TOP_IMAGE, LEFT_IMAGE
from src.exceptions import LauncherException
from src.helper import Coordinates, GameHelper
from src.listener import MouseController, KeyboardController


def display_image(image, name: str = None):
    # define the screen resolution
    screen_res = 1280, 720
    scale_width = screen_res[0] / image.shape[1]
    scale_height = screen_res[1] / image.shape[0]
    scale = min(scale_width, scale_height)
    # resized window width and height
    window_width = int(image.shape[1] * scale)
    window_height = int(image.shape[0] * scale)
    # cv2.WINDOW_NORMAL makes the output window resizealbe
    win_name = "Display Frame" if not name else name

    cv.namedWindow(win_name, cv.WINDOW_NORMAL)
    # resize the window according to the screen resolution
    cv.resizeWindow(win_name, window_width, window_height)

    cv.imshow(win_name, image)
    cv.waitKey(0)


class GameLauncher:
    """
    The Game Launcher class. This class is responsible for the following:
     - Start the game app if not started already.
     - launch the AoZ app
    """
    instance = None
    game_path = 'C:\Program Files\BlueStacks_nxt\HD-Player.exe'
    cwd = Path(__file__).cwd()
    _templates_path = {
        "app": str(cwd.joinpath("data", "app")),
        "game": str(cwd.joinpath("data", "game", "app_icon")),
        "rewards": str(cwd.joinpath("data", "game", "rewards")),
        "mobility": str(cwd.joinpath("data", "game", "mobility")),
        "city-icon": str(cwd.joinpath("data", "game", "city_icon")),
        "outside-icon": str(cwd.joinpath("data", "game", "outside_icon")),
        "radar": str(cwd.joinpath("data", "game", "radar")),

    }
    IMG_COLOR = cv.IMREAD_COLOR

    def __init__(self, mouse: MouseController,
                 keyboard: KeyboardController,
                 enable_debug=True):
        self._app_templates = None
        self.app_pid = None
        self._mss = mss()
        self._debug = enable_debug
        self._app_coordinates: Optional[Coordinates] = None
        self._game_coordinates: Optional[Coordinates] = None
        self._aoz_launched = None
        self._mouse = mouse
        self._keyboard = keyboard

    @property
    def mouse(self):
        """Returns the mouse object"""
        return self._mouse

    def start_game(self):
        """
        Starts and prep the AoZ game app
        :return:
        """
        self.log_message(
            "############## Launching Bluestack App now ##############")
        self.launch_app()
        self.log_message("############## Finding the app screen ##############")
        try:
            self.find_app()
        except Exception as error:
            if "Bluestack screen not detected" in str(error):
                # attempts again
                self.find_app()
            else:
                raise error
        self.log_message("############# Finding the game app ##############")
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
                raise Exception("Error launching bluestack app")
            # wait for the app to be ready.
            time.sleep(20)

    def get_rewards(self):
        """Get the rewards that shows on the home screen"""
        game_screen = self.get_game_screen()
        self.log_message("Finding the available rewards button.")
        rewards_location = self.find_target(
            game_screen,
            self.target_templates('rewards'))
        if rewards_location:
            reward_box = GameHelper.get_relative_coordinates(
                self._app_coordinates, rewards_location)
            # display_image(reward_image)
            self._mouse.set_position(reward_box.start_x, reward_box.start_y)
            reward_center = GameHelper.get_center(reward_box)
            self._mouse.move(*reward_center)
            self._mouse.click()
            time.sleep(2)
            # click again to remove the notification of the rewards collected
            self._mouse.click()

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
            time.sleep(10)
            # now we click on the reward that popups on the game screen.
            self.get_rewards()
            # self game is alive now.
            self.log_message("Game now active")
            # shake to collect available resources
            self._keyboard.shake()
            time.sleep(5)

    @property
    def screen_image_path(self) -> str:
        """Returns te path for the screenshot"""
        return str(self.cwd.joinpath("data", "screenshot.png"))

    def take_screenshot(self) -> None:
        """Takes a screenshot of the current monitor screen"""
        self._mss.shot(mon=1, output=self.screen_image_path)
        self._mss.close()

    def get_game_screen(self) -> np.ndarray:
        """
        Returns the current game screen. Used when the game screen has
        been updated.
        :return:
        """
        self.take_screenshot()
        screen_image = cv.imread(self.screen_image_path, self.IMG_COLOR)
        start_x, start_y, end_x, end_y = self._app_coordinates
        game_screen = screen_image[start_y:end_y, start_x:end_x]
        return game_screen

    def get_screen_section(self,
                           percentage: int,
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

    def get_bottom_menu(self) -> tuple[np.ndarray, dict[int, np.ndarray],
                                       Coordinates]:
        """
        Gets the game button menu
        :return: An enum of the game menu.
        """
        bottom_menu, bottom_coordinates_relative = \
            self.get_screen_section(10, BOTTOM_IMAGE)
        # extract and categorizes all bottom menu.
        # first menu is about 20% and the others share 16%
        t_h, t_w, _ = bottom_menu.shape
        city_icon_end_width = int(0.20 * t_w)
        city_icon = bottom_menu[0:t_h, 0:city_icon_end_width]

        menu_dict = {0: city_icon}

        icon_width = int(0.16 * t_w)
        end_width = city_icon_end_width
        for count in range(1, 6):
            start_width = end_width
            end_width = start_width + icon_width
            if end_width > t_w:
                end_width = t_w
            menu_icon = bottom_menu[0:t_h, start_width:end_width]
            menu_dict[count] = menu_icon
        return bottom_menu, menu_dict, bottom_coordinates_relative

    def set_view(self, view: int):
        """
        Set the game view from with inside city or outside the city
        :param view: Either activate the inside city or outside city view.
        Possible values are - 1 for inside city and 2 for outside city.
        :return: None
        """
        bottom_image, _, coordinates = self.get_bottom_menu()
        coords = self.find_target(
            bottom_image, self.target_templates('city-icon'))
        if view == 1:
            # go to inside city view
            if coords:
                self.log_message("Now in city view mode")
                return
            coords = self.find_target(
                bottom_image, self.target_templates('outside-icon'))
            if not coords:
                raise LauncherException(
                    "View changing could not be completed.")
            center = GameHelper.get_center(coords)
            self._mouse.set_position(coordinates.start_x,
                                     coordinates.start_y)
            self._mouse.move(*center)
            time.sleep(2)
            self._mouse.click()
            time.sleep(5)
            self.log_message("Now in city view mode")
            return
        if view == 2:
            # go to outside city view
            if not coords:
                self.log_message("Now in outside city view mode")
                return
            coords = self.find_target(
                bottom_image, self.target_templates('city-icon'))
            if not coords:
                raise LauncherException(
                    "View changing could not be completed.")
            center = GameHelper.get_center(coords)
            self._mouse.set_position(coordinates.start_x,
                                     coordinates.start_y)
            self._mouse.move(*center)
            time.sleep(2)
            self._mouse.click()
            time.sleep(5)
            self.log_message("Now in outside city view mode")
            return
        raise LauncherException(f"View mode {view} not supported")

    def find_game(self):
        """
        Helper function for finding the coordinates of the AoZ game app
        :return:
        """
        screen_image = cv.imread(self.screen_image_path, self.IMG_COLOR)
        start_x, start_y, end_x, end_y = self._app_coordinates
        reference_image = screen_image[start_y:end_y, start_x:end_x]
        location = self.find_target(reference_image,
                                    self.target_templates('game'))
        if not location:
            raise Exception("Game app not detected. Bot can't proceed")
        # extract the coordinates in reference to the main screen
        self._game_coordinates = GameHelper.get_relative_coordinates(
            self._app_coordinates, location)
        time.sleep(1)

    def find_app(self):
        """
        Helper function for finding the coordinates of the bluestack android
        emulator app. It returns the bound box location of the screen
        :return:
        """
        # take the screenshot first
        self.take_screenshot()
        # load the screenshot to memory
        screen_image = cv.imread(self.screen_image_path,
                                 self.IMG_COLOR)
        location = self.find_target(screen_image,
                                    self.target_templates('app'))
        if not location:
            raise LauncherException(
                "Bluestack screen not detected. Bot can't proceed")
        self._app_coordinates = location

    def find_target(self, reference: np.ndarray, target: List[np.ndarray]) \
            -> Optional[Coordinates]:
        """
        Helper function for finding the coordinates of the
        of a given target in a reference image.
        It returns the bounding box location of the game app.
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

        if min_val < 0.55 and cosine_score > 0.50:
            if self._debug:
                self.log_message("Target image found successfully")
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
        if target.lower() == "game":
            directory = self._templates_path["game"]
        elif target.lower() == "rewards":
            directory = self._templates_path["rewards"]
        elif target.lower() == "app":
            directory = self._templates_path["app"]
        elif target.lower() == "mobility":
            directory = self._templates_path["mobility"]
        elif target.lower() == "city-icon":
            directory = self._templates_path["city-icon"]
        elif target.lower() == "outside-icon":
            directory = self._templates_path["outside-icon"]
        elif target.lower() == "radar":
            directory = self._templates_path["radar"]
        else:
            raise Exception(f"Target {target} is not recognized")
        return self._load_all_templates(directory)

    def log_message(self, message: str):
        """Prints to log if enabled"""
        if self._debug:
            print(message)
