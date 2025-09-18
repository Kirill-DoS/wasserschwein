#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
//#include "hardware/pwm.h"

#define UART_ID uart0
#define BAUD_RATE 9600
#define UART_TX_PIN 0
#define UART_RX_PIN 1
#define LED 2


int main(){
    stdio_init_all();
    gpio_init(LED);
    uart_init(UART_ID, BAUD_RATE);

    gpio_set_dir(LED, GPIO_OUT);

    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    while(true){
        if(uart_is_readable(UART_ID)){
            char c = uart_getc(UART_ID);
            
            if(c == '1'){
                gpio_put(LED, 1);
            }else 
            if(c == '0'){
                gpio_put(LED, 0);
            }

            sleep_ms(10);
        }
    }
}