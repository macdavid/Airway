""" Converts images to booleans, then saves them as numpy array
"""

import os
import sys

import numpy as np
import pydicom

# Process arguments supplied
try:
    output_data_path = sys.argv[1]
    input_data_path = sys.argv[2]
except IndexError:
    print("ERROR: No source or data path provided, aborting!")
    sys.exit(1)

dir_names_to_id = {
    "Bronchus": 1,
    "LeftLowerLobe": 2,
    "LeftUpperLobe": 3,
    "RightLowerLobe": 4,
    "RightMiddleLobe": 5,
    "RightUpperLobe": 6,
    # "Vein": 7,
    # "Artery": 8,
}


def get_image_num(filename):
    return int(filename.replace('IMG', ''))


def save_images_as_npy(raw_data_path, processed_data_path):
    """Saves a 3D numpy matrix of the model to $processed_data_path

    The matrix has 0 for empty space and dir_names_to_id for each
    type given. 
    """

    # Get the patient id from the folder name 
    patient_id = os.path.basename(raw_data_path)

    # s is just a debug value to print out the sum of all the lobes.
    # Useful in case some of the bronchus do overlap with some of
    # the lungs. The sums should be equal, if not something is amiss.
    total_sum = 0

    # Iterate over each type, adding each layer on top of the model
    # with the corresponding id marked in that position.
    for folder, lobe_id in dir_names_to_id.items():
        abs_folder_path = os.path.join(raw_data_path, folder)
        image_files = sorted(os.listdir(abs_folder_path), key=get_image_num)
        curr_sum = 0

        # Initialize model. Note that we do this in this unusual location
        # instead of outside the loop because the count of the images_files
        # is not known before the loop. Therefore this should only be 
        # initialized on the first run of the loop.
        if total_sum == 0:
            model = np.zeros((len(image_files), 512, 512), dtype=np.int8)

        for index, image_name in enumerate(image_files):
            image_path = os.path.join(abs_folder_path, image_name)

            # Read the data and save the pixel_array which will have a 
            # shape of around (700, 512, 512), the 512s being consistent.
            im = pydicom.dcmread(image_path).pixel_array

            # Due to the image using -10000 as "no value" and values between
            # -1000 and 0 as "value" we can normalize the image by adding
            # 10000 to every value. Then clipping every value to 0 and lobe_id.
            # Then we add this matrix to the model. This causes all pixels
            # of that type to have that id. This being implemented in 
            # completely in numpy speeds it up at least ten-fold. Note
            # that in case later types are at the same coordinates these
            # will be overwritten.
            im = np.clip(np.add(im, 10000), 0, lobe_id)
            model[index] = np.add(model[index], im)

            # This if else part adds the bronchus. But it tries to also
            # label the bronchus depending on which lobe they are in. The
            # problem with this approach was that the lobes do not share
            # any coordinates with the bronchus, therefore this did not
            # label any of the bronchus. So it is not in use for now.
            # if folder == 'Bronchus':
            #     im = np.clip(np.add(im, 10000), 0, lobe_id)
            #     model[index] = np.add(model[index], im)
            # else:
            #     im = np.clip(np.add(im, 10000), 1, lobe_id)
            #     model[index] = np.multiply(model[index], im)

            curr_sum += np.sum(im)//lobe_id
        print(f"{folder} pixel count:\t {curr_sum:,}")
        total_sum += curr_sum

    # Create folders if they do not exist
    if not os.path.exists(processed_data_path):
        os.makedirs(processed_data_path)

    # Print sums of the model for easier debugging
    print(f"Non empty pixels:\t {np.count_nonzero(model):,}")
    # print("Model sum: %d" % np.sum(model))
    # Save as numpy binary file to given location
    np.save(os.path.join(processed_data_path, "model"), model)

    class CoordinateOverlapException(Exception):
        pass

    if total_sum != np.count_nonzero(model):
        raise CoordinateOverlapException("ERROR: It seems like some coords overlap with other coords, "
                                         "meaning some data may have been lost.")


if __name__ == "__main__":
    save_images_as_npy(input_data_path, output_data_path)
