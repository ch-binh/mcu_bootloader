

#include "inc/bootloader.h"
#include "inc/hal_bld.h"
#include "inc/hal_gpio.h"
#include "inc/hal_uart.h"

volatile bld_state_e sys_state = BLD_IDLE;
volatile bld_cmd_e host_cmd = CMD_NOP;

extern uint8_t uart_rx_ctr; // rx buffer counter
extern uint8_t uart_rx_buf[UART_RX_LEN_MAX];

static void exe_cmd(void) {
  switch (host_cmd) {
  case CMD_GET_BLD_VER: {

    uint8_t bld_ver[BLD_VER_LEN] = {BLD_VER_MAJOR, BLD_VER_RESERVE,
                                    BLD_VER_MINOR, BLD_VER_PATCH};

    hal_uart_burst_write(UART_0_INST, bld_ver, BLD_VER_LEN);
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
      host_cmd = hal_uart_read_cmd(uart_rx_buf, uart_rx_ctr);
      sys_state = BLD_EXE_CMD;
    } break;

    case BLD_EXE_CMD: {
      exe_cmd();
      sys_state = BLD_IDLE;
    } break;

    case BLD_RESPONDING: {

    } break;
    case BLD_FINISH: {

    } break;
    }
  }
}
