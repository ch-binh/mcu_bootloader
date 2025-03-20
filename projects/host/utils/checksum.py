def calc_checksum(data: list):
    """
    Calculate checksum for data string that contains 1 byte per element
    """
    total_checksum = 0

    
    
    for e in data:
        if isinstance(e, int):
            total_checksum += e
        else:
            print("debug here")

    # %256 for return to 0 if reach 256
    calc_checksum = (256-total_checksum % 256) % 256
    return calc_checksum


