import cv2
import imutils
import numpy as np
import pytesseract as ocr
from imutils import contours

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
    print(ocr.image_to_data(image))
    return ocr.image_to_string(image, config=config).strip()
