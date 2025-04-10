#ifndef HAL_UART_H
#define HAL_UART_H

#include "bootloader.h"
#include <string.h>

#define UART_RX_LEN_MAX 128
#define UART_END_BYTE 0xFE

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
  CMD_NUM,
  CMD_UNDEFINED = 0xFF,
} bld_cmd_e;

/**
 *                       SETUPS
 *===================================================================
 */
void hal_uart_en_irq(void);

/**
 *                       UART BASIC OPERATIONS
 *===================================================================
 */

void hal_uart_write(UART_Regs *const reg, uint8_t data);
void hal_uart_burst_write(UART_Regs *const reg, uint8_t *data, uint8_t size);

/**
 *                       APPLICATION
 *===================================================================
 */
bld_cmd_e hal_uart_read_cmd(void);

/**
 *                       FETCH DATA
 *===================================================================
 */

void hal_uart_fetch_rx_buf(uint8_t *buf, uint8_t len);
uint8_t hal_uart_fetch_rx_buf_cnt(void);

/**
 *                       INTERRUPT HANDLER
 *===================================================================
 */
void UART_0_INST_IRQHandler(void);

#endif