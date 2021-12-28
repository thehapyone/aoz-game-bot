from src.game_launcher import GameLauncher
from src.listener import MouseController, KeyboardController
from src.radar import Radar
from src.zombies import Zombies

if __name__ == '__main__':
    mouse = MouseController()
    keyboard = KeyboardController()
    # Run game launcher
    launcher = GameLauncher(mouse, keyboard)
    launcher.start_game()

    # zombie
    zombie = Zombies(launcher)

    # radar
    radar = Radar(launcher)
    radar.select_radar_menu(5)