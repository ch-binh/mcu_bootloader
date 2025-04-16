#ifndef HAL_UART_H
#define HAL_UART_H

#include "bootloader.h"
#include "hal_bld.h"
#include <string.h>

/**
 *  VARIABLES AND DEFINES
 *===================================================================
 */
#define UART_RX_LEN_MAX 256
#define UART_END_BYTE 0xFE

/**
 *  SETUPS
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
 *  BLD APPLICATION
 *===================================================================
 */
bld_cmd_e hal_uart_read_cmd(void);
void hal_uart_resp(UART_Regs *const reg, uint8_t *data, uint8_t size);

/**
 *                       FETCH DATA
 *===================================================================
 */

void hal_uart_fetch_rx_buf(uint8_t *buf, uint16_t len);
uint8_t hal_uart_fetch_rx_buf_cnt(void);

/**
 *                       INTERRUPT HANDLER
 *===================================================================
 */
void UART_0_INST_IRQHandler(void);

#endif