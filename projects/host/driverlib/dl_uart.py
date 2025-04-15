import serial
import os
import time

from common.ret_no import ERRNO
from utils.checksum import checksum_calc



RQ_KEY = 0x84AE9B23
RES_KEY = 0x18E2B8AC

NUMBER_OF_ATTEMPTS = 20  # number of resend attempt if respond returns fail
DOWNLOADING_SPEED = 7500  # test successful with 5000, x2 -> 10000 just to be safe
READ_RES_SPEED = 10000
WAIT_FOR_RES = 50000  # make it large for flash downloading and verifying

BUADRATE_LIST = [
    110, 300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400,
    460800, 921600, 1000000, 1500000, 2000000, 2500000, 3000000, 3500000,
    4000000
]

# 🔹 Global Configuration Variables


class Uart:
    ###### SET Functions ######
    uart_port = "/dev/ttyUSB0"
    baudrate = 115200
    file_addr = "../../bin/uart.bin"

    @classmethod
    def cfg_port(cls, value):
        """Set the UART port."""
        if not isinstance(value, str) or not (value.startswith("/dev/")
                                              or value.startswith("COM")):
            return ERRNO.ERR_INVALID
        cls.uart_port = value
        return ERRNO.SUCCESS

    @classmethod
    def cfg_baudrate(cls, value):
        """Set the UART baudrate."""

        if value not in BUADRATE_LIST:
            cls.baudrate = 115200  # Reset to default
            return ERRNO.ERR_INVALID
        cls.baudrate = value
        return ERRNO.SUCCESS

    @classmethod
    def cfg_file_addr(cls, address):
        """Set the binary file address."""
        if not isinstance(address, str) or not os.path.exists(address):
            return ERRNO.ERR_FNF
        cls.file_addr = address
        return ERRNO.SUCCESS


error_count = 0


class Res_cmd():
    """
    Contains the respond signal
    """
    RES_EXIT_BLD_SUCCESS = ord('c')
    RES_EXIT_BLD_FAIL = ord('d')
    RES_ENTER_BLD_SUCCESS = ord('a')
    RES_ENTER_BLD_FAIL = ord('b')
    RES_ERASE_COMPLETE = ord('8')  # Erase memory success
    RES_CRC_FAIL = ord('7')  # Check crc fail
    RES_CRC_SUCCESS = ord('6')  # download image success
    RES_WRITE_DATA_SUCCESS = ord('5')  # download line success
    RES_WRITE_DATA_FAIL = ord('4')  # download line fail - Ask for line again
    RES_DOWNLOAD_INPROG = ord('3')  # downloading in progress - Ask to wait
    RES_APP_FLASH_CLEAN = ord('2')  # main application flash is clean
    RES_APP_FLASH_DIRTY = ord('1')  # main application flash is dirty


def dl_uart_init() -> serial.Serial:
    """Open the UART port."""
    uart_inst = None
    uart_inst = serial.Serial(port=Uart.uart_port,
                              baudrate=Uart.baudrate,
                              timeout=1)
    if uart_inst.is_open:
        print(f"Port {Uart.uart_port} opened successfully.")
        return uart_inst
    else:
        print(f"Failed to open port {Uart.uart_port}.")
        return None


def dl_uart_deinit(cls):
    """Close the UART port."""
    try:
        if hasattr(cls, 'serial_inst') and cls.serial_inst.is_open:
            cls.serial_inst.close()
            print(f"Port {cls.uart_port} closed successfully.")
            return ERRNO.SUCCESS
        else:
            print(f"Port {cls.uart_port} is not open.")
            return ERRNO.ERR_CLOSE
    except serial.SerialException as e:
        print(f"Error closing port {cls.uart_port}: {e}")
        return ERRNO.ERR_CLOSE


####### Utility functions ######
def dl_uart_write(uart_port: serial.Serial, data: list) -> None:
    """
    Send data to the specified COM port and introduce a delay.

    Args:
        COM (object): The COM port object used for communication.
        data_to_send (int): The data byte to be sent to the COM port.
    """
    for byte in data:
        if isinstance(byte, int):
            uart_port.write(bytes([byte]))
        elif isinstance(byte, str):
            uart_port.write(byte.encode())
        else:
            uart_port.write(bytes([byte]))



