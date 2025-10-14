#include <stdio.h>

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/pwm.h"
#include "arcanoid.h"

#define UART_ID uart0
#define BAUDRATE 9600
#define TX 0
#define RX 1
#define LED 2
#define SERVO1 12
#define SERVO2 13
#define L 10
#define R 11

int main(){

    stdio_init_all();    

    uint slice_num = pwm_gpio_to_slice_num(LED);
    uint chan = pwm_gpio_to_channel(LED);

    pwm_set_clkdiv(slice_num, 125.0f);
    pwm_set_wrap(slice_num, 19999);
    pwm_set_enabled(slice_num, true);
    pwm_set_chan_level(slice_num, chan, 128);

    while(true){ 
        // led_on(LED, 1);
        // sleep_ms(500);
        // led_on(LED, 0);
        // sleep_ms(500);
    }
    
return 0;
};
