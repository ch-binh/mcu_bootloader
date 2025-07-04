
#ifndef CHECKSUM_H
#define CHECKSUM_H

#include <stdint.h>
#include <stdbool.h>

uint8_t calc_checksum(uint8_t *data, uint8_t len);

#endif