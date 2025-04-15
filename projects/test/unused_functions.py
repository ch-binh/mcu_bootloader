def str_to_byte_list(string: str):
    """
    Convert a string of hexadecimal values into a list of 16-bit integers in big-endian format.

    Args:
        string (str): A string containing hexadecimal values where each four characters 
                      represent a 16-bit value (e.g., "0A0B" for two bytes).

    Returns:
        list[int]: A list of 16-bit integers where each group of four hexadecimal characters 
                   is combined into a 16-bit value in big-endian format.
                   For example, "0A0B0C0D" becomes [0x0A0B, 0x0C0D].
    """
    counter = 0
    byte_list = []
    for i in range(int(len(string)/4)):
        byte_list.append(i)
        byte_list[i] = int(string[counter:counter+2], base=16)
        byte_list[i] = byte_list[i]*0x100 + \
            int(string[counter+2:counter+4], base=16)
        counter += 4

    return byte_list