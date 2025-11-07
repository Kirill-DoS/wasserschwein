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

void init(){

    gpio_set_function(L, GPIO_FUNC_PWM);
    gpio_set_function(R, GPIO_FUNC_PWM);
    gpio_set_function(SERVO1, GPIO_FUNC_PWM);
    gpio_set_function(SERVO2, GPIO_FUNC_PWM);
    //gpio_set_function(TX, GPIO_FUNC_UART);
    //gpio_set_function(RX, GPIO_FUNC_UART);
    gpio_init(LED);

}

int main(){
    int ms = 1500;
    int ms2 = 1600;
    int ms1 = 1300;

    stdio_init_all();    
    init();
    sleep_ms(200);
    gpio_set_dir(LED, 1);
    gpio_put(LED, 1);

    servo_init(SERVO1);
    servo_init(SERVO2);
    motor_init(L);
    motor_init(R);
    sleep_ms(200);
    
    while(true){   
        esc_set_speed(ms, SERVO1);
        sleep_ms(2000);
        esc_set_speed(ms1, SERVO1);
        sleep_ms(2000);
        // esc_set_speed(ms2, SERVO1);
        // sleep_ms(2000);
    }
    
return 0;
};
