#include "uart.h"
#include "constants.h"
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include <stdio.h>
#include "arcanoid.h"

#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#define MAX_SIZE 10

bool is_cmd_ready = 0;
int uart_idx = 0;
char uart_buf[MAX_SIZE];
char new_uart_buf[3];
char buf[20];

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
    printf("UART buffer\n", uart_buf);
}

void make_buf(){
    uart_buf[0] = 'M';
    uart_buf[1]  = (uint8_t) (200 >> 8);
    uart_buf[2] =( uint8_t) 200 ;
};

void parse_uart_buf(){

    char cmd_char = uart_buf[0];
    char value_str[10] = {0};

    // Копируем числовую часть команды
    strncpy(value_str, &uart_buf[1], strlen(uart_buf) - 2);
    int value = atoi(value_str);

    // Создаем new_uart_buf[3]
    new_uart_buf[0] = cmd_char;  // Байт 1: код команды

    if(cmd_char == 'F') {

        // Преобразуем в uint16_t (с учетом знака)
        //uint16_t unsigned_value = (uint16_t)(value + 255);  // Смещение для отрицательных значений

        //new_uart_buf[1] = (unsigned_value >> 8) & 0xFF;  // Старший байт
        //new_uart_buf[2] = unsigned_value & 0xFF;         // Младший байт

        drive(value);

        //uart_puts(UART_ID, new_uart_buf);
        //printf("Motor command: %c, value: %d, bytes: 0x%02X 0x%02X\n",
        //       cmd_char, value, new_uart_buf[1], new_uart_buf[2]);

    } else if(cmd_char == 'B'){

        drive(-1*value);

    } else if(cmd_char == 'L') {

       // new_uart_buf[1] = (value >> 8) & 0xFF;  // Старший байт
        //new_uart_buf[2] = value & 0xFF;         // Младший байт

        esc_set_speed(value, SERVO2);

        //uart_puts(UART_ID, "Left servo");
        //printf("%c servo command: %d, bytes: 0x%02X 0x%02X\n",
        //      cmd_char, value, new_uart_buf[1], new_uart_buf[2]);

    } else if(cmd_char == 'R'){
       // new_uart_buf[1] = (value >> 8) & 0xFF;  // Старший байт
        //new_uart_buf[2] = value & 0xFF;         // Младший байт

        esc_set_speed(value, SERVO1);
        //uart_puts(UART_ID, "Right servo\n");
        //printf("%c servo command: %d, bytes: 0x%02X 0x%02X\n",
        //       cmd_char, value, new_uart_buf[1], new_uart_buf[2]);
    }
    // else if(cmd_char == 'A'){
    //     // char adc_uart[20] = {"adc val: "};
    //     // adc_uart += (char)battery_charge(BAT);
    //     sprintf(buf, "%.2f", battery_charge(BAT));
    //     uart_puts(UART_ID, "adc val: ");
    //     uart_puts(UART_ID, buf);

    //     printf("ADC val: %d\n", battery_charge(BAT));
    // }
    else{
        uart_puts(UART_ID, "error\n");
    }
}
