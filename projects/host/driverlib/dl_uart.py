import serial
import os
import time

from common.ret_no import ERRNO
from utils.checksum import checksum_calc

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


def dl_uart_read_resp(uart_port: serial.Serial) -> bytearray:
    """
    This function reads rx buffer, including verifying len and checksum
    
    Return:
        if data is available, return from bit 1 to n-1 (excluding length and checksum)
        else return [0]
    """
    # Scan UART buffer for incoming data
    time_out = 0
    while not uart_port.in_waiting:
        time.sleep(0.001) # as tested, 0.001 is min
        time_out += 1
        if time_out == 1000:
            print("timeout")
            return [0]

    # if catched data
    try:
        rx_buf = uart_port.read(uart_port.in_waiting)
    except ValueError:
        print("catch value error")

    # check data integrity and return if data is valid
    if dl_uart_check_rx_buf_integrity(rx_buf):
        return rx_buf[1:len(rx_buf) - 1]

    return [0]


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
