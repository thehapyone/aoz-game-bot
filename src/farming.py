"""Responsible for different farming activities"""
import time

from src.constants import INSIDE_VIEW, OUTSIDE_VIEW, BOTTOM_IMAGE
from src.exceptions import FarmingException
from src.game_launcher import GameLauncher
from src.helper import GameHelper, Coordinates


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

    def __init__(self, farm_type: int, launcher: GameLauncher):
        self._farm_type = farm_type
        self.launcher = launcher

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
        self.launcher.mouse.move(center)
        count = 3
        # Drag the mouse left three times
        for i in range(count):
            self.launcher.mouse.drag(100, 0)
            time.sleep(0.3)
            self.launcher.mouse.set_position(center)
        # Now we should be in the garage view.

        garage_image, garage_area_cords_relative = \
            self.launcher.get_screen_section(40, BOTTOM_IMAGE)
        cords = self.launcher.find_target(
            garage_image,
            self.launcher.target_templates('garage'),
            threshold=0.1
        )
        if not cords:
            raise FarmingException("Unable to find the Garage")
        cords_relative = GameHelper.get_relative_coordinates(
            garage_area_cords_relative, cords)
        return cords_relative

    def get_max_fleet(self):
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
        # now find the fleet army button
        garage_image, garage_area_cords_relative = \
            self.launcher.get_screen_section(40, BOTTOM_IMAGE)
        cords = self.launcher.find_target(
            garage_image,
            self.launcher.target_templates('garage-fleet'),
            threshold=0.1
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

        # now we should have the fleet screen.

