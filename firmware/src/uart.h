#ifndef UART_H
#define UART_H

#include <stdio.h>
#include <stdbool.h>
#include "constants.h"

#define MAX_SIZE 16

extern bool is_cmd_ready;
extern int uart_idx;
extern char uart_buf[MAX_SIZE];

// Считывает доступные байты UART до полной команды, оканчивающейся переводом строки.
void get_uart_buf();
// Выводит принятую команду в UART для ручной диагностики.
void print_uart_buf();
// Проверяет и выполняет принятую текстовую команду F/B/L/R/S.
void parse_uart_buf();
// Останавливает каретку, если допустимая команда давно не приходила.
void uart_safety_watchdog();

// Очищает буфер после обработки команды или ошибки протокола.
static inline void clear_buf() {
    uart_idx = 0;
    for(int i = 0; i < MAX_SIZE; i++) {
        uart_buf[i] = '\0';
    }
    is_cmd_ready = 0;
}

#endif
