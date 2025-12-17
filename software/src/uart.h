#ifndef UART_H
#define UART_H

#include <stdio.h>
#include "constants.h"

extern bool is_cmd_ready;
extern int uart_idx;

void get_uart_buf();
void print_uart_buf();

static inline void clear_buf() {
    uart_idx = 0;
} 

#endif