import time

from dl_hexf import dl_hexf_upload_file
from dl_uart import *
from utils.checksum import *

#
# VARIABLES AND DEFINES
#============================================================================


### Package info
### SIZE [1 Byte] | DATA n... | CHECKSUM
###
class Def:
    WAIT_TIME = 0.01


class UartPkg:
    UART_END_BYTE = 0xFE


class Cmd():
    """
    Contains the request commands
    """
    CMD_NOP = 0x00
    CMD_ENTER_BLD = 0x01
    CMD_GET_BLD_VER = 0x02
    CMD_CHECK_BLANKING = 0x03
    CMD_WRITE = 0x04
    CMD_ERASE = 0x05
    CMD_UPLOADING = 0x06
    CMD_CHECK_CRC_MODE = 0x07
    CMD_SYSRST = 0x08
    CMD_EXIT_BLD = 0x09
    CMD_NUM = 0x0A
    CMD_UNDEFINED = 0xFF


#
# Static functions
# Note: These functions are not part of the class and
# are not intended to be used as methods.
# They are utility functions that can be used independently.
#============================================================================
@staticmethod
def dl_bld_prep_packet(length: int, cmd: int, data: list,
                       req_ack: int) -> bytearray:
    """
    Prepare a packet to be sent over UART.

    Args:
        length (int): Total length of the packet including all fields.
        cmd (int): Command identifier byte.
        data (list): List of data bytes to include in the packet.
        req_ack (int): Acknowledgment request flag (1 for ACK, 0 for no ACK).

    Returns:
        bytearray: The prepared packet.
    """
    packet = [length, cmd] + data + [req_ack]
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

    Args:
        uart_port (serial.Serial): The UART port object used for communication.
        
    Returns:
        bytearray: The response from the MCU containing the bootloader version.
    """
    # Prepare the transmit buffer
    tx_buf = dl_bld_prep_packet(length=4,
                                cmd=Cmd.CMD_GET_BLD_VER,
                                data=[],
                                req_ack=1)

    # Send the command over UART
    dl_uart_write(uart_port, tx_buf)

    time.sleep(Def.WAIT_TIME)
    return dl_uart_read_resp(uart_port)


# CMD 3: CHECK BLANKING
def dl_bld_blanking(uart_port: serial.Serial,
                    fl_adr,
                    size,
                    req_ack: int = 1) -> bool:
    """
    Check blanking of memory range based on starting address and memory length.
    
    Data sent includes:
        1b len, 1b cmd, 4b address, 4b size, 1b req_ack, 1b checksum
        
    Args:
        uart_port (serial.Serial): The UART port object used for communication.
        fl_adr (int/str): Start address of the memory range to be checked (int or hex string).
        size (int/str): Size of data to be checked (int or hex string).
        req_ack (int): Acknowledgment request flag (1 for ACK, 0 for no ACK).

    Returns:
        bool: True if memory range is clean. False if it is dirty.
    """
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
                                req_ack=req_ack)
    dl_uart_write(uart_port, tx_buf)

    time.sleep(Def.WAIT_TIME)
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

    Args:
        uart_port (serial.Serial): The UART port object used for communication.
        fl_adr (int/str): Start address of the memory range to be written (int or hex string).
        data (bytearray): Data to be written to the memory.
        req_ack (int): Acknowledgment request flag (1 for ACK, 0 for no ACK).

    Returns:
        bytearray: The response from the MCU after the write operation.
    """
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
                                req_ack=req_ack)
    dl_uart_write(uart_port, tx_buf)

    # Handle response
    if req_ack == 1:
        time.sleep(Def.WAIT_TIME)
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
                                req_ack=req_ack)
    dl_uart_write(uart_port, tx_buf)

    # Handle response
    if req_ack == 1:
        time.sleep(Def.WAIT_TIME)
        resp = dl_uart_read_resp(uart_port)
        return resp[0]  # ACK 1 or 0

    return 1

# CMD 6: UPLOADING
def dl_bld_upload_file(uart_port: serial.Serial, file_path: str):
    if file_path.endswith(".hex"):
        dl_hexf_upload_file(uart_port, file_path)
        print("Uploading hex file")
    elif file_path.endswith(".bin"):
        print("Uploading bin file")
    elif file_path.endswith(".elf"):
        print("Uploading elf file")
    
    
    return 1

# CMD 7: CHECK CRC

def dl_bld_check_crc(uart_port:serial.Serial):
    pass
    
