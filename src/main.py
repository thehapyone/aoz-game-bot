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
    zombie.initialize_zombie()
    zombie.set_zombie_level(7)

    radar = Radar()
    button = radar.go_button
    launcher.mouse.set_position(button.start_x, button.start_y)
