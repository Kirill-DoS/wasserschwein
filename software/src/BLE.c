#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

#define UART_ID uart0
#define BAUD_RATE 9600
#define UART_TX_PIN 0
#define UART_RX_PIN 1

int main() {
    stdio_init_all();
    sleep_ms(2000);
    printf("Bluetooth HC-06 Test\n");
    
    // Инициализация UART
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    
    while (true) {
        // Чтение данных из Bluetooth
        if (uart_is_readable(UART_ID)) {
            char c = uart_getc(UART_ID);
            putchar(c); // Вывод в консоль
            
            // Эхо обратно в Bluetooth
            uart_putc(UART_ID, c);
        }
        
        sleep_ms(10);
    }
}