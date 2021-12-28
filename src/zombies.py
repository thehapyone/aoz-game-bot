"""Responsible for killing zombies in the Game event"""
import cv2
import numpy as np

from src.constants import OUTSIDE_VIEW
from src.exceptions import ZombieException
from src.game_launcher import GameLauncher, display_image
from src.ocr import get_text_from_image


class Zombies:
    """
    Zombies killing class.

    In order to be able to kill zombies in the game,
    some of this things need to be sorted out:
     - Get current mobility --- done
     - Ability to switch to outside city screen --- done
     - find and click on the green radar button
     - find and click on the find zombie radar
     - get the current level of zombie for the user
     - increase and decrease the zombie level.
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

    @property
    def fuel(self):
        """Returns the current fuel"""
        self._fuel = self._get_latest_fuel()
        return self._fuel

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
        display_image(fuel_image)
        processed_image = self.process_fuel_image(fuel_image)

        display_image(processed_image)
        custom_config = r'-c tessedit_char_blacklist=-/\| --oem 3 --psm 6 ' \
                    r'outputbase digits'

        # extract the fuel value
        fuel_value = get_text_from_image(processed_image, custom_config)
        self.launcher.log_message(f"Current fuel - {fuel_value}")
        if fuel_value:
            return fuel_value
        raise ZombieException("Fuel value not readable")

    def zombie_city(self):
        """
        Activates the zombie city mode. Sets the game view
        to outside view
        :return:
        """
        self.launcher.set_view(OUTSIDE_VIEW)






