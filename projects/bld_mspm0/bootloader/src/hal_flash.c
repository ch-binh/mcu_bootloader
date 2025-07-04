#include "ti/driverlib/dl_flashctl.h"

#include "inc/hal_flash.h"
#include "inc/sysmem_map.h"

/**
 *  BASIC OPERATIONS
 *===================================================================
 */

int hal_flash_write_mem_32(uint32_t start_addr, const uint32_t *data) {
  int ret = -1;
  DL_FlashCTL_executeClearStatus(FLASHCTL);
  DL_FlashCTL_unprotectSector(FLASHCTL, start_addr,
                              DL_FLASHCTL_REGION_SELECT_MAIN);
  ret = DL_FlashCTL_programMemoryFromRAM32(FLASHCTL, start_addr, data);
  return ret;
}

int hal_flash_write_mem_64(uint32_t start_addr, const uint32_t *data) {
  int ret = -1;
  DL_FlashCTL_executeClearStatus(FLASHCTL);
  DL_FlashCTL_unprotectSector(FLASHCTL, start_addr,
                              DL_FLASHCTL_REGION_SELECT_MAIN);
  ret = DL_FlashCTL_programMemoryFromRAM64(FLASHCTL, start_addr, data);
  return ret;
}

int hal_flash_read_mem(uint32_t *buf, uint32_t start_addr, uint8_t size) {
  uint32_t *p32 = (uint32_t *)(start_addr);
  for (int i = 0; i < size; i++) {
    buf[i] = p32[i];
  }
  return 0;
}

int hal_flash_erase_mem(uint32_t start_addr, uint32_t size) {

  // todo: enter crit section
  /* Erase sector by sector, 1 sector = 0x400 bytes for mspm0c1104*/
  for (uint32_t addr = start_addr; addr < start_addr + size;
       addr += SECTOR_SIZE) {
    DL_FlashCTL_executeClearStatus(FLASHCTL);
    DL_FlashCTL_unprotectSector(FLASHCTL, addr, DL_FLASHCTL_REGION_SELECT_MAIN);
    DL_FlashCTL_eraseMemory(FLASHCTL, addr, DL_FLASHCTL_COMMAND_SIZE_SECTOR);
  }

  return 0;
}

/**
 *  APPLICATION OPERATIONS
 *===================================================================
 */

/**
 *  @brief Because the address must be of 64-bit, align with 0x00
 *  This function is a workaround to that matter, allows the address
 *  to be of 32-bit
 *  @Note: this is why we have to use a word:
 *  param[in]  address    Destination memory address to program data. The
 *                         address must be flash word (64-bit) aligned i.e.
 *                         aligned to a 0b000 boundary.
 */
int hal_flash_write_mem_32bit(uint32_t start_addr, uint32_t data) {
  int ret = 0;

  uint32_t data_32[] = {data};
  uint32_t data_64[] = {MEM_BLANK_32BIT, data};

  if (((start_addr - FLASH_SYSTEM_INFO_START) % 8) == 0) {
    ret = hal_flash_write_mem_32(start_addr, data_32);
  } else {
    ret = hal_flash_write_mem_64(start_addr, data_64);
  }
  return ret;
}

/**
 *
 */
bool hal_flash_check_blanking(uint32_t start_addr, uint32_t size) {
  uint32_t *p32 = (uint32_t *)(start_addr);
  for (int i = 0; i < (size >> 2); i++) {
    if (p32[i] != MEM_BLANK_32BIT) {
      return false;
    }
  }
  return true;
}
