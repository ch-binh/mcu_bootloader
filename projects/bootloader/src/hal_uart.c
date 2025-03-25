#include "inc/hal_uart.h"
#include "inc/bootloader.h"
#include "ti/driverlib/m0p/dl_core.h"

extern volatile bld_state_e sys_state;

uint8_t uart_rx_ctr = 0; // rx buffer counter
uint8_t uart_rx_buf[UART_RX_LEN_MAX];

void hal_uart_en_irq(void) {
  NVIC_ClearPendingIRQ(UART_0_INST_INT_IRQN);
  NVIC_EnableIRQ(UART_0_INST_INT_IRQN);
}

/*=======================ANALYZE UART COMMANDS======================*/
/*
static void UART_fill_data(uint8_t u8_data) {
  if (irq_cmd == IRQ_CMD_NOP) {
    switch (u8_data) {
    case RQ_ERASE: {
      irq_cmd = IRQ_CMD_ERASE;
    } break;

    case RQ_CHECK_BLANKING: {
      irq_cmd = IRQ_CMD_CHECK_BLANKING;
    } break;

    case RQ_CHECK_CRC: {
      irq_cmd = IRQ_CMD_CHECK_CRC;
    } break;

    case RQ_UPLOADING: {
      irq_cmd = IRQ_CMD_UPLOADING;
      state = START_WRITE;
      cmd = CMD_UPLOADING;
    } break;

    case RQ_SYSTEM_RESET: {
      cmd = CMD_SYSTEM_RESET;
    } break;

    case RQ_GET_BLD_VER: {
      cmd = CMD_GET_BLD_VER;
    } break;

    case RQ_ENTER_BLD: {
      irq_cmd = IRQ_CMD_ENTER_BLD;
    } break;

    case RQ_EXIT_BLD: {
      irq_cmd = IRQ_CMD_EXIT_BLD;
    } break;

    default:
      break;
    }

    line_ptr = 0;
    line_len = 0;
    uploading_timer = 0;

  } else {
    switch (irq_cmd) {
    case IRQ_CMD_UPLOADING: {
      data.byte[line_ptr++] = u8_data;
      if (line_ptr == 1) {
        line_len = 5 + data.byte[0];
      } else if (line_len == line_ptr) {
        cmd = CMD_UPLOADING;
        state = WRITE_DATA;
        start_timeout = true;
        line_ptr = 0;
        irq_cmd = IRQ_CMD_NOP;
      }
    } break;

    case IRQ_CMD_CHECK_CRC: {
      data.byte[line_ptr++] = u8_data;
      // 4 byte start + 4 byte len
      // 4 bytes for 32 bits crc
      // 1 byte cs
      if (line_ptr == 13) {
        cmd = CMD_CHECK_CRC;
        line_ptr = 0;
        start_timeout = true;
        irq_cmd = IRQ_CMD_NOP;
      }
    } break;

    case IRQ_CMD_CHECK_BLANKING: {
      data.byte[line_ptr++] = u8_data;
      // 4 bytes for address and 4 bytes for size, 1 byte cs
      if (line_ptr == 9) {
        cmd = CMD_BLANKING;
        line_ptr = 0;
        start_timeout = true;
        irq_cmd = IRQ_CMD_NOP;
      }
    } break;

    case IRQ_CMD_ERASE: {
      data.byte[line_ptr++] = u8_data;
      // 4 bytes for address and 4 bytes for size, 1 byte cs
      if (line_ptr == 9) {
        cmd = CMD_ERASE;
        line_ptr = 0;
        start_timeout = true;
        irq_cmd = IRQ_CMD_NOP;
      }
    } break;

    case IRQ_CMD_ENTER_BLD: {
      // 4 bytes rq key, 1 byte cs
      data.byte[line_ptr++] = u8_data;
      if (line_ptr == 5) {
        cmd = CMD_ENTER_BLD;
        line_ptr = 0;
        start_timeout = true;
        irq_cmd = IRQ_CMD_NOP;
      }
    } break;

    case IRQ_CMD_EXIT_BLD: {
      // 4 bytes res key, 1 byte cs
      data.byte[line_ptr++] = u8_data;
      if (line_ptr == 5) {
        cmd = CMD_EXIT_BLD;
        line_ptr = 0;
        start_timeout = true;
        irq_cmd = IRQ_CMD_NOP;
      }
    } break;

    default:
      break;
    }
  }
}
*/

void hal_uart_write(UART_Regs *const reg, uint8_t data) {
  DL_UART_Main_transmitData(reg, data);
}

void hal_uart_burst_write(UART_Regs *const reg, uint8_t *data, uint8_t size) {
  for (int i = 0; i < size; i++) {
    DL_UART_Main_transmitData(reg, data[i]);
    // todo: if there is a function to check if uart tx ready, use here
    while (DL_UART_Main_isBusy(reg)) {
      delay_cycles(240); // delay (1us)
    }
  }
}

/*========================INTERRUPT===============================*/
void UART_0_INST_IRQHandler(void) {
  switch (DL_UART_Main_getPendingInterrupt(UART_0_INST)) {
  case DL_UART_MAIN_IIDX_RX:
    uart_rx_buf[uart_rx_ctr] = DL_UART_Main_receiveData(UART_0_INST);
    uart_rx_ctr++;
    if (uart_rx_buf[uart_rx_ctr - 1] == '\n') {
      //   if (hal_uart_read_cmd(uart_rx_buf, uart_rx_ctr) == -1)
      //     break;

      // hal_uart_burst_write(UART_0_INST, uart_rx_buf, uart_rx_ctr);
      sys_state = BLD_READ_CMD;
      // uart_rx_ctr = 0;
    }

    break;
  default:
    break;
  }
}

/*========================Application specific===============================*/

int hal_uart_read_cmd(uint8_t *data, uint8_t size) {

  /* Check if data size is matched */
  if (data[0] != (size - 3)) {
    return -1;
  }
  if (data[size - 2] != calc_checksum(data, size - 2)) {
    return -1;
  }

  /* reset data package */
  uart_rx_ctr = 0;
  return data[1];
}
