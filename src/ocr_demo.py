from pathlib import Path

import cv2
import cv2 as cv
import numpy as np
import pytesseract as ocr

ocr.pytesseract.tesseract_cmd = \
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'

cwd = Path(__file__).cwd()

main_image = str(cwd.joinpath("zombie5.png"))

img_original = cv.imread(main_image, cv.IMREAD_COLOR)

#opening - erosion followed by dilation
def opening(image):
    kernel = np.ones((2,2),np.uint8)
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

def display_image(image, name: str = None):
    # define the screen resolution
    screen_res = 1280, 720
    scale_width = screen_res[0] / image.shape[1]
    scale_height = screen_res[1] / image.shape[0]
    scale = min(scale_width, scale_height)
    # resized window width and height
    window_width = int(image.shape[1] * scale)
    window_height = int(image.shape[0] * scale)
    # cv2.WINDOW_NORMAL makes the output window resizealbe
    win_name = "Display Frame" if not name else name

    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    # resize the window according to the screen resolution
    cv2.resizeWindow(win_name, window_width, window_height)

    cv.imshow(win_name, image)
    cv.waitKey(0)


green_min = (0,105,10)
green_max = (16,255,75)

white_min = (200,200,200)
white_max = (255,255,255)

black_min = (2,2,2)
black_max = (65,65,65)

method = cv.TM_SQDIFF_NORMED
rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))

try:
    img = img_original.copy()
    green_channel = img.copy()[:,:,1]
    blue_channel = img.copy()[:,:,0]
    red_channel = img.copy()[:,:,2]

    black_channel = cv2.inRange(img, black_min, black_max)
    white_channel = cv2.inRange(img, white_min, white_max)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    display_image(img)
    display_image(gray)

    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, rectKernel)


    display_image(tophat)
    display_image(black_channel)
    display_image(white_channel)


    print(ocr.image_to_string(img))

    custom_config = r'-c tessedit_char_blacklist=-/\| --oem 3 --psm 6 ' \
                    r'outputbase digits'

    custom_config2 = r'-c tessedit_char_whitelist=0123456789 --oem 3 --psm 6 '

    custom_config3 = r'-c tessedit_char_blacklist=-/\| --oem 3 --psm 6'

    print('--------------- white channel --------------------')
    print(ocr.image_to_string(white_channel,  config=custom_config))
    print(ocr.image_to_string(white_channel))

    print('--------------- black channel --------------------')
    print(ocr.image_to_string(black_channel, config=custom_config2))
    result = ocr.image_to_string(black_channel, config=custom_config3)
    digits = []
    for char in result.strip():
        if char.isdigit():
            digits.append(char)
    level = int("".join(digits))
    print("sss - ", level)
    print(ocr.image_to_string(black_channel))

    print('--------------- black channel --------------------')
    print(ocr.image_to_data(black_channel, config=custom_config2))
    print(ocr.image_to_data(black_channel, config=custom_config3))
    print(ocr.image_to_data(black_channel))

    print('--------------- white channel --------------------')
    print(ocr.image_to_data(white_channel, config=custom_config2))
    print(ocr.image_to_data(white_channel))


except KeyboardInterrupt:
    print("stop")

cv.destroyAllWindows()
