"""Holds all the helper or support methods"""
import subprocess
from functools import partial, wraps
from typing import NamedTuple, Tuple, Optional, Callable, Type

import numpy as np
from numpy import dot
from numpy.linalg import norm
from skimage.feature import hog


def retry(
        _func: Callable = None, *,
        exception: Type[BaseException] = Exception,
        message: str = None,
        attempts: int = 1):
    """
    A retry decorator for retying a function that raised
    a particular exception,

    :return:
    """

    if _func is None:
        return partial(retry,
                       exception=exception,
                       message=message,
                       attempts=attempts)

    @wraps(_func)
    def wrapper(*args, **kwargs):
        """
        A wrapper function.

        :param args:
        :param kwargs:
        :return:
        """
        error_exception = None
        for attempt in range(attempts):
            try:
                response = _func(*args, **kwargs)
                return response
            except exception as error:
                error_exception = error
                if message in str(error):
                    print(f"------ Error in {_func.__name__}: Attempting "
                          f"again with attempts {attempt+1}/{attempts}. Error "
                          f"is {str(error)} -------")
                    continue
                raise error
        raise error_exception
    return wrapper


class Coordinates(NamedTuple):
    """
    A Tuple class for the coordinates bounding box.

    :param int start_x: The Top Left x coordinate
    :param int start_y: The Top Left y coordinate
    :param int end_x: The Bottom right x coordinate
    :param int end_y: The Bottom right y coordinate
    """
    start_x: int
    start_y: int
    end_x: int
    end_y: int


class GameHelper:
    """
    The Helper class
    """

    @staticmethod
    def get_center(position: Coordinates) -> Tuple[int, int]:
        """Returns the center points of a bounding box"""
        return (int((position.end_x - position.start_x) / 2.0),
                int((position.end_y - position.start_y) / 2.0))

    @staticmethod
    def is_app_running() -> Optional[int]:
        """
        Checks if the bluestack app is already running.

        :return int: Returns the Bluestack running process id.
        """
        process_cmds = ["wmic", "process", "get",
                        "description,", "processid"]

        running_process = subprocess.run(process_cmds,
                                         capture_output=True,
                                         encoding="utf-8")
        running_process = running_process.stdout.strip().splitlines()
        processes = [process.strip().lower()
                     for process in running_process[1:]
                     if process]
        process_names = [process.split("  ")[0].lower().strip()
                         for process in processes]
        process_ids = [process.split("  ")[-1].lower().strip()
                       for process in processes]
        target_name = "hd-player.exe"
        if target_name in process_names:
            app_index = process_names.index(target_name)
            app_pid = int(process_ids[app_index])
            return app_pid
        return None

    @staticmethod
    def calculate_hog(image: np.ndarray, rgb_channel: False) -> [np.ndarray,
                                                                 np.ndarray]:
        """Calculates the HOG representation of an image"""
        return hog(image, orientations=8,
                   pixels_per_cell=(16, 16),
                   cells_per_block=(1, 1), visualize=True,
                   multichannel=rgb_channel)

    @staticmethod
    def cosine_similarity(vector_a, vector_b):
        """Calculates the cosine similarity between two vectors"""
        return dot(vector_a, vector_b) / \
               (norm(vector_a) * norm(vector_b))

    @staticmethod
    def get_relative_coordinates(
            reference_location: Tuple[int, int, int, int],
            current_location: Tuple[int, int, int, int]) -> \
            Coordinates:
        """
        Returns the coordinates of the current location
        in relative to the given reference location.

        :returns: The relative startX, startY, endX, endY
        """
        return Coordinates(
            reference_location[0] + current_location[0],
            reference_location[1] + current_location[1],
            reference_location[2] - ((reference_location[2] -
                                      reference_location[0])
                                     - current_location[2]),
            reference_location[3] - ((reference_location[3] -
                                      reference_location[1])
                                     - current_location[3]))
