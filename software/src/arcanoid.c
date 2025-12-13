#include "arcanoid.h"
#include "constants.h"

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"


//-------------DC motor-----------

void motor_init(uint GPIO){
    gpio_set_function(GPIO, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(GPIO);

    pwm_set_clkdiv(slice_num, MOTOR_DIVIDER);
    pwm_set_wrap(slice_num, MOTOR_WRAP);
    pwm_set_enabled(slice_num, true);
}

void drive(uint left, uint right, uint GPIO1, uint GPIO2){
    uint slice_num1 = pwm_gpio_to_slice_num(GPIO1);
    uint slice_num2 = pwm_gpio_to_slice_num(GPIO2);
    uint chan1 = pwm_gpio_to_channel(GPIO1);
    uint chan2 = pwm_gpio_to_channel(GPIO2);

    // Просто ограничиваем 0-255
    left = constrain(left, 255, 0);
    right = constrain(right, 255, 0);

    pwm_set_chan_level(slice_num1, chan1, left);
    pwm_set_chan_level(slice_num2, chan2, right);
}

//----------------BLCD motor---------

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

void write_ms(uint degree, uint num){
    degree = constrain(degree, 2400, 600);

    uint slice_num = pwm_gpio_to_slice_num(num);
    uint chan = pwm_gpio_to_channel(num);
    
}
//------------comutation-----------------
//init
#define BUTTON_PIN 5
#define BATTERY_PIN 26

float battery_charge(uint GPIO) {return 1.0;}

void button_clicked(uint GPIO){}

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
