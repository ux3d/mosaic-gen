

import numpy as np


    
def float_to_uint8(image, normalize_min, normalize_max):
    normalized_image = 255 * (image - (normalize_min)) / (normalize_max - (normalize_min))
    normalized_image = np.clip(normalized_image,0,255)
    normalized_image = np.uint8(normalized_image)
    return normalized_image


def create_image_grid(imgs, rows, cols):
    assert len(imgs) == rows*cols
    h, w, channels = imgs[0].shape
    grid = np.zeros((rows * h, cols * w, channels), dtype=np.uint8)
    for i, img in enumerate(imgs):
        x = i % cols
        y = i // cols
        grid[y * h:(y + 1) * h, x * w:(x + 1) * w] = img
    return grid

def split_image(image: np.ndarray, grid_x: int, grid_y: int) -> list:
    h, w = image.shape[:2]
    tile_h, tile_w = h // grid_y, w // grid_x
    
    sub_images = []
    for i in range(grid_y):
        for j in range(grid_x):
            x_start, x_end = j * tile_w, (j + 1) * tile_w
            y_start, y_end = i * tile_h, (i + 1) * tile_h
            sub_images.append(image[y_start:y_end, x_start:x_end])
    
    return sub_images