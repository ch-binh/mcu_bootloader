import sys
import os
import serial.tools.list_ports

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "utils")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "common")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "driverlib")))

from driverlib.dl_uart import *
from driverlib.dl_hexf import *
from driverlib.dl_bld import *
from common.memory_map import *

### Global variable
gUart = None


class SystemInfo:
    com_ports = []
    target_com_port = ""
    


    #============================Selecting COM Ports================================#
    @classmethod
    def scan_com_ports(cls):
        """Lists all available COM ports with details."""
        print("=" * 40)
        print("1. Listing all avaialble COM")
        print("-" * 40)
        cls.com_ports = serial.tools.list_ports.comports()

        if not cls.com_ports:
            print("No COM ports found.")
        else:
            for idx, port in enumerate(cls.com_ports, start=0):
                print(f"{idx}. Port: {port.device} : {port.description}")
                print("-" * 40)  # Separator line

    @classmethod
    def input_set_com_port(cls):
        print("-" * 40)
        print("--- Select the COM port ---")
        print("Instruction: type \"1\" to select COM no.1")

        idx = int(input("Input number: "))

        cls.target_com_port = cls.com_ports[idx].device
        print(f"\nSelect \"{cls.target_com_port}\"\n")




#===========================================================================
#                                 MAIN
#===========================================================================
@staticmethod
def set_sys_info() -> None:
    global gUart
    SystemInfo.scan_com_ports()
    SystemInfo.input_set_com_port()
    Uart.cfg_port(SystemInfo.target_com_port)


    gUart = dl_uart_init()


def main() -> None:
    """Select a control command to execute."""
    print("=" * 40)
    print("2. Select commands")
    print("-" * 40)

    cmd_options = {
        "1": lambda: print("No Operation (NOP)"),
        "2": lambda: cmd_get_bld_version_cb(gUart),
        "3": lambda: cmd_check_blanking_cb(gUart),
        "4": lambda: cmd_write(gUart),
        "5": lambda: cmd_erase(gUart),
        "6": lambda: cmd_upload_file(gUart),
        "7": lambda: cmd_check_crc(gUart),
        "8": lambda: print("No Operation (NOP)"),
        "9": lambda: cmd_exit_bld(gUart),
    }

    cmd_mode = input("0. No Operation (NOP)"
                     "\n1. Enter Bootloader"
                     "\n2. Get Bootloader version"
                     "\n3. Check Blanking"
                     "\n4. Write"
                     "\n5. Erase"
                     "\n6. Upload file"
                     "\n7. Check CRC"
                     "\n8. System reset"
                     "\n9. Exit Bootloader"
                     "\nReturning: write \"r\" to return"
                     "\nChoosing mode: ").strip()

    if cmd_mode == "r":
        exit()
    if cmd_mode in cmd_options:
        cmd_options[cmd_mode]()
    else:
        print("Unknown command, please try again.")


#===========================================================================
#   COMMANDS FUCNTIONS
#===========================================================================


@staticmethod
def cmd_get_bld_version_cb(uart_port: serial.Serial):
    print("Bootloader version is:", dl_bld_get_version(uart_port))


@staticmethod
def cmd_check_blanking_cb(uart_port: serial.Serial):
    addr = 0x1800
    size = 0x400
    print(f"Image from {addr} with size of {size}\
        is {'clean' if dl_bld_blanking(uart_port, addr, size, 1) else 'not blank'}"
          )


@staticmethod
def cmd_write(uart_port: serial.Serial):
    addr = 0x1800
    data = [
        0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C,
        0x0D, 0x0E, 0x0F
    ]
    if dl_bld_write(uart_port, addr, data, 1):
        print("Write success")
    else:
        print("Write failed")


@staticmethod
def cmd_erase(uart_port: serial.Serial):
    addr = 0x1800
    size = 0x400
    if dl_bld_erase(uart_port, addr, size, 1):
        print("Erase success")
    else:
        print("Erase failed")


@staticmethod
def cmd_upload_file(uart_port: serial.Serial):
    
        
    if dl_bld_upload_file(uart_port):
        print("Upload success")
    else:
        print("Upload failed")


@staticmethod
def cmd_check_crc(uart_port: serial.Serial):
    addr = 0x1800
    size = 0x400
    data = input("Input some data here: ")
    if dl_bld_check_img_crc(uart_port, addr, size, data):
        print("CRC check success")
    else:
        print("CRC check failed")
        
        
@staticmethod
def cmd_exit_bld(uart_port: serial.Serial):
    if dl_bld_exit(uart_port):
        print("Exiting bootloader, enterring Application...")
        exit()


#===========================================================================
#                                 MAIN
#===========================================================================

if __name__ == "__main__":
    set_sys_info()
    while (1):
        main()
