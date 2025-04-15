#include "inc/bootloader.h"
#include "inc/hal_bld.h"
#include "inc/hal_flash.h"
#include "inc/hal_gpio.h"
#include "inc/hal_uart.h"

#include "utils/crc.h"

/**
 *  VARIABLES AND DEFINE
 *===================================================================
 */

volatile bld_state_e sys_state = BLD_IDLE;
volatile bld_cmd_e host_cmd = CMD_NOP;

/**
 *  Enter application
 *===================================================================
 */

static bool is_enter_app_triggred(void) {
  int ret;
  /* Check if boot pin is selected */
  if (!DL_GPIO_readPins(GPIOA_PORT, GPIOA_ENTER_BLD_PIN)) {
    /* Verify if jumping address has been loaded */
    ret = hal_bld_verify_app_mem(FLASH_MAIN_APP_ADDR);
    if (!ret) {
      return true;
    }
  }
  return false;
}

/**
 *  APPLICATION OPERATIONS
 *===================================================================
 */

static void bld_exe_cmd(void) {
  uint8_t rx_buffer[UART_RX_LEN_MAX];
  uint32_t addr = 0;
  uint32_t size = 0;

  hal_uart_fetch_rx_buf(rx_buffer, sizeof(rx_buffer)); // copy rx buffer
  switch (host_cmd) {

  case CMD_GET_BLD_VER: {

    uint8_t bld_ver[BLD_VER_LEN] = {BLD_VER_MAJOR, BLD_VER_RESERVE,
                                    BLD_VER_MINOR, BLD_VER_PATCH};

    hal_uart_resp(UART_0_INST, bld_ver, BLD_VER_LEN);
  } break;

  case CMD_CHECK_BLANKING:
  case CMD_ERASE: {
    /* shared process*/
    for (int i = 0; i < 4; i++) {
      addr |= rx_buffer[2 + i] << (24 - i * 8);
      size |= rx_buffer[6 + i] << (24 - i * 8);
    }

    /* Individual process*/
    if (host_cmd == CMD_CHECK_BLANKING) {
      bool is_blank = hal_flash_check_blanking(addr, size);
      hal_uart_resp(UART_0_INST, (uint8_t *)&is_blank, sizeof(is_blank));
    } else {
      hal_flash_erase_mem(addr, size);
      if (rx_buffer[rx_buffer[0] - 2] == REQ_ACK) {
        uint8_t ret = 0x01;
        hal_uart_resp(UART_0_INST, (uint8_t *)&ret, sizeof(ret));
      }
    }
  } break;
  case CMD_WRITE:
  case CMD_WRITE_CRC: {
    uint8_t byte_ofs = 0;
    if (host_cmd == CMD_WRITE_CRC) {
      byte_ofs = COR_BYTE_OFS; // shared code for when correction code can be
                               // checksum (1byte) or crc32bit (4 bytes)
    }

    for (int i = 0; i < 4; i++) {
      addr |= rx_buffer[2 + i] << (24 - i * 8);
    }

    uint32_t write_buffer = 0x00;
    for (int i = 0; i < rx_buffer[0] - (8 + byte_ofs); i += 4) {
      for (int j = 0; j < 4; j++) {
        write_buffer |= rx_buffer[6 + i + j] << (24 - j * 8);
      }
      hal_flash_write_mem_32bit(addr + i, write_buffer);
      write_buffer = 0x00;
    }

    if (rx_buffer[rx_buffer[0] - (2 + byte_ofs)] == REQ_ACK) {
      uint8_t ret = 0x01;
      hal_uart_resp(UART_0_INST, (uint8_t *)&ret, sizeof(ret));
    }

  } break;

  case CMD_CRC_CHECK: {
    /* 1. Fetch data from UART Buffer*/
    uint32_t ref_crc = 0;
    for (int i = 0; i < 4; i++) {
      addr |= rx_buffer[2 + i] << (24 - i * 8);
      size |= rx_buffer[6 + i] << (24 - i * 8);
      ref_crc |= rx_buffer[10 + i] << (24 - i * 8);
    }

    uint32_t calc_crc = crc32_lookup_tb(0, size, (uint8_t *)(addr));

    uint8_t ret;
    if (calc_crc != ref_crc) {
      ret = 0x00;
    }

    if (rx_buffer[rx_buffer[0] - 2] == REQ_ACK) {
      ret = 0x01;
      hal_uart_resp(UART_0_INST, (uint8_t *)&ret, sizeof(ret));
    }

  } break;
  case CMD_EXIT_BLD: {
    if (is_enter_app_triggred()) {
      hal_bld_go_to_main_app(FLASH_MAIN_APP_ADDR);
    }
  } break;

  default:
    break;
  }
}

/**
 *  MAIN
 *===================================================================
 */
int main(void) {

  /* Power on GPIO, initialize pins as digital outputs */
  SYSCFG_DL_init();
  /* Init */

  if (is_enter_app_triggred()) {
    hal_bld_go_to_main_app(FLASH_MAIN_APP_ADDR);
  }
  /*===============^^^================*/
  /* Instaying in bootloader */

  hal_uart_en_irq();
  // DL_SYSCTL_enableSleepOnExit();

  while (1) {
    switch (sys_state) {
    case BLD_IDLE: {
    } break;

    case BLD_READ_CMD: {
      host_cmd = hal_uart_read_cmd();
      if (host_cmd != CMD_UNDEFINED) {
        sys_state = BLD_EXE_CMD;
      }
    } break;

    case BLD_EXE_CMD: {
      bld_exe_cmd();
      sys_state = BLD_IDLE;
    } break;

    case BLD_RESPONDING: {

    } break;
    case BLD_FINISH: {

    } break;
    }
  }
}
