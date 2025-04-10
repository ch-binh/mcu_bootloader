

#include "inc/bootloader.h"
#include "inc/hal_bld.h"
#include "inc/hal_flash.h"
#include "inc/hal_gpio.h"
#include "inc/hal_uart.h"

volatile bld_state_e sys_state = BLD_IDLE;
volatile bld_cmd_e host_cmd = CMD_NOP;

static void bld_exe_cmd(void) {
  switch (host_cmd) {

  case CMD_GET_BLD_VER: {

    uint8_t bld_ver[BLD_VER_LEN] = {BLD_VER_MAJOR, BLD_VER_RESERVE,
                                    BLD_VER_MINOR, BLD_VER_PATCH};

    hal_uart_burst_write(UART_0_INST, bld_ver, BLD_VER_LEN);
  } break;

  case CMD_BLANKING: {
    uint8_t rx_buffer[UART_RX_LEN_MAX];
    uint32_t addr = 0;
    uint32_t size = 0;

    hal_uart_fetch_rx_buf(rx_buffer, sizeof(rx_buffer));

    for (int i = 0; i < 4; i++) {
      addr |= rx_buffer[2 + i] << (24 - i * 8);
      size |= rx_buffer[6 + i] << (24 - i * 8);
    }

    bool is_blank = hal_flash_check_blanking(addr, size);
    hal_uart_burst_write(UART_0_INST, (uint8_t *)&is_blank, sizeof(is_blank));
  } break;

  case CMD_ERASE: {
    while (1)
      ;
  } break;

  default:
    break;
  }
}

int main(void) {
  int ret;
  /* Power on GPIO, initialize pins as digital outputs */
  SYSCFG_DL_init();
  /* Init */

  /* Check if boot pin is selected */
  if (!DL_GPIO_readPins(GPIOA_PORT, GPIOA_ENTER_BLD_PIN)) {
    /* Verify if jumping address has been loaded */
    ret = hal_bld_verify_app_mem(FLASH_MAIN_APP_ADDR);
    if (!ret) {
      hal_bld_go_to_main_app(FLASH_MAIN_APP_ADDR);
    }
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
