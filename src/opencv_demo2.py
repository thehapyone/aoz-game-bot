from pathlib import Path

import cv2
import cv2 as cv

cwd = Path(__file__).cwd()
template_file = str(cwd.joinpath("data", 'game'))

main_image = str(cwd.joinpath("fuel.png"))

img_original = cv.imread(main_image, cv.IMREAD_COLOR)

def load_all_templates(path: str):
    """Loads all the template files found in path folder"""
    template_path = Path(path)
    if not template_path.is_dir():
        raise Exception("Only directory are allowed")
    template_images = []
    for image_path in template_path.glob('template_*.png'):
        template_images.append(cv.imread(str(image_path), 0))

    if not template_images:
        raise Exception("No template image found.")
    return template_images


# All the 6 methods for comparison in a list
methods = ['cv.TM_SQDIFF', 'cv.TM_CCOEFF_NORMED',
           'cv.TM_SQDIFF_NORMED']


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


method = cv.TM_SQDIFF_NORMED
try:
    img = img_original.copy()
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    display_image(gray)
except KeyboardInterrupt:
    print("stop")

cv.destroyAllWindows()
