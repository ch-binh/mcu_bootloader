from dl_file import *

#
# DEFINES AND VARIABLES
#============================================================================

_image_info = ImageInfo()


#
# Command functions: Only need this one
#============================================================================

def dl_bin_readf(file_path: str) -> ImageInfo:
    """
    Read and verify the hex file, and store the image in RAM.
    """
    print("Verify file path: opening file...")
    try:
        with open(file_path, 'rb') as file:
            print("Verify file path: file opened successfully")


            # Also to determine the start and end address
            # dl_hexf_get_addr_boundary(_image_info, file)
            # _image_info.
            

            # # Store image in RAM so can be used to verify later
            # dl_hexf_shadow_read(_image_info, file)

            return _image_info

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except IOError:
        print(f"An error occurred while reading the file: {file_path}")
        return None

