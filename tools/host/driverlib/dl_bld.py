from dl_file import *
from dl_uart import *
from utils.checksum import *
from utils.crc import crc32_lookup_tb
from utils.measure import measure_exe_time

#
# VARIABLES AND DEFINES
#============================================================================


class Cmd():
    """
    Contains the request commands
    """
    CMD_NOP = 0x00
    CMD_ENTER_BLD = 0x01
    CMD_GET_BLD_VER = 0x02
    CMD_CHECK_BLANKING = 0x03
    CMD_WRITE = 0x04
    CMD_WRITE_CRC = 0x05
    CMD_ERASE = 0x06
    CMD_UPLOAD = 0x07
    CMD_IMAGE_CRC_VERIFY = 0x08
    CMD_SYSRST = 0x09
    CMD_EXIT_BLD = 0x0A
    CMD_NUM = 0x0A
    CMD_UNDEFINED = 0xFF


#
# Static functions
# They are utility functions that can be used independently.
#============================================================================
@staticmethod
def dl_bld_prep_packet(length: int,
                       cmd: int,
                       data: list,
                       csum: int = 1,
                       crc32: int = 0,
                       req_ack: int = 0) -> bytearray:
    """
    Prepare a packet to be sent over UART.

    Args:
        length (int): Total length of the packet including all fields.
        cmd (int): Command identifier byte.
        data (list): List of data bytes to include in the packet.
        req_ack (int): Acknowledgment request flag (1 for ACK, 0 for no ACK).
        csum (int): Checksum flag (1 to include checksum, 0 otherwise).
        crc32 (int): CRC32 flag (1 to include CRC32, 0 otherwise).
        
    Returns:
        bytearray: The prepared packet.
    """

    packet = [length, cmd] + data + [req_ack]
    # recommendation, if length is > 64 bytes using crc
    if crc32:
        crc = crc32_lookup_tb(packet)
        packet.extend((crc >> (24 - i * 8)) & 0xFF for i in range(4))
    elif csum:
        packet.append(checksum_calc(packet))

    return bytearray(packet)


#
# Command functions
#============================================================================


# CMD 2: GET BOOTLOADER VERSION
def dl_bld_get_version(uart_port: serial.Serial) -> bytearray:
    """
    Retrieve the bootloader version from the MCU.

    Notes:
        The data sent includes:
        - 1 length byte (value = 3)
        - 1 command byte (CMD_GET_BLD_VER)
        - 1 checksum byte
    """
    # Prepare the transmit buffer
    tx_buf = dl_bld_prep_packet(length=4,
                                cmd=Cmd.CMD_GET_BLD_VER,
                                data=[],
                                csum=1,
                                req_ack=1)

    # Send the command over UART
    dl_uart_write(uart_port, tx_buf)
    # handle response
    resp = dl_uart_read_resp(uart_port)
    return resp if resp[0] else resp[0]


# CMD 3: CHECK BLANKING
def dl_bld_blanking(uart_port: serial.Serial,
                    fl_adr,
                    size,
                    req_ack: int = 1) -> bool:
    """
    Check blanking of memory range based on starting address and memory length.
    
    Data sent includes:
        1b len, 1b cmd, 4b address, 4b size, 1b req_ack, 1b checksum
    """
    # check connection first
    if not dl_bld_get_version(uart_port):
        print("Read BLD version failed, MCU might be out of bootloader")
        return 0
    # Connection confirmed, continue function

    packet_data = []

    if isinstance(fl_adr, str):
        packet_data.extend(
            int(fl_adr[i * 2:i * 2 + 2], base=16) for i in range(4))
        packet_data.extend(
            int(size[i * 2:i * 2 + 2], base=16) for i in range(4))
    elif isinstance(fl_adr, int):
        packet_data.extend((fl_adr >> (24 - i * 8)) & 0xFF for i in range(4))
        packet_data.extend((size >> (24 - i * 8)) & 0xFF for i in range(4))

    tx_buf = dl_bld_prep_packet(length=len(packet_data) + 4,
                                cmd=Cmd.CMD_CHECK_BLANKING,
                                data=packet_data,
                                csum=1,
                                req_ack=req_ack)
    dl_uart_write(uart_port, tx_buf)

    # Handle response
    resp = dl_uart_read_resp(uart_port)
    return resp[0]


