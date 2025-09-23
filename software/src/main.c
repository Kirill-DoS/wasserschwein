#include <stdio.h>

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "arcanoid.h"

#define UART_ID uart0
#define BAUDRATE 9600
#define TX 0
#define RX 1

#define SERVO1 12
#define SERVO2 13

int main(){

    stdio_init_all();
    gpio_set_function(TX, GPIO_FUNC_UART);
    gpio_set_function(RX, GPIO_FUNC_UART);

    uart_init(UART_ID, BAUDRATE);
    servo_1_init();
    servo_2_init();


    while(1){
        if(uart_is_readable(UART_ID)){
            char c = uart_getc(UART_ID);
            uart_putc(UART_ID, c);

            if(c == '1'){
                esc_set_speed(100, SERVO1);
            }else if(c == '0'){
                esc_set_speed(0, SERVO1);
            // }else{
            //     uart_putc(UART_ID, 'E');
            //     uart_putc(UART_ID, c);
            // }
            sleep_ms(10);
        }
        
    }
}
return 0;
}