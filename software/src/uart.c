#include "uart.h"
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

#define MAX_SIZE 10

bool is_cmd_ready = 0;
int uart_idx = 0;
char uart_buf[MAX_SIZE];

void get_uart_buf(){
    if (uart_is_readable(UART_ID)){
        char c = uart_getc(UART_ID);
        uart_buf[uart_idx] = c;
        uart_idx++;

        if(uart_idx == MAX_SIZE){
            uart_idx = 0;
        }

        if(c == '\n'){
            is_cmd_ready = 1;
            uart_buf[uart_idx]  = '\0';
        }

    }
}

void print_uart_buf(){
    uart_puts(UART_ID, "UART buffer\n");
    uart_puts(UART_ID, uart_buf);

    // printf("%s", uart_buf);
    // printf("\n");
}