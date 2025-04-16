from dl_file import *

#
# DEFINES AND VARIABLES
#============================================================================

_image_info = ImageInfo()

#
# Command functions: Only need this one
#============================================================================


def dl_bin_readf(file_path: str, start_addr: int = 0x00000000) -> ImageInfo:
    """
    Read and verify the BIN file, and store the image in RAM.
    """
    print("Verify file path: opening file...")
    try:
        with open(file_path, 'rb') as file:
            print("Verify file path: file opened successfully")

            _image_info.s_addr = start_addr & 0xFFFF
            _image_info.main_addr = (start_addr >> 16) & 0xFFFF
            dl_binf_shadow_read(_image_info, file)
            return _image_info

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except IOError:
        print(f"An error occurred while reading the file: {file_path}")
        return None


@staticmethod
def dl_binf_shadow_read(image: ImageInfo, f) -> None:
    f.seek(0, 0)  # return cursor to start of line

    print("Shadowing bin file: reading file...")
    data = f.read()

    for i, byte in enumerate(data):
        image.mem_buffer[i] = byte

    image.e_addr = image.s_addr + len(data) - 1
    print("Shadowing bin file: memory copy success")
