from pathlib import Path

import cv2
import cv2 as cv
import numpy as np
import pytesseract as ocr

from src.zombies import Zombies

ocr.pytesseract.tesseract_cmd = \
    r'C:\Program Files\Tesseract-OCR\tesseract.exe'

cwd = Path(__file__).cwd()

main_image = str(cwd.joinpath("fuel-error2.png"))

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

white_min = (130,130,130)
white_max = (220,220,220)

black_min = (2,2,2)
black_max = (65,65,65)

method = cv.TM_SQDIFF_NORMED
rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 5))
rectKernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 2))
dilatekernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

sqKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
try:
    img = img_original.copy()
    print(img.shape)
    area = img.copy()[10:30, 50:150]
    t_h, t_w, _ = img.shape
    target_area = img[:,
                  int(0.22 * t_w):int(0.75 * t_w)
                  ]
    green_channel = img.copy()[:,:,1]
    blue_channel = img.copy()[:,:,0]
    red_channel = img.copy()[:,:,2]
    image22 = Zombies.process_fuel_image(img)
    custom_config = r'-c tessedit_char_whitelist=0123456789 ' \
                        r'--oem 3 --psm 6 '

    display_image(image22)
    print(ocr.image_to_data(image22, config=custom_config))
    exit(2)

    zeros = np.zeros_like(img)
    zeros[:, int(0.22 * t_w):int(0.75 * t_w)] = target_area

    display_image(img)
    display_image(zeros)

    green_channel = img.copy()[:,:,1]
    blue_channel = img.copy()[:,:,0]
    red_channel = img.copy()[:,:,2]

    black_channel = cv2.inRange(zeros, black_min, black_max)
    white_channel = cv2.inRange(zeros, white_min, white_max)

    gray = cv2.cvtColor(zeros, cv2.COLOR_BGR2GRAY)
    display_image(green_channel)

    display_image(img)
    display_image(gray)

    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, rectKernel)
    display_image(tophat, 'tophat')
    '''
    # compute the Scharr gradient of the tophat image, then scale
    # the rest back into the range [0, 255]
    gradX = cv2.Sobel(tophat, ddepth=cv2.CV_32F, dx=1, dy=0,
                      ksize=-1)
    gradX = np.absolute(gradX)
    (minVal, maxVal) = (np.min(gradX), np.max(gradX))
    gradX = (255 * ((gradX - minVal) / (maxVal - minVal)))
    gradX = gradX.astype("uint8")
    display_image(gradX, 'sobel')

    gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, rectKernel2)
    display_image(gradX, 'gradx')

    thresh = cv2.threshold(gradX, 0, 255,
                           cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # apply a second closing operation to the binary image, again
    # to help close gaps between credit card number regions
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, rectKernel2)

    display_image(thresh, 'thresh2')

    #thresh = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, dilatekernel)
    display_image(thresh, 'dilate')
    '''
    #display_image(black_channel)
    display_image(white_channel)


    print(ocr.image_to_string(img))

    custom_config = r'-c tessedit_char_blacklist=-/\| --oem 3 --psm 6 ' \
                    r'outputbase digits'

    custom_config2 = r'-c tessedit_char_whitelist=:0123456789 --oem 3 --psm 6 '

    custom_config3 = r'-c tessedit_char_blacklist=-/\| --oem 3 --psm 6'

    custom_config4 = r'-c tessedit_char_blacklist=-/\| --oem 3 --psm 7'

    custom_config5 = r'-c tessedit_char_whitelist=0123456789 --oem 3 --psm 10'


    print('--------------- white channel --------------------')
    print(ocr.image_to_string(image22,  config=custom_config))
    print(ocr.image_to_string(image22,  config=custom_config2))

    print('---------------  --------------------')

    print(ocr.image_to_string(image22,  config=custom_config2))
    print(ocr.image_to_string(image22,  config=custom_config3))
    print(ocr.image_to_string(image22,  config=custom_config4))
    print(ocr.image_to_string(image22,  config=custom_config5))
    print(ocr.image_to_string(image22))
    print(ocr.image_to_string(image22))

    custom_config5 = r'-c tessedit_char_whitelist=0123456789 --oem 3 --psm 10'

    print('--------------- black channel --------------------')
    print(ocr.image_to_string(black_channel, config=custom_config2))
    print(ocr.image_to_string(black_channel, config=custom_config3))
    print(ocr.image_to_string(black_channel))

    print('--------------- black channel --------------------')
    print(ocr.image_to_data(black_channel, config=custom_config2))
    print(ocr.image_to_data(black_channel, config=custom_config3))
    print(ocr.image_to_data(black_channel))

    print('--------------- white channel --------------------')
    print(ocr.image_to_data(white_channel, config=custom_config3))
    print(ocr.image_to_data(white_channel))

    print('--------------- top hat channel --------------------')
    print(ocr.image_to_data(tophat))
    print(ocr.image_to_data(tophat, config=custom_config2))


except KeyboardInterrupt:
    print("stop")

cv.destroyAllWindows()
