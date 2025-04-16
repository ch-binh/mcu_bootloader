import sys
import os
import serial.tools.list_ports

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "utils")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "common")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "driverlib")))

from driverlib.dl_uart import Uart
from driverlib.dl_hexf import *
from driverlib.dl_bld import *
from common.memory_map import *



#===========================================================================
#                                 MAIN
#===========================================================================
@staticmethod
def uart_port_init() -> None:
    Uart.scan_com_ports()
    Uart.input_set_com_port()
    Uart.cfg_port(Uart.target_com_port)
    Uart.init()
    
def uart_port_deinit() -> None:
    Uart.deinit()

def main() -> None:
    """Select a control command to execute."""
    print("=" * 40)
    print("2. Select commands")
    print("-" * 40)

    cmd_tb = [
        ("Enter Bootloader", lambda: print("TODO: Enter Bootloader")),
        ("Get Bootloader version", lambda: cmd_get_bld_version_cb()),
        ("Check Blanking", lambda: cmd_check_blanking_cb()),
        ("Write", lambda: cmd_write()),
        ("Erase", lambda: cmd_erase()),
        ("Upload file", lambda: cmd_upload_file()),
        ("Check CRC", lambda: cmd_check_crc()),
        ("System reset", lambda: print("No Operation (NOP)")),
        ("Exit Bootloader", lambda: cmd_hexf_to_binf()),
        ("Convert hex file to bin file", lambda: cmd_hexf_to_binf()),
    ]

    print("\nAvailable commands:")
    for idx, (desc, _) in enumerate(cmd_tb):
        print(f"{idx}. {desc}")
    print('Returning: write "r" to return')

    choice = input("Choosing mode: ").strip()
    if choice.lower() == 'r':
        exit()
    if choice.isdigit():
        idx = int(choice)
        
        uart_port_init()
        if 0 <= idx < len(cmd_tb):
            cmd_tb[idx][1]()  # Call the function
        else:
            print("Invalid choice.")
        uart_port_deinit()
        
        
    else:
        print("Invalid input.")


#===========================================================================
# BOOTLOADER COMMANDS FUCNTIONS
#===========================================================================


@staticmethod
def cmd_get_bld_version_cb():
    print("Bootloader version is:", dl_bld_get_version(Uart.inst))


@staticmethod
def cmd_check_blanking_cb():
    addr = 0x1800
    size = 0x400
    print(f"Image from {addr} with size of {size}\
        is {'clean' if dl_bld_blanking(Uart.inst, addr, size, 1) else 'not blank'}"
          )


@staticmethod
def cmd_write():
    addr = 0x1800
    data = [
        0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C,
        0x0D, 0x0E, 0x0F
    ]
    if dl_bld_write(Uart.inst, addr, data, 1):
        print("Write success")
    else:
        print("Write failed")


@staticmethod
def cmd_erase():
    addr = 0x1800
    size = 0x400
    if dl_bld_erase(Uart.inst, addr, size, 1):
        print("Erase success")
    else:
        print("Erase failed")


@staticmethod
def cmd_upload_file():
    if dl_bld_upload(Uart.inst):
        print("Upload success")
    else:
        print("Upload failed")


@staticmethod
def cmd_check_crc():
    addr = 0x1800
    size = 0x400
    data = input("Input some data here: ")
    if dl_bld_check_img_crc(Uart.inst, addr, size, data):
        print("CRC check success")
    else:
        print("CRC check failed")


#===========================================================================
# UTILITIES COMMANDS FUCNTIONS
#===========================================================================

@staticmethod
def cmd_hexf_to_binf(fname):
    # select hex file
    FileInfo.scan_files(get_hexf=True)
    FileInfo.select_files()

    fname = input("Input file name: ")

    if FileInfo.fpath.endswith(".hex"):
        dl_hexf_to_binf(fpath=FileInfo.fpath, ouputf_name=fname + ".bin")


#===========================================================================
#                                 MAIN
#===========================================================================

if __name__ == "__main__":
    while (1):
        main()
