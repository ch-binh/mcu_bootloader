#ifndef HAL_BLD_H
#define HAL_BLD_H

#include <stdint.h>
#include "bootloader.h"

int hal_bld_verify_app_mem(uint32_t start_adr);
void hal_bld_go_to_main_app(uint32_t jump_addr);

#endif // HAL_BLD_H