import time
from dl_uart import *
from common.memory_map import *


#
# DEFINES AND VARIABLES
#============================================================================
class ImageInfo:

    def __init__(self,
                 flash_size=0x2000,
                 main_addr=0x0000,
                 cur_addr=0x0000,
                 s_addr=0xFFFFFFFF,
                 e_addr=0x00000000):
        self.flash_size = flash_size
        self.main_addr = main_addr
        self.cur_addr = cur_addr
        self.s_addr = s_addr
        self.e_addr = e_addr
        self.mem_buffer = [0xFF] * flash_size


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
# Command functions
#============================================================================
def dl_hexf_read_file(file_path: str) -> ImageInfo:
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
def dl_hexf_shadow_read(image_buf: ImageInfo, file) -> bool:
    file.seek(0, 0)  # return cursor to start of line

    print("Shadowing hex file: reading file...")
    for line in file:
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





#=============================================================================
#
#
#
# OLD functions
#============================================================================
def send_hex_file(file_path, check_crc: int = True) -> None:
    """
    Processing hex file. Which including verify hex file,
    send hex file, check data transmission status

    Args:
        file_path (str): Hex file path
    """

    global period, start_time

    # Verify the hex data
    # Also to determine the start and end address
    try:
        with open(file_path, 'rb') as hex_file:
            hex_file.seek(0, 0)  # return cursor to start of line
            # read data
            line_counter = 0
            for line in hex_file:
                if not dl_hexf_verify_file(line, hex_file, num_byte=8):
                    exit()
                line_counter += 1
                if line_counter == LINE_TO_READ:
                    break

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        exit()
    except IOError:
        print(f"An error occurred while reading the file: {file_path}")
        exit()

    print("==============Verify complete===================")
    # send erase
    erase_len = int(END_ADR, 16) - int(START_ADR, 16) + END_ADR_OFFSET
    erase_len = int((erase_len + SECTOR_SIZE - 1) / SECTOR_SIZE) * SECTOR_SIZE
    is_erased = send_erase_cmd(UART_PORT, int(START_ADR, 16), erase_len)
    if is_erased:
        print("Flash erase success")
    else:
        print("Fail to erase before downloading")
        exit()

    # After successful verification, data is read and sent ============
    with open(file_path, 'rb') as hex_file:

        n_lines = hex_file.readlines()
        hex_file.seek(0, 0)  # return cursor to start of line

        # read data
        line_counter = 0
        for line in hex_file:  # using line loop for check EOF
            period = 0
            start_time = time.time()
            line_counter += 1
            # read line and send it
            line_str = write_line_to_mem(line, hex_file, n_lines, line_counter)
            # send line
            send_line(UART_PORT, line_str)

            # calculate read and send time
            period = time.time() - start_time
            print(" |", round(period * len(n_lines), 2), "s")
            if line_counter == LINE_TO_READ:
                break

        # ==========
        print("====================")
        print("downloading end")
        # CRC_check
        if (check_crc):
            print("====================")
            print("Check crc")
            send_crc_check(UART_PORT, hex_file)

        # exit CRC check, downloading is completed
        print("downloading complete. Exiting")
        exit()


