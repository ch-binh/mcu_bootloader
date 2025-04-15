

/**
 ******************************************************************************
 * @file    util.h
 * @author  VCD
 * @brief   Header file to compute CRC using software
 * @date    Nov 30 2023
 ******************************************************************************
 * @attention
 *
 * Copyright (c) 2023 Austin Circuit Design.
 * All rights reserved.
 ******************************************************************************
 */
#ifndef __UTIL_H
#define __UTIL_H

#include "utils/crc.h"
#include <stdbool.h>
#include <stdint.h>

#define CRC32_INIT_VAL 0
// CRC-16/BUYPASS
uint32_t crc32_lookup_tb(uint32_t crcInit, uint32_t len, uint8_t *pBuf);
#endif