def send_enter_bld_cmd(uart_port, rq_key: int = RQ_KEY) -> None:
    """
    Send enter bootloader flag

    Notes: Data sent including:
        1 cmd byte
        4 request key bytes
        1checksum byte

    Args:
        COM (object): The COM port object used for communication.
        rq_key (int): Request key
    """
    dl_uart_write(uart_port, RqCmd.RQ_ENTER_BLD)

    # convert from int to int list
    if type(rq_key == int):
        rq_key_list = [None] * 4

        rq_key_list[0] = rq_key >> 24
        rq_key_list[1] = rq_key >> 16 & 0xFF
        rq_key_list[2] = rq_key >> 8 & 0xFF
        rq_key_list[3] = rq_key & 0xFF

        # send key bytes
        for e in rq_key_list:
            dl_uart_write(uart_port, e)

    # calculate checksum
    data_str = []
    for i in range(4):
        data_str.append(str(rq_key_list[i]))

    # Send checksum
    checksum = checksum_calc(data_str)
    dl_uart_write(uart_port, checksum)


def read_enter_bld_response(uart_port):
    """
    Read response after sending enter bootloader command

    Returns:
        bool: True if enter successful, False otherwise
    """
    if is_sent_success(uart_port):
        return True
    else:  # False = checksum fail
        send_enter_bld_cmd(uart_port)
        # resend the command
        num_try = 0
        while (True):
            if (is_sent_success(uart_port)):
                return True
            else:
                print(f"Enter failed, resend. Try: {num_try}")
                send_enter_bld_cmd(uart_port)
                num_try += 1
                if num_try == 3:
                    return False


def send_exit_bld_cmd(uart_port, res_key: int = RES_KEY) -> None:
    """
    Send exit bootloader flag

    Notes: Data sent including:
        1 cmd byte
        4 response key bytes
        1checksum byte

    Args:
        COM (object): The COM port object used for communication.
        response_key (int): response key
    """
    # send first byte command
    dl_uart_write(uart_port, RqCmd.RQ_EXIT_BLD)

    # convert from int to int list
    if type(res_key == int):
        res_key_list = [None] * 4

        res_key_list[0] = res_key >> 24
        res_key_list[1] = res_key >> 16 & 0xFF
        res_key_list[2] = res_key >> 8 & 0xFF
        res_key_list[3] = res_key & 0xFF

        # send key bytes
        for e in res_key_list:
            dl_uart_write(uart_port, e)

    # calculate checksum
    data_str = []
    for i in range(4):
        data_str.append(str(res_key_list[i]))

    # Send checksum
    checksum = checksum_calc(data_str)
    dl_uart_write(uart_port, checksum)


def read_exit_bld_response(uart_port) -> bool:
    """
    Read response after sending exit bootloader command

    Returns:
        bool: True if exit successful, False otherwise
    """
    if is_sent_success(uart_port):
        return True
    else:  # False = checksum fail
        # resend the command
        send_exit_bld_cmd(uart_port)
        num_try = 0
        while (True):
            if (is_sent_success(uart_port)):
                return True
            else:
                print(f"Enter failed, resend. Try: {num_try}")
                send_exit_bld_cmd(uart_port)
                num_try += 1
                if num_try == 3:
                    return False


def dl_uart_read_resp(uart_port: serial.Serial) -> bytearray:
    # Scan UART buffer for incoming data
    time_out = 0
    while not uart_port.in_waiting:
        time.sleep(0.01)
        time_out += 1
        if time_out == 100:
            print("timeout")
            return 0

    # if catched data
    try:
        rx_buf = uart_port.read(uart_port.in_waiting)
    except ValueError:
        print("catch value error")

    # check data integrity and return if data is valid
    if dl_uart_check_rx_buf_integrity(rx_buf):
        return rx_buf[1:len(rx_buf) - 1]

    return 0


@staticmethod
def dl_uart_check_rx_buf_integrity(rx_buf: bytearray) -> bool:
    """
    Check the integrity of the received buffer by verifying its length and checksum.
    """

    # Check if the buffer is empty or too short
    if len(rx_buf) != rx_buf[0]:
        print("Error: Received buffer is empty or too short.")
        return False

    # Check CRC
    if rx_buf[-1] != checksum_calc(rx_buf[:-1]):
        print("Error: Checksum mismatch.")
        return False

    return True
