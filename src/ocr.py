from typing import List, Optional, Union

import cv2
import imutils
import numpy as np
import pytesseract as ocr
from imutils import contours

from src.helper import Coordinates

ocr.pytesseract.tesseract_cmd = \
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def ocr_from_contour(image: np.ndarray,
                     config: str = r'--oem 3 --psm 10'):
    """
    Perform OCR on a given image by extracting all the
    contours out first and then applying the ocr to each single
    contour and joining the final result together.

    :param config: A custom config
    :param image: The input image
    :return: Detected text in image
    """
    cnts = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = contours.sort_contours(cnts,
                                  method="left-to-right")[0]
    result = []
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        roi = image[y:y + h, x:x + w]
        roi = cv2.resize(roi, (57, 88))
        output = ocr.image_to_string(roi, config=config)
        if output:
            result.append(output.strip())
    return "".join(result)


def get_text_from_image(image: np.ndarray, config: str = '') -> str:
    """
    Perform OCR on a given image and returns the detected
    text

    :param config: A custom config
    :param image: The input image
    :return: Text in image
    """
    return ocr.image_to_string(image, config=config).strip()


def get_box_from_image(
        match: Union[str, List[str]], image: np.ndarray,
        config: str = '', partial: bool = False) -> Optional[Coordinates]:
    """
    Perform OCR on a given image and returns the detected
    text bounding box

    :param match: The target string to match
    :param config: A custom config
    :param partial: Return true if text in substring found as well.
    :param image: The input image
    :return: Text in image
    """
    result = ocr.image_to_data(image,
                               output_type=ocr.Output.DICT,
                               config=config)
    # print(ocr.image_to_string(image, config=config).strip())
    matched_texts: List[str] = result.get("text")
    if not matched_texts:
        return None
    for index, text in enumerate(matched_texts):
        if not text:
            continue
        if isinstance(match, list):
            if text.lower().strip() in match \
                    and float(result['conf'][index]) >= 0:
                break
        else:
            if text.lower().strip() == match.lower().strip() \
                    and float(result['conf'][index]) >= 0:
                break

            if partial:
                if match.lower().strip() in text.lower().strip() \
                        and float(result['conf'][index]) >= 0:
                    break
    else:
        return None
    # returns the bounding box
    bounding_box = Coordinates(
        start_x=result['left'][index],
        end_x=result['left'][index] + result['width'][index],
        start_y=result['top'][index],
        end_y=result['top'][index] + result['height'][index]
    )

    return bounding_box
