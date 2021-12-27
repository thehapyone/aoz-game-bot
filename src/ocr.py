import numpy as np
import pytesseract as ocr

ocr.pytesseract.tesseract_cmd = \
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def get_text_from_image(image: np.ndarray) -> str:
    """
    Perform OCR on a given image and returns the detected
    text

    :param image:
    :return: Text in image
    """
    print(ocr.image_to_data(image))
    return ocr.image_to_string(image).strip()
