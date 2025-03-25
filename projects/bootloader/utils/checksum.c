#include "checksum.h"
#include "stdio.h"

/**
 * Checksum algorithm
 * @param data data to be check
 * @param len data length
 */
uint8_t calc_checksum(uint8_t *data, uint8_t len) {
  // combine all data
  int total_cs = 0;
  for (uint8_t i = 0; i < len; i++) {
    total_cs += data[i];
  }

  return (256 - (total_cs & 0xFF)) & 0xFF;

}