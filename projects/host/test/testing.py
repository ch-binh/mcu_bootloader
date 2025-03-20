START_ADR = "00002000"
END_ADR = "00002400"
SECTOR_SIZE = 1024
erase_len = int(END_ADR[:8], base=16) - int(START_ADR[:8], base=16)
erase_len = int((erase_len + SECTOR_SIZE - 1) / SECTOR_SIZE)*SECTOR_SIZE

print(erase_len)