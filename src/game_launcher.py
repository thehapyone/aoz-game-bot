import subprocess
import time
from typing import Optional, List
import imutils
import numpy as np
from mss import mss
from pathlib import Path
import cv2 as cv

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
    game_path = 'C:\Program Files\BlueStacks_nxt\HD-Player.exe'
    cwd = Path(__file__).cwd()
    _templates_path = {
        "app": str(cwd.joinpath("data", "app")),
        "game": str(cwd.joinpath("data", "game", "app_icon")),
        "rewards": str(cwd.joinpath("data", "game", "rewards")),
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

    def start_game(self):
        """
        Starts and prep the AoZ game app
        :return:
        """
        self.log_message("Launching Bluestack App now")
        launcher.launch_app()
        self.log_message("Finding the app screen")
        try:
            launcher.find_app()
        except Exception as error:
            if "Bluestack screen not detected" in str(error):
                # attempts again
                launcher.find_app()
            else:
                raise error
        self.log_message("Finding the game app")
        launcher.find_game()
        self.log_message("Launching the game now")
        launcher.launch_aoz()

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
        game_screen = self._get_game_screen()
        self.log_message("Finding the available rewards button.")
        rewards_location = self._find_target(
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

    @property
    def screen_image_path(self) -> str:
        """Returns te path for the screenshot"""
        return str(self.cwd.joinpath("data", "screenshot.png"))

    def take_screenshot(self) -> None:
        """Takes a screenshot of the current monitor screen"""
        image_file = self.screen_image_path
        self._mss.shot(mon=1, output=image_file)
        self._mss.close()

    def _get_game_screen(self) -> np.ndarray:
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

    def find_game(self):
        """
        Helper function for finding the coordinates of the AoZ game app
        :return:
        """
        screen_image = cv.imread(self.screen_image_path, self.IMG_COLOR)
        start_x, start_y, end_x, end_y = self._app_coordinates
        reference_image = screen_image[start_y:end_y, start_x:end_x]
        location = self._find_target(reference_image,
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
        location = self._find_target(screen_image,
                                     self.target_templates('app'))
        if not location:
            raise Exception("Bluestack screen not detected. Bot can't proceed")
        self._app_coordinates = location

    def _find_target(self, reference: np.ndarray, target: List[np.ndarray]) \
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
        else:
            raise Exception(f"Target {target} is not recognized")
        return self._load_all_templates(directory)

    def log_message(self, message: str):
        """Prints to log if enabled"""
        if self._debug:
            print(message)


if __name__ == '__main__':
    mouse = MouseController()
    keyboard = KeyboardController()
    # Run game launcher
    launcher = GameLauncher(mouse, keyboard)
    launcher.start_game()
