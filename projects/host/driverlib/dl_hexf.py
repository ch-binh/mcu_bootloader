import time
from dl_uart import *
from common.memory_map import *
from dl_file import *

#
# DEFINES AND VARIABLES
#============================================================================


class IHexRecType:
    """
    Record types for Intel HEX format.
    """
    DATA = 0x00
    EOF = 0x01
    EXT_SEG_ADDR = 0x02
    EXT_LINEAR_ADDR = 0x04
    START_SEG_ADDR = 0x03
    START_LINEAR_ADDR = 0x05


_image_info = ImageInfo()


#
# Command functions: Only need this one
#============================================================================
def dl_hexf_readf(file_path: str) -> ImageInfo:
    """
    Read and verify the hex file, and store the image in RAM.
    """
    print("Verify file path: opening file...")
    try:
        with open(file_path, 'rb') as file:
            print("Verify file path: file opened successfully")
            # Verify the hex data
            if not dl_hexf_verify_file(file):
                print("Hex file is invalid")
                return False

            # Also to determine the start and end address
            dl_hexf_get_addr_boundary(_image_info, file)

            # Store image in RAM so can be used to verify later
            dl_hexf_shadow_read(_image_info, file)

            return _image_info

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except IOError:
        print(f"An error occurred while reading the file: {file_path}")
        return None


#=================================================================
@staticmethod
def dl_hexf_verify_file(file) -> bool:
    """
    Verify the hex file by checking the checksum of each line.
    """
    # Verify file content
    print("Verify file content: reading file...")
    file.seek(0, 0)  # return cursor to start of line

    for line in file:
        hex_line = dl_hexf_line_breakdown(line)
        # check validation, Hex line contains ":" at the beginning
        if hex_line[0] != ord(":"):
            print(f"error, first byte is not \":\": {hex_line[0]} with {':'}")
            return False

        # prepare check checksum
        checksum_data = []
        for i in range(1, len(hex_line) - 2):
            if isinstance(hex_line[i], int):
                checksum_data.append(hex_line[i])
            elif isinstance(hex_line[i], list):
                checksum_data.extend(hex_line[i])
        # check checksum
        if (checksum_calc(checksum_data) != hex_line[5]):
            print("Checksum not pass, recheck the HEX file")
            return False
    print("Verify file content: complete")
    return True


@staticmethod
def dl_hexf_get_addr_boundary(image_buf: ImageInfo, file) -> bool:
    """
    Read the hex file and determine the start and end addresses of the data.
    """
    # read line
    main_addr = 0
    s_addr = 0xFFFFFFFF
    e_addr = 0x00000000

    file.seek(0, 0)  # return cursor to start of line

    print("Finding boundary addresss: reading file...")
    for line in file:
        hex_line = dl_hexf_line_breakdown(line)

        # if indicating main address data, save main address
        if hex_line[3] == IHexRecType.EXT_LINEAR_ADDR:
            main_addr = hex_line[4]
        # if indicating data, save start and end address
        elif hex_line[3] == IHexRecType.DATA:
            line_addr = main_addr + (hex_line[2][0] << 8 | hex_line[2][1])

            # update start and end address value
            if line_addr < s_addr:
                s_addr = line_addr
            if line_addr > e_addr:
                e_addr = line_addr + hex_line[1] - 1

    image_buf.main_addr = main_addr
    image_buf.s_addr = s_addr
    image_buf.e_addr = e_addr
    print("Finding boundary addresss: File read complete..")
    return True


@staticmethod
def dl_hexf_shadow_read(image_buf: ImageInfo, f) -> bool:
    f.seek(0, 0)  # return cursor to start of line

    print("Shadowing hex file: reading file...")
    for line in f:
        hex_line = dl_hexf_line_breakdown(line)

        # if indicating data, save start and end address
        if hex_line[3] == IHexRecType.DATA:
            line_addr = image_buf.main_addr + (hex_line[2][0] << 8
                                               | hex_line[2][1])
            for i in range(hex_line[1]):
                # read data from hex line and store in memory
                image_buf.mem_buffer[line_addr - image_buf.s_addr +
                                     i] = hex_line[4][i]

    print("Shadowing hex file: memory copy success")

    return True


@staticmethod
def dl_hexf_line_breakdown(line: str) -> list:
    """
    Breaks down a single line of a hex file into its components.

    Args:
        line (str): A single line from the hex file.

    Returns:
        list: A list containing the following components:
            - s_sym (str): Start symbol (e.g., ':').
            - data_len (int): Length of the data in bytes.
            - addr (list[int]): Address as a list of two bytes.
            - rec_type (int): Record type.
            - data (list[int]): Data bytes as a list of integers.
            - checksum (int): Checksum value.
            - eol (str): End of line characters.
    """
    # Extract components from the line
    start_symbol = line[0]
    data_length = int(line[1:3], 16)
    address = [int(line[3:5], 16), int(line[5:7], 16)]
    record_type = int(line[7:9], 16)

    # Extract data bytes
    data = [int(line[i:i + 2], 16) for i in range(9, 9 + (data_length * 2), 2)]

    # Extract checksum and end of line
    checksum = int(line[-4:-2], 16)
    end_of_line = line[-2:]

    # Return the parsed components
    return [
        start_symbol, data_length, address, record_type, data, checksum,
        end_of_line
    ]



