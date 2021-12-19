import time

import cv2
import cv2 as cv
import imutils as imutils
import numpy
from numpy import dot
from numpy.linalg import norm
from skimage.feature import hog
from skimage.metrics import structural_similarity as ssim
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path

cwd = Path(__file__).cwd()
template_file = str(cwd.joinpath("data", 'game'))

main_image = str(cwd.joinpath("data", 'app', "template_2.png"))

img_original = cv.imread(main_image, 0)
img2 = img_original.copy()


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


all_templates = load_all_templates(template_file)

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


def pad_images_to_same_size(images):
    """
    :param images: sequence of images
    :return: list of images padded so that all images have same width and height (max width and height are used)
    """
    width_max = 0
    height_max = 0
    for img in images:
        h, w = img.shape[:2]
        width_max = max(width_max, w)
        height_max = max(height_max, h)

    images_padded = []
    for img in images:
        h, w = img.shape[:2]
        diff_vert = height_max - h
        pad_top = diff_vert // 2
        pad_bottom = diff_vert - pad_top
        diff_hori = width_max - w
        pad_left = diff_hori // 2
        pad_right = diff_hori - pad_left
        img_padded = cv2.copyMakeBorder(img, pad_top, pad_bottom, pad_left,
                                        pad_right, cv2.BORDER_CONSTANT, value=0)
        assert img_padded.shape[:2] == (height_max, width_max)
        images_padded.append(img_padded)

    return images_padded


method = cv.TM_SQDIFF_NORMED
try:
    img = img2.copy()
    found = None
    time_now = time.time()
    # loop over for the best template match from a series of templates
    for template in all_templates:
        # loop over scales of image
        for scale in np.linspace(0.05, 1.0, 20)[::-1]:
            # resize the image according to the scale, and keep track
            # of the ratio of the resizing
            resized = imutils.resize(img, width=int(img.shape[1] * scale))
            r = img.shape[1] / float(resized.shape[1])
            # if the resized image is smaller than the template, then break
            # from the loop
            tW, tH = template.shape[::-1]
            if resized.shape[0] < tH or resized.shape[1] < tW:
                break
            # Apply template Matching
            res = cv.matchTemplate(resized, template, method)
            min_val, _, min_loc, _ = cv.minMaxLoc(res)

            # if we have found a new min correlation value, then update
            # the bookkeeping variable
            if found is None or min_val < found[1]:
                found = (template, min_val, min_loc, r)

    (template, min_val, min_loc, r) = found
    print("min val -", min_val)
    # unpack the bookkeeping variable and compute the (x, y) coordinates
    # of the bounding box based on the resized ratio
    tW, tH = template.shape[::-1]
    (startX, startY) = (int(min_loc[0] * r), int(min_loc[1] * r))
    (endX, endY) = (int((min_loc[0] + tW) * r), int((min_loc[1] + tH) * r))
    found_template = img[startY:endY, startX:endX]
    resize_found_template = cv.resize(found_template, (template.shape[1],
                                                       template.shape[0]))

    feature_vec_t, hog_image_t = hog(template,
                                     orientations=8, pixels_per_cell=(16, 16),
                                     cells_per_block=(1, 1), visualize=True,
                                     multichannel=False)
    feature_vec_th, hog_image_th = hog(resize_found_template,
                                       orientations=8, pixels_per_cell=(16, 16),
                                       cells_per_block=(1, 1), visualize=True,
                                       multichannel=False)

    # calculate Cosine Similarity python
    cosine_score = dot(feature_vec_t, feature_vec_th) / \
                   (norm(feature_vec_t) * norm(feature_vec_th))
    print(cosine_score)

    if min_val < 0.65 and cosine_score > 0.55:
        print("Found successfully")

        
        top_left = min_loc
        bottom_right = (min_loc[0] + tW, min_loc[1] + tH)
    
        new_img = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
        cv.rectangle(new_img,top_left, bottom_right, (255,255,0), 4)
        plt.figure()
        plt.imshow(found_template, cmap='gray')
        plt.title('Detected Region'), plt.xticks([]), plt.yticks([])
        plt.show()
    else:
        print("Not found")


except KeyboardInterrupt:
    print("stop")

cv.destroyAllWindows()
