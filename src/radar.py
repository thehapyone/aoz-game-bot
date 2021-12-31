"""Responsible for managing the radar"""
import time

from src.constants import OUTSIDE_VIEW, BOTTOM_IMAGE, TOP_IMAGE, RIGHT_IMAGE
from src.exceptions import RadarException
from src.game_launcher import GameLauncher
from src.helper import Coordinates, GameHelper


class Radar:
    """
    Radar handling class

    :param GameLauncher launcher: The game launcher instance
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Radar, cls).__new__(cls)
            cls._instance.launcher = args[0]  # type GameLauncher
            cls._instance._activated = False
            cls._instance._go_button = None
        return cls._instance

    @property
    def go_button(self) -> Coordinates:
        """Returns the go button coordinates"""
        if not self._go_button:
            self._go_button = self.get_go_button()
        return self._go_button

    def activate_radar(self):
        """
        Activates the radar in the outside city
        :return:
        """
        self.launcher.set_view(OUTSIDE_VIEW)
        radar_area_image, radar_area_coords_relative = \
            self.launcher.get_screen_section(23, BOTTOM_IMAGE)
        radar_area_image, radar_area_coords_relative = \
            self.launcher.get_screen_section(30, RIGHT_IMAGE,
                                             radar_area_image,
                                             radar_area_coords_relative)
        coords = self.launcher.find_target(
            radar_area_image,
            self.launcher.target_templates('radar'))
        if not coords:
            raise RadarException("Radar icon could not be found.")
        coords_relative = GameHelper. \
            get_relative_coordinates(
            radar_area_coords_relative, coords)

        center = GameHelper.get_center(coords_relative)
        self.launcher.mouse.set_position(coords_relative.start_x,
                                         coords_relative.start_y)
        time.sleep(1)
        self.launcher.mouse.move(*center)
        self.launcher.mouse.click()
        time.sleep(2)
        self._activated = True

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
        if not self._activated:
            self.activate_radar()

        radar_section, radar_area_coords_relative = \
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
                radar_area_coords_relative,
                Coordinates(start_width, 0, end_width, t_h))
            radar_options[count] = cords_relative

        # Now activate the selected menu
        current_coords = radar_options[menu]
        center = GameHelper.get_center(current_coords)
        self.launcher.mouse.set_position(
            current_coords.start_x, current_coords.start_y)
        self.launcher.mouse.move(*center)
        time.sleep(2)
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
