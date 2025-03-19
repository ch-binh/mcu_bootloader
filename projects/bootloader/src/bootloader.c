

#include "inc/bootloader.h"
#include "inc/hal_bld.h"
#include "inc/hal_gpio.h"

/* This results in approximately 0.5s of delay assuming 24MHz CPU_CLK */
volatile uint8_t gEchoData = 0;

int main(void) {
  int ret;
  /* Power on GPIO, initialize pins as digital outputs */
  SYSCFG_DL_init();

  NVIC_ClearPendingIRQ(UART_0_INST_INT_IRQN);
  NVIC_EnableIRQ(UART_0_INST_INT_IRQN);

  if (!DL_GPIO_readPins(GPIOA_PORT, GPIOA_ENTER_BLD_PIN)) {
    ret = hal_bld_verify_app_mem(FLASH_MAIN_APP_ADDR);
    if (ret) {
      // hal_bld_go_to_main_app(FLASH_MAIN_APP_ADDR);
    }
  }

  DL_SYSCTL_enableSleepOnExit();

  while (1) {
    __WFI();
  }
}

void UART_0_INST_IRQHandler(void) {
  switch (DL_UART_Main_getPendingInterrupt(UART_0_INST)) {
  case DL_UART_MAIN_IIDX_RX:
    DL_GPIO_togglePins(GPIOA_PORT, GPIOA_BUILTIN_LED_PIN);
    gEchoData = DL_UART_Main_receiveData(UART_0_INST);
    DL_UART_Main_transmitData(UART_0_INST, gEchoData);
    break;
  default:
    break;
  }
}
