
class ERRNO:
    CRC_PASS = 1
    CRC_FAIL = -1
    SUCCESS = 0  # Successful operation
    ERR = -2  # General error
    ERR_FNF = -1  # File not found
    ERR_INVALID = -3  # Invalid value
    ERR_INVALID_PORT = -4  # Invalid port
    ERR_INVALID_DATATYPE = -5  # Invalid data type