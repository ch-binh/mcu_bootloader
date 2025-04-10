import serial
import os

from common.ret_no import ERRNO
from utils.checksum import checksum_calc

IMAGE_TAG = 0xD1B45E82
IMAGE_START = 0x00002000
IMAGE_SIZE = 0x0000068A
IMAGE_CRC = 0x1C18B4D5
IMAGE_JUMP_ADDR = 0x00002000

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


class RqCmd():
    """
    Contains the request commands
    """
    RQ_NOP = 0x00
    RQ_ERASE = 0x01
    RQ_CHECK_BLANKING = 0x02
    RQ_UPLOADING = 0x03
    RQ_CHECK_CRC_MODE = 0x04
    RQ_SYSTEM_RESET = 0x05
    RQ_GET_BLD_VER = 0x06
    RQ_ENTER_BLD = 0x07
    RQ_EXIT_BLD = 0x08


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


def is_sent_success(uart_port) -> bool:
    """
    Check if the transmission was successful by reading the MCU's response.

    Args:
        COM (object): The COM port object used for communication.

    Returns:
        bool: True if the response indicates success, False otherwise.
    """
    global error_count
    read_success_flag = 0

    msp_res = ''
    try:
        if read_success_flag != 1:
            # waiting for data to come
            timeout_counter = 0
            while not uart_port.in_waiting:
                # if dont have data to read yet, set timeout
                timeout_counter += 1
                if timeout_counter >= 1500000:
                    print("Reading UART timeout. Exiting...")
                    exit()

            msp_res = uart_port.read(uart_port.in_waiting)

            if len(msp_res) == 1:
                msp_res = ord(msp_res)
            else:
                msp_res = ord(chr(msp_res[len(msp_res) - 1]))

        else:
            return True

    except ValueError:
        ticks = 0
        while (ticks < READ_RES_SPEED):
            ticks += 1
        # if read catch NULL, try read again, if fail return fail values
        if is_sent_success(uart_port):
            read_success_flag = 1  # return to main app right away
            return True
        else:
            return False

    else:
        match msp_res:
            case Res_cmd.RES_DOWNLOAD_INPROG:
                print(f"Response: please wait: {msp_res}")
                # response indicates please wait, add ticks

                while not is_sent_success(uart_port):
                    print("res code = 3 -> Waiting")

                return True

            case Res_cmd.RES_WRITE_DATA_FAIL:
                print(
                    f"Response: fail: {msp_res}. Re-send data, tries: {error_count}"
                )
                error_count += 1
                if error_count == NUMBER_OF_ATTEMPTS:
                    print("Exceed number of attempts")
                    exit()
                return False

            case Res_cmd.RES_WRITE_DATA_SUCCESS:
                error_count = 0
                return True

            case Res_cmd.RES_CRC_SUCCESS:
                error_count = 0
                print("Response: CRC success")
                return True

            case Res_cmd.RES_CRC_FAIL:
                print("Response: CRC Fail!!!")
                return False

            case Res_cmd.RES_ERASE_COMPLETE:
                error_count = 0
                print("Response: Erase complete")
                return True

            case Res_cmd.RES_APP_FLASH_CLEAN:
                error_count = 0
                print("Response: Memory is clean")
                return True

            case Res_cmd.RES_APP_FLASH_DIRTY:
                print("Response: Memory is NOT erased")
                return False

            case Res_cmd.RES_ENTER_BLD_SUCCESS:
                print("Response: Enter Bootloader success")
                return True

            case Res_cmd.RES_ENTER_BLD_FAIL:
                print("Response: Enter Bootloader fail")
                return False

            case Res_cmd.RES_EXIT_BLD_SUCCESS:
                print("Response: Exit Bootloader success")
                return True

            case Res_cmd.RES_EXIT_BLD_FAIL:
                print("Response: Exit Bootloader fail")
                return False

            case _:
                print("Response: Receive unknown response: ", msp_res)
                error_count += 1
                if error_count == NUMBER_OF_ATTEMPTS:
                    print("Reach maximum number of retries. Exiting...")
                    exit()


def send_crc_cmd(uart_port, s_adr, size, crc: int) -> None:
    """
    Check crc of memory range based on starting address and memory length

    Notes: Data sent including:
        1 cmd byte
        4 address bytes
        4 memory size bytes
        4 crc bytes (crc32)
        1checksum byte

    Args:
        COM (object): The COM port object used for communication.
        s_adr (int/str): Start address of the memory range that to be checked
        size (int/str): Size of data to be checked
        crc (int): Crc value to be checked
    """
    # send commmand
    dl_uart_write(uart_port, RqCmd.RQ_CHECK_CRC_MODE)

    # prepare to send data
    if type(s_adr) == str:
        # send start address of memory
        for i in range(4):
            dl_uart_write(uart_port, int(s_adr[i * 2:i * 2 + 2], base=16))
        # send size of memory range that want to be erased
        for i in range(4):
            dl_uart_write(uart_port, int(size[i * 2:i * 2 + 2], base=16))
        for i in range(4):
            dl_uart_write(uart_port, int(crc[i * 2:i * 2 + 2], base=16))

        # send checksum
        data_str = s_adr + size + crc
        checksum = calculate_checksum_2byte(data_str)
        dl_uart_write(uart_port, checksum)

    # send size of memory range that want to be check
    if type(s_adr) == int:
        adr_list = [None] * 4
        size_list = [None] * 4
        crc_list = [None] * 4

        # convert from int to int list
        adr_list[0] = s_adr >> 24
        adr_list[1] = s_adr >> 16 & 0xFF
        adr_list[2] = s_adr >> 8 & 0xFF
        adr_list[3] = s_adr & 0xFF

        size_list[0] = size >> 24
        size_list[1] = size >> 16 & 0xFF
        size_list[2] = size >> 8 & 0xFF
        size_list[3] = size & 0xFF

        crc_list[0] = crc >> 24
        crc_list[1] = crc >> 16 & 0xFF
        crc_list[2] = crc >> 8 & 0xFF
        crc_list[3] = crc & 0xFF

        # send byte element in list
        for e in adr_list:
            dl_uart_write(uart_port, e)
        for e in size_list:
            dl_uart_write(uart_port, e)
        for e in crc_list:
            dl_uart_write(uart_port, e)

        # calculate checksum
        data_str = []
        for i in range(4):
            data_str.append(str(adr_list[i]))
        for i in range(4):
            data_str.append(str(size_list[i]))
        for i in range(4):
            data_str.append(str(crc_list[i]))

        checksum = checksum_calc(data_str)
        dl_uart_write(uart_port, checksum)


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



def delay_tick(time: int) -> None:
    """
    Simple delay function that simulates a delay for a specified number of ticks.

    Args:
        time (int): The number of ticks to delay.
    """
    tick = 0
    while (tick <= time):
        tick += 1


def dl_uart_read_resp(uart_port: serial.Serial) -> bytearray:
    try:
        rx_buf = uart_port.read(uart_port.in_waiting)
    except ValueError:
        print("catch value error")

    if dl_uart_check_rx_buf_intergity(rx_buf):
        return rx_buf[1:len(rx_buf) - 1]

    return None

@staticmethod
def dl_uart_check_rx_buf_intergity(rx_buf: bytearray) -> bool:
    """
    Check the integrity of the received buffer by verifying its length and checksum.

    Args:
        rx_buf (bytearray): The received buffer.

    Returns:
        bool: True if the buffer length is valid, False otherwise.
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
