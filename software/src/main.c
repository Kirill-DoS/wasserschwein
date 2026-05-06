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
uint servo1_slice = 0;
uint servo2_slice = 0;

void config(void);
void callibrate_esc(void);

int main(void){
    //IS_DEBUG = true;

    stdio_init_all();
    config();
    sleep_ms(1000);

    printf("RP2040 running!\n");
    callibrate_esc();
    gpio_put(LED, 1);

    while(true){
        get_uart_buf();
        if(is_cmd_ready){
            parse_uart_buf();
            clear_buf();
        }
    }

    return 0;
}

void callibrate_esc(void){
    esc_set_speed(1000, SERVO1);
    esc_set_speed(1000, SERVO2);
    sleep_ms(1000);
    esc_set_speed(2000, SERVO1);
    esc_set_speed(2000, SERVO2);
    sleep_ms(1000);
    esc_set_speed(1200, SERVO1);
    esc_set_speed(1200, SERVO2);
    sleep_ms(500);
    esc_set_speed(1000, SERVO1);
    esc_set_speed(1000, SERVO2);
    printf("Callibration pass\n");
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

    servo1_slice = pwm_gpio_to_slice_num(SERVO1);
    pwm_set_clkdiv(servo1_slice, SERVO_DIVIDER);
    pwm_set_wrap(servo1_slice, SERVO_WRAP);
    pwm_set_enabled(servo1_slice, true);

    servo2_slice = pwm_gpio_to_slice_num(SERVO2);
    pwm_set_clkdiv(servo2_slice, SERVO_DIVIDER);
    pwm_set_wrap(servo2_slice, SERVO_WRAP);
    pwm_set_enabled(servo2_slice, true);

    chan1 = pwm_gpio_to_channel(L);
    chan2 = pwm_gpio_to_channel(R);

     pwm_set_chan_level(motor1_slice, chan1, 0);
    pwm_set_chan_level(motor2_slice, chan2, 0);

}
