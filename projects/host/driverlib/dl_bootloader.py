from dl_uart import *
from utils.checksum import *
### Package info
### SIZE [1 Byte] | DATA n... | CHECKSUM | END BYTE
###


def dl_bld_get_version(uart_port, num_byte: int = 1) -> bytearray:
    """
    Read response from MCU based on defined number of byte wants to be read..
    """

    data = [1, RqCmd.RQ_GET_BLD_VER]
    data.append(calc_checksum(data))
    data.append("\n")
    
    dl_uart_write(uart_port, data)

    time.sleep(0.01)
    try:
        return uart_port.read(num_byte.in_waiting)

    except ValueError:
        print("catch value error")
