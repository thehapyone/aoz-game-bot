"""The mouse listener code. Outputs the mouse screen interaction"""
import time
import pyautogui
from multipledispatch import dispatch


class KeyboardController:
    """
    The Keyboard controller class
    """

    @staticmethod
    def shake():
        """
        Initiate a shake on the bluestack app
        Shake key combination is = Ctrl + 3.
        Note: The cursor should be on the app before this else, shake will
        not occur
        """
        pyautogui.hotkey('ctrl', '3')

    @staticmethod
    def back():
        """
        Press the esc key to go back
        """
        pyautogui.press('esc')


class MouseController:
    """
    Mouse controller class
    """

    def __init__(self):
        self._mouse = pyautogui

    def set_position(self, x, y):
        """Set the current mouse position"""
        self._mouse.moveTo(x, y)

    def reset_position(self):
        """Reset the mouse position to 0, 0"""
        self._mouse.moveTo(0, 0)

    @property
    def position(self):
        """Get the current mouse position"""
        return self._mouse.position()

    @dispatch(tuple)
    def move(self, center: tuple):
        """Move mouse to a relative position"""
        self._mouse.move(*center)
        time.sleep(0.5)

    @dispatch(int, int)
    def move(self, dx: int, dy: int):
        """Move mouse to a relative position"""
        self._mouse.move(dx, dy)
        time.sleep(0.5)

    def click(self,
              clicks: int = 1):
        """Perform a mouse click on the current mouse position"""
        self._mouse.click(clicks=clicks)

    def drag(self, x: int, y: int, button: str = 'left'):
        """
        Drags the mouse to a given position.
        """
        self._mouse.drag(x, y, button=button, duration=0.5)


'''
if __name__ == '__main__':
    mouse = MouseController()
    time.sleep(5)
    print('setting mouse position')
    print(mouse.position)
    mouse.set_position(3381, 977)
    time.sleep(1)
    #mouse.click(1)
    time.sleep(5)


    print('scrolling up')
    time.sleep(1)
    # mouse.scroll(0, -
    mouse.drag(0, 50)
    time.sleep(1)
    KeyboardController.shake()

    # mouse.scroll(0, 50)

    print(mouse.position)
    print("finished")
'''