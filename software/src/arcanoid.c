#include "arcanoid.h"

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/pwm.h"


//uart init
// #define UART_ID uart0
// #define BAUD_RATE 9600
// #define UART_TX 0
// #define UART_RX 1


//-------------colector motor-----------
//pwm init
#define SYS_FREQ 125000000
#define WRAP 255
#define DIVIDER SYS_FREQ / (WRAP + 1)

void motor_init(uint GPIO){
    gpio_set_function(GPIO, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(GPIO);

    pwm_set_clkdiv(slice_num, DIVIDER);
    pwm_set_wrap(slice_num, WRAP);
    pwm_set_enabled(slice_num, true);
}

void drive(uint left, uint right, uint GPIO1, uint GPIO2){
    uint slice_num1 = pwm_gpio_to_slice_num(GPIO1);
    uint slice_num2 = pwm_gpio_to_slice_num(GPIO2);
    uint chan1 = pwm_gpio_to_channel(GPIO1);
    uint chan2 = pwm_gpio_to_channel(GPIO2);

    left = constrain(left, 0, WRAP);
    right = constrain(right, 0, WRAP);

    pwm_set_chan_level(slice_num1, chan1, left);
    pwm_set_chan_level(slice_num2, chan2, right);
}


//----------------uncolector motor---------
//servo init
#define SERVO1 12
#define SERVO2 13
#define SERVO_WRAP 19999
#define SERVO_DIVIDER 125.0f

void servo_init(uint GPIO){
    uint slice_num = pwm_gpio_to_slice_num(GPIO);
    
    pwm_set_clkdiv(slice_num, SERVO_DIVIDER);
    pwm_set_wrap(slice_num, SERVO_WRAP);
    pwm_set_enabled(slice_num, true);
}

void esc_set_speed(uint pulse_us, uint num)
{
    pulse_us = constrain(pulse_us, 1000, 2000);

    uint slice_num = pwm_gpio_to_slice_num(num);
    uint chan = pwm_gpio_to_channel(num);
    uint level = (pulse_us * (SERVO_WRAP + 1)) / 20000;

    pwm_set_chan_level(slice_num, chan, level);
}

//------------comutation-----------------
//init
#define BUTTON_PIN 5
#define LED_PIN 2
#define BATTERY 26

float battery_charge(uint GPIO)
{
    
}

void button_clicked(uint GPIO)
{

}

int constrain(int value, int high_level, int low_level)
{
    if(value > high_level){
        return high_level;
    }else if(value < low_level){
        return low_level;
    }else{
        return value;
    }
}
void led_on(uint GPIO, bool state)
{
    gpio_init(GPIO);
    if(state == 1){
        gpio_set_dir(GPIO, true);
        gpio_put(GPIO, 1);
    }else{
        gpio_set_dir(GPIO, true);
        gpio_put(GPIO, 1);
    }

}