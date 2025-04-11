#ifndef BOOTLOADER_H
#define BOOTLOADER_H


#include "ti_msp_dl_config.h"
#include "inc/sysmem_map.h"
#include "utils/checksum.h"

/**
 *  VARIABLES AND DEFINE
 *===================================================================
 */
#define DELAY (12000000)

#define BLD_VER_MAJOR '0'
#define BLD_VER_RESERVE '.'
#define BLD_VER_MINOR '1'
#define BLD_VER_PATCH 'A'
#define BLD_VER_LEN 4

#define NUM_VEC 4

typedef enum {
  BLD_IDLE,
  BLD_READ_CMD,
  BLD_EXE_CMD,
  BLD_RESPONDING,
  BLD_FINISH
} bld_state_e;

/**
 *  FUNCTIONS
 *===================================================================
 */

#endif