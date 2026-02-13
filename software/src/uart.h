#ifndef UART_H
#define UART_H

#include <stdio.h>
#include "constants.h"

#define MAX_SIZE 10
#define NEW_BUF_SIZE 3

extern bool is_cmd_ready;
extern int uart_idx;
extern char uart_buf[MAX_SIZE];
extern char new_uart_buf[NEW_BUF_SIZE];

void get_uart_buf();
void print_uart_buf();
void parse_uart_buf();
void make_new_buf();  // Изменено имя для ясности
static inline void clear_buf() {
    uart_idx = 0;
    for(int i = 0; i < MAX_SIZE; i++) {
        uart_buf[i] = '\0';
    }
    is_cmd_ready = 0;
}

#endif
