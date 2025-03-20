
import sys
import os
import serial.tools.list_ports

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "utils")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "common")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "driverlib")))

from driverlib.dl_uart import *
from driverlib.dl_hex_file import *
from driverlib.dl_bootloader import *
from common.memory_map import *

### Global variable
gUart = None

class SystemInfo:
    com_ports = []
    hex_files = []

    target_com_port = ""
    target_hex_file_addr = ""

    target_release_dir = "../../Release"

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
        

    #============================Selecting Hex Files================================#
    @classmethod
    def scan_hex_files(cls):
        """Scans for .hex files in the specified directory."""

        print("=" * 40)
        print("2. Listing all available hex files")
        print("-" * 40 + "\n")
        if not os.path.exists(cls.target_release_dir):
            print(
                f"Error: Directory '{cls.target_release_dir}' does not exist.")
            return None

        cls.hex_files = [
            f for f in os.listdir(cls.target_release_dir) if f.endswith(".hex")
        ]

        if not cls.hex_files:
            print("No .hex files found in", cls.target_release_dir)
            return None

        print(f"Found .hex files in \"{cls.target_release_dir}\":")
        for idx, file in enumerate(cls.hex_files, start=0):
            print(f"{idx}. {file}")

    @classmethod
    def input_set_hex_file(cls):
        print("--- Select the hex file ---")
        print("Instruction: type \"1\" to select hex file no.1")

        idx = int(input("Input number: "))
        cls.target_hex_file_addr = os.path.abspath(
            f"{cls.target_release_dir}/{cls.hex_files[idx]}")

        print(f"\nSelect \"{cls.target_release_dir}/{cls.hex_files[idx]}\"\n")


#============================Main================================#
@staticmethod
def set_sys_info() -> None:
    global gUart
    SystemInfo.scan_com_ports()
    SystemInfo.input_set_com_port()
    Uart.cfg_port(SystemInfo.target_com_port)
    
    SystemInfo.scan_hex_files()
    SystemInfo.input_set_hex_file()
    Uart.cfg_port(SystemInfo.target_hex_file_addr)
    
    gUart = dl_uart_init()


def main() -> None:
    """Select a control command to execute."""
    print("=" * 40)
    print("2. Select commands")
    print("-" * 40 + "\n")
    
    

    cmd_options = {
        "1":
        lambda:
        (print("Flash erase success")
         if send_erase_cmd(UART_PORT, FLASH_APP_START, FLASH_APP_SIZE) else
         (print("Fail to erase"), exit())),
        "2":
        lambda: dl_uart_check_blanking(0x0000, 0x400),
        "3":
        lambda: dl_uart_write(UART_PORT, RqCmd.RQ_SYSTEM_RESET),
        "4":
        lambda: print("Bootloader version is:", dl_bld_get_version(gUart)),
        "5":
        lambda: read_enter_bld_response(UART_PORT)
        if send_enter_bld_cmd(UART_PORT) else None,
        "6":
        lambda: read_exit_bld_response(UART_PORT)
        if send_exit_bld_cmd(UART_PORT) else None,
    }

    cmd_mode = input("\n0. Download"
                     "\n1. Erase"
                     "\n2. Check Blanking"
                     "\n3. System reset"
                     "\n4. Get Bootloader version"
                     "\n5. Enter Bootloader"
                     "\n6. Exit Bootloader"
                     "\nReturning: write \"r\" to return"
                     "\nChoosing mode: ").strip()

    if cmd_mode == "r":
        exit()
    if cmd_mode in cmd_options:
        cmd_options[cmd_mode]()
    else:
        print("Unknown command, please try again.")
        exit()


if __name__ == "__main__":
    set_sys_info()
    while(1):
        main()
