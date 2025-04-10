import time

from dl_uart import *
from utils.checksum import *
### Package info
### SIZE [1 Byte] | DATA n... | CHECKSUM
###


class UartPkg:
    UART_END_BYTE = 0xFE

# CMD 1: ERASE
def dl_bld_erase(uart_port: serial.Serial, fl_adr, size) -> bool:
    """
    Send erase command to MCU. Including starting address and size of memory to be erased.
    First send blanking command, if returns dirty, erase command is sent. Otherwise, 
    The erase command is dismissed.

    Notes: Data sent including:
        1 cmd byte
        4 address bytes
        4 memory size bytes
        1 checksum byte

    Args:
        COM (object): The COM port object used for communication.
        s_adr (int/str): Start address of the memory range that to be erased
        size (int/str): Size of data to be erased

    Returns:
        bool: True if MCU is erased successfully, or memory is already clean. \
            False if not getting erase successful response.
    """

    if(dl_bld_blanking(uart_port, fl_adr, size)):
        print("Image is already blank, erase skipped")
        return True
    
    tx_buf = []
    
    # send first byte command
    tx_buf.append(11)  # length of data to be sent
    tx_buf.append(RqCmd.RQ_ERASE)

    if type(fl_adr) == str:
        # send start address of memory
        for i in range(4):
            tx_buf.append(int(fl_adr[i * 2:i * 2 + 2], base=16))
        # send size of memory range that want to be erased
        for i in range(4):
            tx_buf.append(int(size[i * 2:i * 2 + 2], base=16))

        checksum = checksum_calc(tx_buf)
        tx_buf.append(checksum)
        dl_uart_write(uart_port, tx_buf)

    elif type(fl_adr) == int:
        for i in range(4):
            tx_buf.append((fl_adr >> (24 - i * 8)) & 0xFF)
        for i in range(4):
            tx_buf.append((size >> (24 - i * 8)) & 0xFF)

        # send checksum
        checksum = checksum_calc(tx_buf)
        tx_buf.append(checksum)
        dl_uart_write(uart_port, tx_buf)

    #handle response
    return dl_uart_read_resp(uart_port)



# CMD 2: CHECK BLANKING
def dl_bld_blanking(uart_port: serial.Serial, fl_adr, size) -> bool:
    """
    Check blanking of memory range based on starting address and memory length

    Notes: Data sent including:
        1 len byte = 11
        1 cmd byte
        4 address bytes
        4 memory size bytes
        1 checksum byte

    Args:
        uart_port (serial.Serial): The COM port object used for communication.
        s_adr (int/str): Start address of the memory range that to be checked
        size (int/str): Size of data to be checked

    Returns:
        bool: True if memory range is clean. False if it is dirty.
    """
    tx_buf = []  # buffer to store transmit data

    print("====================")
    print("start adr: ", fl_adr)
    print("len: ", size)
    print("====================")

    # send first byte command
    tx_buf.append(11)  # length of data to be sent
    tx_buf.append(RqCmd.RQ_CHECK_BLANKING)

    if type(fl_adr) == str:
        # send start address of memory
        for i in range(4):
            tx_buf.append(int(fl_adr[i * 2:i * 2 + 2], base=16))
        # send size of memory range that want to be erased
        for i in range(4):
            tx_buf.append(int(size[i * 2:i * 2 + 2], base=16))

        checksum = checksum_calc(tx_buf)
        tx_buf.append(checksum)
        dl_uart_write(uart_port, tx_buf)

    elif type(fl_adr) == int:
        for i in range(4):
            tx_buf.append((fl_adr >> (24 - i * 8)) & 0xFF)
        for i in range(4):
            tx_buf.append((size >> (24 - i * 8)) & 0xFF)

        # send checksum
        checksum = checksum_calc(tx_buf)
        tx_buf.append(checksum)
        dl_uart_write(uart_port, tx_buf)

    time.sleep(0.01)
    # handle response
    resp = dl_uart_read_resp(uart_port)
    return resp[0]


# CMD 4: GET BOOTLOADER VERSION
def dl_bld_get_version(uart_port: serial.Serial,
                       num_byte: int = 1) -> bytearray:
    """
    Read response from MCU based on defined number of byte wants to be read..
    
    Notes: Data sent including:
        1 len byte = 3
        1 cmd byte
        1 checksum byte
    """
    tx_buf = []
    rx_buf: bytes
    tx_buf.append(3)
    tx_buf.append(RqCmd.RQ_GET_BLD_VER)
    tx_buf.append(checksum_calc(tx_buf))

    dl_uart_write(uart_port, tx_buf)

    time.sleep(0.01)
    # handle response
    return dl_uart_read_resp(uart_port)