def send_crc_check(u_port, hex_file):
    """

    """

    # define variable
    global memory_str, END_ADR, START_ADR, END_ADR_OFFSET

    crc_start_addr = int(START_ADR, 16)
    memory_byte_list = []
    # build memory list with each element is a byte

    for element in memory_str:
        memory_byte_list.append(int(element, base=16))

    # check crc whole image first

    end_ptr = int(END_ADR, 16) - int(START_ADR, 16) + END_ADR_OFFSET
    image_crc = crc32.crc32(memory_byte_list[:end_ptr])
    # print(memory_byte_list[:end_ptr])
    print("====================")
    print("start adr: ", START_ADR)
    print("end adr: ", END_ADR)
    print("end address offset: ", END_ADR_OFFSET)
    print("end pointer is: ", end_ptr)
    print("image crc: ", image_crc)
    print("====================")

    send_crc_cmd(u_port, crc_start_addr, end_ptr, image_crc)

    delay_tick(WAIT_FOR_RES)

    # if fail, check crc for each individual sector
    if is_sent_success(u_port):
        pass
    else:
        is_reach_end = False
        element_size = 1  # each element is 2 bytes
        chunk_size = int(KB / element_size)
        start_ptr = 0
        end_ptr = start_ptr + chunk_size
        test_case_1 = 10
        while (True):
            crc_len = end_ptr - start_ptr
            if test_case_1 == 1:
                sector_crc = crc32.crc32(
                    memory_byte_list[start_ptr:start_ptr + crc_len - 1])
                test_case_1 += 10
            else:
                sector_crc = crc32.crc32(
                    memory_byte_list[start_ptr:start_ptr + crc_len])
                test_case_1 += 1

            print("Prepare to send: ", crc_start_addr, crc_len)
            send_crc_cmd(u_port, crc_start_addr, crc_len, sector_crc)

            crc_start_addr += chunk_size

            delay_tick(WAIT_FOR_RES)

            if (is_sent_success(u_port)):
                if is_reach_end == True:
                    break

                start_ptr, end_ptr, is_reach_end = move_ptr(
                    start_ptr, end_ptr, KB)

            # if fail crc check, enter resend and crc check loop
            else:
                time_out = 0

                #   erase sector
                send_erase_cmd(u_port, crc_start_addr, SECTOR_SIZE)
                # write sector
                while (True):
                    # resend the hex sector  that fails crc
                    hex_file.seek(0, 0)
                    for line in hex_file:  # using line loop for check EOF
                        data_str = read_hex_sector(line, hex_file, start_ptr)
                        if data_str != None:
                            # print(data_str)
                            send_line(u_port, data_str)

                    # calculate and send crc

                    print(start_ptr, end_ptr, crc_len)
                    crc_len = end_ptr - start_ptr
                    sector_crc = crc32.crc32(
                        memory_byte_list[start_ptr:start_ptr + crc_len])

                    send_crc_cmd(u_port, crc_start_addr, crc_len, sector_crc)
                    delay_tick(WAIT_FOR_RES)

                    if (is_sent_success(u_port)):
                        if is_reach_end == True:
                            print("Read end, exiting")
                            exit()
                        # move start and end address to 1 sector
                        start_ptr, end_ptr, is_reach_end = move_ptr(
                            start_ptr, end_ptr, KB)
                        time_out = 0
                        break
                    else:
                        time_out += 1
                    if time_out >= 10:
                        print("CRC fails, exiting")
                        exit()


def send_line(u_port, data_str: str):
    """
    Algorithm to send hex line to UART COM

    Args:
        data_str (str): Individual line from the hex file.
    """
    data = 0
    counter = 0
    # raise is_downloading flag
    dl_uart_write(u_port, RqCmd.RQ_DOWNLOAD)
    # send data
    for _ in range(int(len(data_str) / 2)):
        data = int(data_str[counter:counter + 2], base=16)
        counter += 2
        dl_uart_write(u_port, data)

        # wait for ACK
    delay_tick(WAIT_FOR_RES)

    if (is_sent_success(u_port)):
        pass
    else:
        print("resend line...")
        delay_tick(WAIT_FOR_RES)
        send_line(u_port, data_str)