# CMD 4: WRITE
def dl_bld_write(uart_port: serial.Serial,
                 fl_adr,
                 data: bytearray,
                 req_ack: int = 0) -> bytearray:
    """
    Send data to the MCU to be written to flash memory.

    Data sent includes:
        1b len, 1b cmd, 4b address, n data, 1b req_ack, 1b checksum
    """
    # check connection first
    if not dl_bld_get_version(uart_port):
        print("Read BLD version failed, MCU might be out of bootloader")
        return 0
    # Connection confirmed, continue function

    packet_data = []

    if isinstance(fl_adr, str):
        packet_data.extend(
            int(fl_adr[i * 2:i * 2 + 2], base=16) for i in range(4))
    elif isinstance(fl_adr, int):
        packet_data.extend((fl_adr >> (24 - i * 8)) & 0xFF for i in range(4))

    #padding data to 4 bytes
    if len(data) % 4 != 0:
        for _ in range(4 - len(data) % 4):
            data.extend([0xFF])

    packet_data.extend(data)

    tx_buf = dl_bld_prep_packet(length=len(packet_data) + 4,
                                cmd=Cmd.CMD_WRITE,
                                data=packet_data,
                                csum=1,
                                req_ack=req_ack)
    dl_uart_write(uart_port, tx_buf)

    # Handle response
    if req_ack == 1:
        resp = dl_uart_read_resp(uart_port)
        return resp[0]  # ACK 1 or 0

    return 1


# CMD 5: ERASE
def dl_bld_erase(uart_port: serial.Serial,
                 fl_adr,
                 size,
                 req_ack: int = 0) -> bytearray:
    """
    Send erase command to MCU. Including starting address and size of memory to be erased.

    Notes: Data sent includes:
        1 cmd byte
        4 address bytes
        4 memory size bytes
        1 checksum byte

    Args:
        uart_port (serial.Serial): The UART port object used for communication.
        fl_adr (int/str): Start address of the memory range to be erased (int or hex string).
        size (int/str): Size of data to be erased (int or hex string).
        req_ack (int): Acknowledgment request flag (1 for ACK, 0 for no ACK).

    Returns:
        bytearray: The response from the MCU after the erase operation.
    """
    # check connection first
    if not dl_bld_get_version(uart_port):
        print("Read BLD version failed, MCU might be out of bootloader")
        return 0
    # Connection confirmed, continue function

    packet_data = []

    if isinstance(fl_adr, str):
        packet_data.extend(
            int(fl_adr[i * 2:i * 2 + 2], base=16) for i in range(4))
        packet_data.extend(
            int(size[i * 2:i * 2 + 2], base=16) for i in range(4))
    elif isinstance(fl_adr, int):
        packet_data.extend((fl_adr >> (24 - i * 8)) & 0xFF for i in range(4))
        packet_data.extend((size >> (24 - i * 8)) & 0xFF for i in range(4))

    tx_buf = dl_bld_prep_packet(length=len(packet_data) + 4,
                                cmd=Cmd.CMD_ERASE,
                                data=packet_data,
                                csum=1,
                                req_ack=req_ack)
    dl_uart_write(uart_port, tx_buf)

    # Handle response
    if req_ack == 1:
        resp = dl_uart_read_resp(uart_port)
        return resp[0]  # ACK 1 or 0

    return 1


#
# CMD 6: UPLOADING
#=====================================================================
def dl_bld_upload(uart_port: serial.Serial):
    # check connection first
    if not dl_bld_get_version(uart_port):
        print("Read BLD version failed, MCU might be out of bootloader")
        return 0
    # Connection confirmed, continue function

    # Select file
    FileInfo.scan_files(get_binf=True, get_hexf=True, get_elf=True)
    FileInfo.select_files()
    # Upload the selected file
    fpath = FileInfo.fpath
    if fpath.endswith(".hex"):
        return dl_bld_upload_hexf(uart_port, fpath)
    elif fpath.endswith(".bin"):
        start_addr = input("Input start address (ex: 0x1800 or 6144): ")
        return dl_bld_upload_binf(uart_port, fpath, start_addr)

        print("Uploading bin file")
    elif fpath.endswith(".elf"):
        print("Uploading elf file")

    return 1


@measure_exe_time
@staticmethod
def dl_bld_upload_hexf(uart_port: serial.Serial, file_path: str):
    from dl_hexf import dl_hexf_readf
    # upload image
    image_info = dl_hexf_readf(file_path)
    return dl_bld_upload_target_file(uart_port, image_info)


