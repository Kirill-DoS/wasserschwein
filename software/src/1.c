#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

#define UART_ID uart0
#define BAUD_RATE 9600
#define UART_TX_PIN 0
#define UART_RX_PIN 1


// Включает, выключает или кратко мигает светодиодом в старом тестовом примере.
void on_off_LED(const int NUM_LED, const int del, const int status){
    
    int state = status;
    int LED = NUM_LED;
    int delay = del;
    gpio_set_dir(LED, 1);
    
    if(state == 1){
        gpio_put(LED, 1);
    }
    else if(state == 0){
        gpio_put(LED, 0);
    }
    else if(state == 2){
        gpio_put(LED, 1);
        sleep_ms(del);
        gpio_put(LED, 0);
        sleep_ms(del);
    }
   

}

// Обрабатывает один символ Bluetooth в старом тестовом примере.
void read_bluetooth(char c){
    
    if(c == 'O'){
        on_off_LED(2, 500, 1);
        char A = 'activate';
        uart_putc(UART_ID, A);
    }else if(c == 'o'){
        char D= 'deactivate';
        uart_putc(UART_ID, D);  
        on_off_LED(2,500, 0);
    }
}

// Запускает устаревший тест UART и светодиода; в основную прошивку не входит.
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
        // if (uart_is_readable(UART_ID)) {
        //     char c = uart_getc(UART_ID);
        //     read_bluetooth(c);
            
        // }
        
        on_off_LED(2, 500, 1);

        sleep_ms(10);
    }
}
