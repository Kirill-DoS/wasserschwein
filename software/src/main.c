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
        esc_set_speed(2000, SERVO1);
        sleep_ms(2000);
        esc_set_speed(1500, SERVO1);
        sleep_ms(1000);
        esc_set_speed(1000, SERVO1);
        sleep_ms(2000);
        esc_set_speed(1500, SERVO1);
        sleep_ms(500);       
    }
return 0;
}