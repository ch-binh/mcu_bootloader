def checksum_calc(data: list) -> int:
    """
    Calculate checksum for data string that contains 1 byte per element
    """
    total_checksum = 0

    for e in data:
        if isinstance(e, int):
            total_checksum += e
        else:
            print("debug here")

    return (256 - total_checksum % 256) % 256
