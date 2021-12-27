"""Responsible for killing zombies in the Game event"""
import cv2
import numpy as np

from src.game_launcher import GameLauncher, display_image
from src.ocr import get_text_from_image


class Zombies:
    """
    Zombies killing class.

    In order to be able to kill zombies in the game,
    some of this things need to be sorted out:
     - Get current mobility --- done
     - Ability to switch to outside city screen
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

    def get_latest_fuel(self):
        """Get the current fuel value"""
        # take a screen shoot of screen
        # cut out the top 10% of the screen
        # search the roi for the fuel template.
        game_screen = self.launcher.get_game_screen()
        fuel_screen = self.get_fuel_screen(game_screen)
        display_image(fuel_screen)

        # search fuel target to extract fuel area
        fuel_cords = self.launcher.find_target(
            fuel_screen, self.launcher.target_templates('mobility'))
        new_x = fuel_cords.end_x + 5
        end_x = fuel_screen.shape[1] - 5
        fuel_image = fuel_screen[
                     fuel_cords.start_y + 5:fuel_cords.end_y - 5,
                     new_x:end_x,
                     ]
        # extract the fuel value
        cv2.imwrite('fuel2.png', fuel_image)
        display_image(fuel_image)
        fuel_value = get_text_from_image(fuel_image)
        self.launcher.log_message(f"Current fuel - {fuel_value}")
        if fuel_value:
            return fuel_value
        raise Exception("Fuel value not readable")

    def zombie_city(self):
        """
        Activates the zombie city mode
        :return:
        """





