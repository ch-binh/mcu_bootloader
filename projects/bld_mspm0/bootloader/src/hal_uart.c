#include "ti/driverlib/m0p/dl_core.h"

#include "inc/bootloader.h"
#include "inc/hal_bld.h"
#include "inc/hal_uart.h"

#include "utils/checksum.h"
#include "utils/crc.h"

extern volatile bld_state_e sys_state;

/**
 *  VARIABLES
 *===================================================================
 */

static uint8_t rx_buf_cnt = 0; // rx buffer counter
static uint8_t rx_buf[UART_RX_LEN_MAX];

/**
 *  SETUPS
 *===================================================================
 */

void hal_uart_en_irq(void) {
  NVIC_ClearPendingIRQ(UART_0_INST_INT_IRQN);
  NVIC_EnableIRQ(UART_0_INST_INT_IRQN);
}

/**
 *  BASIC OPERATIONS
 *===================================================================
 */

void hal_uart_write(UART_Regs *const reg, uint8_t data) {
  DL_UART_Main_transmitData(reg, data);
}

void hal_uart_burst_write(UART_Regs *const reg, uint8_t *data, uint8_t size) {
  /* Send actual data package*/
  for (int i = 0; i < (size); i++) {
    DL_UART_Main_transmitData(reg, data[i]);
    // todo: if there is a function to check if uart tx ready, use here
    while (DL_UART_Main_isBusy(reg)) {
      delay_cycles(240); // delay (1us)
    }
  }
}

/**
 *  APLICATION
 *===================================================================
 */
bld_cmd_e hal_uart_read_cmd(void) {

  /* Verify rx data*/
  
  // in case of crc
  if (rx_buf[1] == CMD_WRITE_CRC) {    
    uint32_t crc_result = crc32_lookup_tb(0, rx_buf_cnt - 4, rx_buf);
    for (int i = 0; i < 4; i++) {
      if (rx_buf[rx_buf_cnt - 1 - i] != ((crc_result >> (8 * i)) & 0xFF)) {
        return CMD_UNDEFINED;
      }
    }
  } else if (rx_buf[rx_buf_cnt - 1] != calc_checksum(rx_buf, rx_buf_cnt - 1)) {
    return CMD_UNDEFINED;
  }

  /* reset data package */
  rx_buf_cnt = 0;
  return rx_buf[1];
}

void hal_uart_resp(UART_Regs *const reg, uint8_t *data, uint8_t size) {
  uint8_t tx_buf[size + 2];

  tx_buf[0] = size + 2;                // add len to the packet
  for (uint8_t i = 0; i < size; i++) { // move data buffer up 1 element
    tx_buf[i + 1] = data[i];
  }
  tx_buf[size + 1] = calc_checksum(tx_buf, size + 1); // add cs

  hal_uart_burst_write(reg, tx_buf, size + 2);
}

/**
 *  FETCH DATA
 *===================================================================
 */

void hal_uart_fetch_rx_buf(uint8_t *buf, uint16_t len) {
  if (len > UART_RX_LEN_MAX)
    len = UART_RX_LEN_MAX;
  memcpy(buf, rx_buf, len);
}

uint8_t hal_uart_fetch_rx_buf_cnt(void) { return rx_buf_cnt; }

/**
 *  INTERRUPT HANDLER
 *===================================================================
 */
void UART_0_INST_IRQHandler(void) {
  switch (DL_UART_Main_getPendingInterrupt(UART_0_INST)) {
  case DL_UART_MAIN_IIDX_RX:
    rx_buf[rx_buf_cnt] = DL_UART_Main_receiveData(UART_0_INST);
    rx_buf_cnt++;
    if (rx_buf_cnt == (rx_buf[0])) {
      sys_state = BLD_READ_CMD;
    }

    break;
  default:
    break;
  }
}
