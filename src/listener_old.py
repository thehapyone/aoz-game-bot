"""The mouse listener code. Outputs the mouse screen interaction"""
import time

import pynput
from multipledispatch import dispatch
from pynput.keyboard import Key
from pynput.mouse import Listener, Button, Controller


class KeyboardController:
    """
    The Keyboard controller class
    """
    def __init__(self):
        self._keyboard = pynput.keyboard.Controller()

    def shake(self):
        """
        Initiate a shake on the bluestack app
        Shake key combination is = Ctrl + 3.
        Note: The cursor should be on the app before this else, shake will
        not occur
        """
        with self._keyboard.pressed(Key.ctrl):
            self._keyboard.tap('3')


class MouseController:
    """
    Mouse controller class
    """

    def __init__(self):
        self._mouse = Controller()

    def set_position(self, x, y):
        """Set the current mouse position"""
        self._mouse.position = (x, y)

    def reset_position(self):
        """Reset the mouse position to 0, 0"""
        self._mouse.position = (0, 0)

    @property
    def position(self):
        """Get the current mouse position"""
        return self._mouse.position

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
              button: Button = Button.left,
              clicks: int = 1):
        """Perform a mouse click on the current mouse position"""
        self._mouse.click(button, clicks)


class MouseListener:
    """
    Mouse listener class
    """

    instance = None

    def __init__(self, on_move=False, on_click=True, on_scroll=False):
        self._listener = Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.global_stop = False
        self._enable_on_move = on_move
        self._enable_on_click = on_click
        self._enable_on_scroll = on_scroll

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()

    @property
    def listener(self):
        return self._listener

    def start(self):
        self._listener.start()
        self._listener.wait()

    def finish(self):
        self._listener.join()
        self._listener.stop()

    def on_move(self, x, y):
        if self.global_stop:
            return False
        if self._enable_on_move:
            print('Pointer moved to {0}'.format(
                (x, y)))

    def on_click(self, x, y, button, pressed):
        if self.global_stop:
            return False
        if self._enable_on_click:
            print('{0} at {1}'.format(
                'Pressed' if pressed else 'Released',
                (x, y)))

    def on_scroll(self, x, y, dx, dy):
        if self.global_stop:
            return False
        if self._enable_on_scroll:
            print('Scrolled {0} at {1}'.format(
                'down' if dy < 0 else 'up',
                (x, y)))

    def run(self):
        while True:
            try:
                time.sleep(0.01)
            except KeyboardInterrupt:
                print("keyboard interrupt - Now shutting down")
                break
        self.global_stop = True


if __name__ == '__main__':
    mouse = Controller()
    handler = MouseListener(on_click=True, on_move=False,
                            on_scroll=True)
    time.sleep(5)
    print('setting mouse position')

    mouse.position = (1343, 370)
    time.sleep(1)
    mouse.click(Button.left, 1)
    time.sleep(5)

    print('scrolling now')
    time.sleep(1)
    mouse.scroll(0, -5)
    time.sleep(1)

    #mouse.scroll(0, 50)

    print(mouse.position)
    print("finished")
    '''
    (1343, 470)
    '''
