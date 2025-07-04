#ifndef HAL_FLASH_H
#define HAL_FLASH_H

#include "ti_msp_dl_config.h"
#include <stdint.h>

/**
 *  DEFINE
 *===================================================================
 */

#define MEM_BLANK_32BIT (0xFFFFFFFF)

/**
 *  VARIALES
 *===================================================================
 */

/**
 *  BASIC OPERATIONS
 *===================================================================
 */

int hal_flash_write_mem_32(uint32_t start_addr, const uint32_t *data);
int hal_flash_write_mem_64(uint32_t start_addr, const uint32_t *data);
int hal_flash_read_mem(uint32_t *buf, uint32_t start_addr, uint8_t size);
int hal_flash_erase_mem(uint32_t start_addr, uint32_t size);

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
int hal_flash_write_mem_32bit(uint32_t start_addr, uint32_t data);

bool hal_flash_check_blanking(uint32_t start_addr, uint32_t size);


#endif // HAL_FLASH_H