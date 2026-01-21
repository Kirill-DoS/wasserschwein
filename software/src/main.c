#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"

#include "arcanoid.h"
#include "constants.h"
#include "uart.h"

uint motor1_slice = 0;
uint motor2_slice = 0;
uint chan1 = 0;
uint chan2 = 0;

void config(void);

int main(void){
    stdio_init_all();
    config();
    sleep_ms(1000);

    printf("RP2040 running!\n");
    gpio_put(LED, 1);


    while(true){
        parse_uart_buf();

        // get_uart_buf();
        // parse_uart_buf();
        // if(is_cmd_ready){
        //     print_uart_buf();
        //     is_cmd_ready = 0;
        //     clear_buf();
        // }
    }

return 0;
}

void config(void){
    gpio_set_function(L, GPIO_FUNC_PWM);
    gpio_set_function(R, GPIO_FUNC_PWM);
    gpio_set_function(SERVO1, GPIO_FUNC_PWM);
    gpio_set_function(SERVO2, GPIO_FUNC_PWM);
    gpio_set_function(TX, GPIO_FUNC_UART);
    gpio_set_function(RX, GPIO_FUNC_UART);
    uart_init(UART_ID, BAUDRATE);
    gpio_init(LED);
    gpio_set_dir(LED, 1);

    motor1_slice = pwm_gpio_to_slice_num(L);
    pwm_set_clkdiv(motor1_slice, MOTOR_DIVIDER);
    pwm_set_wrap(motor1_slice, MOTOR_WRAP);
    pwm_set_enabled(motor1_slice, true);

    motor2_slice = pwm_gpio_to_slice_num(R);
    pwm_set_clkdiv(motor2_slice, MOTOR_DIVIDER);
    pwm_set_wrap(motor2_slice, MOTOR_WRAP);
    pwm_set_enabled(motor2_slice, true);

    uint servo1_slice = pwm_gpio_to_slice_num(SERVO1);
    pwm_set_clkdiv(servo1_slice, SERVO_DIVIDER);
    pwm_set_wrap(servo1_slice, SERVO_WRAP);
    pwm_set_enabled(servo1_slice, true);

    uint servo2_slice = pwm_gpio_to_slice_num(SERVO2);
    pwm_set_clkdiv(servo2_slice, SERVO_DIVIDER);
    pwm_set_wrap(servo2_slice, SERVO_WRAP);
    pwm_set_enabled(servo2_slice, true);

    //motor1_slice = pwm_gpio_to_slice_num(L);
    chan1 = pwm_gpio_to_channel(L);
    //motor2_slice = pwm_gpio_to_slice_num(R);
    chan2 = pwm_gpio_to_channel(R);
}
