import numpy as np
import pytesseract as ocr

ocr.pytesseract.tesseract_cmd = \
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def get_text_from_image(image: np.ndarray, config: str = None) -> str:
    """
    Perform OCR on a given image and returns the detected
    text

    :param config: A custom config
    :param image: The input image
    :return: Text in image
    """
    return ocr.image_to_string(image, config=config).strip()
