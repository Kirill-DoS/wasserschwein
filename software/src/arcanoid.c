#include "arcanoid.h"
#include "constants.h"

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"
#include "hardware/adc.h"

#include <stdio.h>

//-------------DC motor-----------
char debug_buf[20];
bool IS_DEBUG = true;

void motor_init(){

}

void drive(int pwm){
    //uart_puts(UART_ID, "drive\n");
    int level = pwm;

    if(pwm > 0){
        //printf("pwm more 0\n");
        // level = constrain(pwm, 255, 0);
        pwm_set_chan_level(motor1_slice, chan1, 255);
        pwm_set_chan_level(motor2_slice, chan2, (255-level));
    }else if(pwm < 0){
        //printf("pwm less 0\n");
        //level = constrain(pwm, 0, -255);
        pwm_set_chan_level(motor1_slice, chan1, (255+level));
        pwm_set_chan_level(motor2_slice, chan2, 255);
    }else if(pwm == 0){
        //printf("pwm equal 0\n");
        //level = 0;
        pwm_set_chan_level(motor1_slice, chan1, 255);
        pwm_set_chan_level(motor2_slice, chan2, 255);
    }
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
    //pulse_us = constrain(pulse_us, 2000, 1000);
    uint level = (pulse_us * (SERVO_WRAP + 1)) / 20000;

    uint chan = pwm_gpio_to_channel(num);
    pwm_set_chan_level(pwm_gpio_to_slice_num(num), chan, level);
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

float battery_charge(uint GPIO) {
        adc_init();
        adc_gpio_init(26);
        adc_select_input(0);
        float val = adc_read();
        return val;
}

void button_clicked(uint GPIO){

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
