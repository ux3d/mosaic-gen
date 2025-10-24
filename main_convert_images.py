import argparse

import file_utils
import image_utils
from PIL import Image
import numpy as np
import os


def images_to_mosaic(input_dir, output_dir, grid_x, grid_y):
    output_name ="output"
    print(input_dir)
    print(output_dir)

    file_list = file_utils.get_files(input_dir)
    frame_index=0
    img_array = []
    for f in file_list:

        print("read: "+str(f))
        image = Image.open(f)
        image_data = np.asarray(image)
        img_array.append(image_data)

        if len(img_array) == grid_x*grid_y:
            img_grid = image_utils.create_image_grid(img_array, grid_x, grid_y)
            output_file = output_name+'_'+str(frame_index).zfill(5)+'.png' 
            path = os.path.join(output_dir, output_file)
            img_grid = Image.fromarray(img_grid)
            img_grid = img_grid.resize((3840, 2160), resample=Image.NEAREST)
            img_grid.save(path)
            print("write: "+str(path))
            img_array.clear()
            frame_index=frame_index+1


if __name__ == "__main__":

    parser = argparse.ArgumentParser("Multiview")

    parser.add_argument( "-i", "--input", help="Directory of image files to combine to mosaic images", required=True)
    parser.add_argument("-o", "--output", help="Directory for output mosaic image files ", required=True)


    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output

    grid_x = 4
    grid_y = 4

    images_to_mosaic(input_dir, output_dir, grid_x, grid_y)

   

        