@measure_exe_time
@staticmethod
def dl_bld_upload_binf(uart_port: serial.Serial, file_path: str, start_addr):
    from dl_binf import dl_bin_readf
    # convert str to int
    if isinstance(start_addr, str):
        if start_addr.startswith("0x"):
            start_addr = int(start_addr[2:], base=16)
        else:
            start_addr = int(start_addr, base=10)
    

    # prepare upload image
    image_info = dl_bin_readf(file_path, start_addr)

    # upload image
    return dl_bld_upload_target_file(uart_port, image_info)


@staticmethod
def dl_bld_upload_target_file(uart_port: serial.Serial, image_info: ImageInfo):
    # Prepare the transmit buffer
    chunk_size = 240  # 240 bytes /max = 240
    image_size = image_info.e_addr - image_info.s_addr + 1
    num_of_packets = int(
        image_size /
        chunk_size) + 1  # last packet may be smaller than 128 bytes

    # 1. Clear the flash image
    print("Uploading file: Cleaning flash image...")
    start_addr = image_info.main_addr + image_info.s_addr
    if not dl_bld_erase(uart_port, start_addr, image_size, 1):
        print("Image cleaning failed")
        return 0
    print("Uploading file: Cleaning flash image success")

    # 2. Send write command
    print("Uploading file: writing flash image...")
    for i in range(num_of_packets):
        num_of_attempt = 0
        while (1):
            num_of_attempt += 1
            packet_data = []
            # add address
            write_addr = (image_info.main_addr <<
                          16) + image_info.s_addr + chunk_size * i
            packet_data.extend(
                (write_addr >> (24 - i * 8)) & 0xFF for i in range(4))

            # add data, rearrange data to big endian format
            for j in range(0, chunk_size, 4):
                for k in range(4):
                    packet_data.append(image_info.mem_buffer[(chunk_size * i) +
                                                             j + 3 - k])

            tx_buf = dl_bld_prep_packet(length=len(packet_data) + 7,
                                        cmd=Cmd.CMD_WRITE_CRC,
                                        data=packet_data,
                                        crc32=1,
                                        req_ack=1)

            dl_uart_write(uart_port, tx_buf)

            # Handle response
            resp = dl_uart_read_resp(uart_port)
            if num_of_attempt == 3:
                print("Retry failed, abort")
                exit()
            if resp[0]:  # ACK return success
                break
            else:
                print(f"Write @{write_addr} failed, retry: {num_of_attempt}")

    print("Uploading file: write flash image success")

    # 3. CRC check
    if dl_bld_check_img_crc(uart_port, start_addr, image_size,
                            image_info.mem_buffer[:image_size]):
        return 1
    return 0


#
# CMD 7: CHECK CRC
#=====================================================================
def dl_bld_check_img_crc(uart_port: serial.Serial, addr: int, size: int,
                         data: bytearray):
    """
    Send check image crc to MCU. Including starting address and size of memory to be erased.

    Notes: Data sent includes:
        1 length
        1 cmd byte
        4 address bytes
        4 memory size bytes
        4 crc32 result bytes
        1 req ack byte
        1 checksum byte
        
        
    """
    print(f"Check image crc: mem - {addr}, size - {size}, checking...")

    crc_result = crc32_lookup_tb(data)

    packet_data = []
    packet_data.extend((addr >> (24 - i * 8)) & 0xFF for i in range(4))
    packet_data.extend((size >> (24 - i * 8)) & 0xFF for i in range(4))
    packet_data.extend((crc_result >> (24 - i * 8)) & 0xFF for i in range(4))

    tx_buf = dl_bld_prep_packet(length=len(packet_data) + 4,
                                cmd=Cmd.CMD_IMAGE_CRC_VERIFY,
                                data=packet_data,
                                csum=1,
                                req_ack=1)

    dl_uart_write(uart_port, tx_buf)

    # Handle response
    resp = dl_uart_read_resp(uart_port)
    if not resp[0]:  # ACK return fail
        print("Debug here")
        exit()

    print(f"Check image crc: CRC correct")
    return resp[0]


#
# CMD 9: EXIT BOOTLOADER
#=====================================================================
def dl_bld_exit(uart_port: serial.Serial):

    print("Exit Bootloader: exiting...")
    tx_buf = dl_bld_prep_packet(length=4,
                                cmd=Cmd.CMD_EXIT_BLD,
                                data=[],
                                csum=1,
                                req_ack=1)

    dl_uart_write(uart_port, tx_buf)

    # Handle response
    resp = dl_uart_read_resp(uart_port)
    if not resp[0]:  # ACK return fail
        print("Debug here")
        exit()

    return resp[0]
