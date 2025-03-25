#include "inc/hal_bld.h"


/**
 * @brief Verify that app image exists
 * @return true if verification is successful, false otherwise
 */
int hal_bld_verify_app_mem(uint32_t start_adr) {
  uint32_t *p32 = (uint32_t *)(start_adr);
  if ((p32[0] < RAM_START_ADDR) || (p32[0] > RAM_END_ADDR)) {
    return -1;
  } else {
    for (uint8_t i = 1; i <= NUM_VEC; i++) {
      if ((p32[i] < FLASH_START_ADDR) || (p32[i] > FLASH_END_ADDR)) {
        return -1;
      }
    }
  }
  return 0;
}

void hal_bld_go_to_main_app(uint32_t jump_addr) {
  uint32_t app_addr;
  typedef void (*pfunction)(void);
  pfunction jump_to_app;

  app_addr = *(uint32_t *)(jump_addr + 0x04);
  jump_to_app = (pfunction)app_addr;
  jump_to_app();
}