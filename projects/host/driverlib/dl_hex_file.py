


import time
from dl_uart import *
import utils.crc_32 as crc_32
from common.memory_map import *

global period
global main_address
global START_ADR
global END_ADR
global END_ADR_OFFSET
global is_first_read_attempt
global SIZE
global memory_str

LINE_TO_READ = 9999  # define number of line to read and sent
KB = 1024  # size of KB

START_ADR = "00000000"
END_ADR = "00000000"
main_address = "0001"
start_code = ""
byte_count = ""
line_adr = ""
record_type = ""
datapart = ""
checksum = ""
data_EOL = ""
start_time = 1


blanking_address = "00002000"
blanking_size = "00002000"


END_ADR_OFFSET = 0
is_first_read_attempt = True
FLASH_SIZE = 16*KB  # 16kB
SECTOR_SIZE = KB
memory_str = ["FF"]*FLASH_SIZE


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
                if not verify_file(line, hex_file, num_byte=8):
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
    erase_len = int((erase_len + SECTOR_SIZE - 1) / SECTOR_SIZE)*SECTOR_SIZE
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
            line_str = write_line_to_mem(line, hex_file,
                                         n_lines, line_counter)
            # send line
            send_line(UART_PORT, line_str)

            # calculate read and send time
            period = time.time() - start_time
            print(" |", round(period*len(n_lines), 2), "s")
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
    image_crc = crc_32.crc32(memory_byte_list[:end_ptr])
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
                sector_crc = crc_32.crc32(
                    memory_byte_list[start_ptr:start_ptr+crc_len-1])
                test_case_1 += 10
            else:
                sector_crc = crc_32.crc32(
                    memory_byte_list[start_ptr:start_ptr+crc_len])
                test_case_1 += 1

            

            print("Prepare to send: ", crc_start_addr, crc_len)
            send_crc_cmd(u_port, crc_start_addr,
                         crc_len, sector_crc)

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
                        data_str = read_hex_sector(
                            line, hex_file, start_ptr)
                        if data_str != None:
                            # print(data_str)
                            send_line(u_port, data_str)

                    # calculate and send crc

                    print(start_ptr, end_ptr, crc_len)
                    crc_len = end_ptr - start_ptr
                    sector_crc = crc_32.crc32(
                        memory_byte_list[start_ptr:start_ptr+crc_len])

                    send_crc_cmd(u_port, crc_start_addr,
                                 crc_len, sector_crc)
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


def verify_file(line_data: str, hex_file: str, num_byte: int) -> bool:
    """
    Algorithm to read and verify a hex file.

    Args:
        line_data (str): Individual line from the hex file.
        hex_file (str): Path to the selected hex file.
        num_byte (int): number of byte each flashing require

    Returns:
        bool: True if verification is successful, False otherwise.
    """

    global main_address, START_ADR, END_ADR
    global is_first_read_attempt
    global memory_str
    global END_ADR_OFFSET
    # read line
    hex_file.seek(-len(line_data), 1)
    data_list = parse_hex_line(hex_file, len(line_data))
    start_code, byte_count, line_adr, record_type, datapart, checksum, eol = data_list

    # check validation, Hex line contains ":" at the beginning
    if start_code != ":":
        print("error, first byte is not \":\"")
        return False

    # prepare for line checksum
    data_string = byte_count + line_adr + record_type + datapart
    if not verify_checksum(data_string, checksum):
        print("checksum not pass, recheck the HEX file")
        return False
    # ===============================

    # if indicating main address data, save main address
    if record_type == "04":
        main_address = datapart
    # if indicating data, save start and end address
    elif record_type == "00":
        # First read attempt to initialize data address value
        full_address = main_address + line_adr
        if is_first_read_attempt:
            START_ADR = full_address
            is_first_read_attempt = False
        elif int(START_ADR, 16) >= int(full_address, 16):
            START_ADR = full_address

        # Save end address value
        if int(END_ADR, 16) <= int(full_address, 16):
            END_ADR = full_address
            END_ADR_OFFSET = int(byte_count[:2], 16)

    return True


def write_line_to_mem(line_data: str, hex_file: str, n_line: int, line_ctr: int) -> str:
    """
    Algorithm to read line of hex data. Additionally printing out
    downloading speed

    Args:
        line_data (str): Individual line from the hex file.
        hex_file (str): Path to the selected hex file.
        total_line (int): Total number of hex lines.
        line_counter (int): Counter to track the current line.

    Returns:
        str: The function returns the entire data string, including:
            - Data address
            - Data string
            - Data checksum
            - Data CRC checksum
            - CRC for the whole image
    """
    global period
    global main_address, START_ADR, END_ADR
    global is_first_read_attempt
    global memory_str

    # Output to terminal current download progress
    print(line_ctr, "/", len(n_line), "|",
          f'{round(line_ctr*100/len(n_line),2):.2f}' + "%", end="")

    # return cursor to start of line
    hex_file.seek(-len(line_data), 1)
    data_list = parse_hex_line(hex_file, len(line_data))
    start_code, byte_count, line_adr, record_type, datapart, checksum, eol = data_list

    # write "binary" file here because need to determine start and end address first

    full_address = main_address + line_adr
    start_adr = int(START_ADR, 16)
    current_adr = int(full_address, 16)
    # write to memory bin
    if record_type == "04":
        main_address = datapart
    # if indicating data, save start and end address
    elif record_type == "00":
        j = 0
        # First read attempt to initialize data address value
        for i in range(int(byte_count[j:j+2], base=16)):
            memory_str[current_adr - start_adr + i] = datapart[j:j+2]
            j += 2

    # prepare for line checksum
    data_string = byte_count + line_adr + record_type + datapart + checksum

    return data_string


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
    for _ in range(int(len(data_str)/2)):
        data = int(data_str[counter:counter+2], base=16)
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


def parse_hex_line(file: str, line_len: int) -> list:
    """
    Parse a hex line from the given file and return its components as a list.

    Args:
        file (str): A file-like object from which the hex line is read. Should be opened in read mode.
        line_len (int): The length of the hex line, including all components.

    Returns:
        List[str]: A list containing the parsed components of the hex line:
            - list[0]: The start delimiter, always ":".
            - list[1]: The byte count of the data part.
            - list[2]: The address where the data is stored.
            - list[3]: The record type (e.g., data, end of file).
            - list[4]: The data part of the line.
            - list[5]: The checksum of the data.
            - list[6]: End of line characters (e.g., "\r\n").
    """
    return [
        file.read(1).decode(),          # Read ":"
        file.read(2).decode(),          # Read byte count
        file.read(4).decode(),          # Read address
        file.read(2).decode(),          # Read record type
        file.read(line_len - 13).decode(),  # Read data
        file.read(2).decode(),          # Read checksum
        file.read(2).decode()           # Bypass /r/n
    ]


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
        if ((offset_address < start_ptr and (offset_address + byte_len > start_ptr)) or
                offset_address >= start_ptr):
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
    data = b''.join(value.to_bytes(2, byteorder='little')
                    for value in data_list)

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
    for i in range(int(len(str_list)/2)):
        byte_list.append(i)
        byte_list[i] = int(str_list[counter+1], base=16)
        byte_list[i] = byte_list[i]*0x100 + int(str_list[counter], base=16)
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
