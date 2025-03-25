#ifndef HAL_UART_H
#define HAL_UART_H

#include "bootloader.h"

#define UART_RX_LEN_MAX 128

typedef enum {
  CMD_NOP,
  CMD_ERASE,
  CMD_BLANKING,
  CMD_UPLOADING,
  CMD_CHECK_CRC,
  CMD_SYSTEM_RESET,
  CMD_GET_BLD_VER,
  CMD_ENTER_BLD,
  CMD_EXIT_BLD,

  CMD_NUM
} bld_cmd_e;

void hal_uart_en_irq(void);

void hal_uart_write(UART_Regs *const reg, uint8_t data);
void hal_uart_burst_write(UART_Regs *const reg, uint8_t *data, uint8_t size);

void UART_0_INST_IRQHandler(void);

int hal_uart_read_cmd(uint8_t *data, uint8_t size);


#endif