def read_hex_sector(current_line: str, hex_file: str, start_ptr: int) -> str:
    """
    Reads and processes a sector of hex data from the given file

    Args:
        current_line (str): The current line of the hex file being processed.
        hex_file (str): A file-like object representing the hex file to be read.
        start_ptr (int): The starting pointer in the sector, provided as an integer.

    Returns:
        str or None: Returns the data string if the current line is part of the target sector,
        otherwise returns `None` if the line does not belong to the sector.
    """

    global START_ADR, main_address, byte_len

    hex_file.seek(-len(current_line), 1)
    data_list = parse_hex_line(hex_file, len(current_line))

    start_code, byte_count, line_adr, record_type, datapart, checksum, eol = data_list

    data_string = byte_count + line_adr + record_type + datapart + checksum

    full_address = ""
    offset_address = 0
    if record_type == "04":
        main_address = datapart
    # if indicating data, check if current line is on the target sector
    elif record_type == "00":
        # First read attempt to initialize data address value
        full_address = main_address + line_adr

        offset_address = int(full_address, 16) - int(START_ADR, 16)

    if record_type != "01":
        byte_len = int(byte_count[:2], 16)
        # in case of start ptr in inside a hex line, not the beginning
        if ((offset_address < start_ptr and
             (offset_address + byte_len > start_ptr))
                or offset_address >= start_ptr):
            # limit to 1 sector
            if offset_address < (start_ptr + KB):
                return data_string

    elif record_type == "01":
        return data_string

    # if not in sector, return None
    return None


def crc16_ccitt_false(data_list: list[int]) -> int:
    """
    Calculate the CRC-16-CCITT (False) checksum for a given list of 16-bit integers.

    Args:
        data_list (list[int]): A list of 16-bit integer values to be processed.

    Returns:
        int: The calculated CRC-16-CCITT (False) checksum as a 16-bit integer.
    """
    # Parameters for CRC-16-CCITT (False)
    polynomial = 0x1021
    crc = 0xFFFF

    # Convert the list of 16-bit values into bytes (2 bytes per value, big-endian order)
    data = b''.join(
        value.to_bytes(2, byteorder='little') for value in data_list)

    # Process each byte
    for byte in data:
        crc ^= (byte << 8)  # XOR byte into the upper 8 bits of CRC
        for _ in range(8):
            if crc & 0x8000:  # if the uppermost bit is set
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1
            crc &= 0xFFFF  # Trim CRC to 16 bits

    return crc


def str_list_to_byte_list(str_list: list[str]):
    """
    Convert a list of string of hexadecimal values into a list of 16-bit integers in big-endian format.

    Args:
        string (str): A list of string containing hexadecimal values where each two characters 
                      represent a byte (e.g., ["0A0B", "0C0D"] for two bytes).

    Returns:
        list[int]: A list of 16-bit integers where each pair of hexadecimal characters 
                   is combined into a 16-bit value in little-endian format.
                   For example, "0A0B" becomes 0x0A0B.
    """
    counter = 0
    byte_list = []
    for i in range(int(len(str_list) / 2)):
        byte_list.append(i)
        byte_list[i] = int(str_list[counter + 1], base=16)
        byte_list[i] = byte_list[i] * 0x100 + int(str_list[counter], base=16)
        counter += 2

    return byte_list


def move_ptr(s_adr: int, e_adr: int, sector_size) -> list:
    """
    Move the pointer between start and end addresses, ensuring the pointer does not exceed 
    the image's end address. Adjusts the pointers based on the sector size.

    Args:
        s_adr (int): The current start address pointer.
        e_adr (int): The current end address pointer.
        sector_size (int): The size of the sector to process.

    Returns:
        list: A list containing:
            - The updated start address (`s_adr`).
            - The updated end address (`e_adr`).
            - A boolean flag `is_reach_end` indicating if the pointer reached the image's end.
    """
    global START_ADR, END_ADR, END_ADR_OFFSET
    element_size = 1  # each element is 2 bytes
    chunk_size = int(sector_size / element_size)
    is_reach_end = False

    s_adr = e_adr
    e_adr = s_adr + chunk_size
    # check if end address reach end
    image_end_address = (int(END_ADR, 16) - int(START_ADR, 16))

    if (e_adr > image_end_address):
        e_adr = image_end_address + END_ADR_OFFSET
        is_reach_end = True

    print(s_adr, e_adr, image_end_address)
    return [s_adr, e_adr, is_reach_end]
