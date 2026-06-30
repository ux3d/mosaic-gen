import argparse
import re
from pathlib import Path

import file_utils
import image_utils
from PIL import Image
import numpy as np
import os

from util import find_closest_factors, sort_input_files


def _find_common_output_stem(files):
    stems = [Path(f).stem for f in files]
    if len(stems) == 1:
        return stems[0]

    # Remove trailing view/index numbers and separators (e.g. image.001, image_12, image-3)
    cleaned = [re.sub(r"[._-]?\d+$", "", s) for s in stems]
    common = os.path.commonprefix(cleaned).rstrip("._-")
    if common:
        return common

    return cleaned[0] if cleaned[0] else stems[0]


def images_to_mosaic(input_dir, output_dir):
    print(input_dir)
    print(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    file_list = [f for f in file_utils.get_files(input_dir) if f.suffix.lower() == ".png"]
    file_list = [Path(p) for p in sort_input_files([str(p) for p in file_list])]
    if not file_list:
        raise ValueError("No .png files found in input directory")

    rows, cols = find_closest_factors(len(file_list))
    print(f"Building mosaic from {len(file_list)} views as {cols}x{rows} (cols x rows)")

    img_array = []
    for f in file_list:
        print("read: " + str(f))
        with Image.open(f) as image:
            image_data = np.asarray(image.convert("RGB"))
        img_array.append(image_data)

    img_grid = image_utils.create_image_grid(img_array, rows, cols)

    output_name = _find_common_output_stem(file_list)
    output_file = f"{output_name}.mosaic.{cols}x{rows}.png"
    path = os.path.join(output_dir, output_file)
    Image.fromarray(img_grid).save(path)
    print("write: " + str(path))


if __name__ == "__main__":

    parser = argparse.ArgumentParser("Multiview")

    parser.add_argument( "-i", "--input", help="Directory of image files to combine to mosaic images", required=True)
    parser.add_argument("-o", "--output", help="Directory for output mosaic image files ", required=True)


    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output

    images_to_mosaic(input_dir, output_dir)

   

        

