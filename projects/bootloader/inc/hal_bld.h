#ifndef HAL_BLD_H
#define HAL_BLD_H

#include "bootloader.h"
#include <stdint.h>


/**
 *  VARIABLES AND DEFINES
 *===================================================================
 */

#define REQ_ACK 0x01


typedef enum {
    CMD_NOP,
    CMD_ENTER_BLD,
    CMD_GET_BLD_VER,
    CMD_CHECK_BLANKING,
    CMD_WRITE,
    CMD_WRITE_CRC,
    CMD_ERASE,
    CMD_UPLOADING,
    CMD_IMAGE_CRC_VERIFY,
    CMD_SYSRST,
    CMD_EXIT_BLD,
    CMD_NUM,
    CMD_UNDEFINED = 0xFF
} bld_cmd_e;

/**
 *  SETUPS
 *===================================================================
 */

/**
 *  APPLICATION FUNCTIONS
 *===================================================================
 */
int hal_bld_verify_app_mem(uint32_t start_adr);
void hal_bld_go_to_main_app(uint32_t jump_addr);

#endif // HAL_BLD_H