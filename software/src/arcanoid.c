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
#define FI 11
#define BI 10
#define SYS_FREQ 125000000
#define WRAP 99
#define DIVIDER 125.0f

void fi(int *pwm)
{
    
}

void bi(int *pwm)
{
    
}


//----------------uncolector motor---------
//servo init
#define SERVO1 12
#define SERVO2 13
#define SERVO_WRAP 19999
#define SERVO_DIVIDER 125.0f

void servo_1_init()
{
    gpio_set_function(SERVO1, GPIO_FUNC_PWM);
    int slice_num = pwm_gpio_to_slice_num(SERVO1);
    int chan = pwm_gpio_to_channel(SERVO1);

    pwm_config config = pwm_get_default_config();
    pwm_config_set_clkdiv(&config, SERVO_DIVIDER);
    pwm_config_set_wrap(&config, SERVO_WRAP);

    pwm_init(slice_num, &config, true);

}

void servo_2_init()
{
    gpio_set_function(SERVO2, GPIO_FUNC_PWM);
    int slice_num = pwm_gpio_to_slice_num(SERVO2);
    int chan = pwm_gpio_to_channel(SERVO2);

    pwm_config config = pwm_get_default_config();
    pwm_config_set_clkdiv(&config, SERVO_DIVIDER);
    pwm_config_set_wrap(&config, SERVO_WRAP);

    pwm_init(slice_num, &config, true);
}

void esc_set_speed(int *percent, int num)
{
    int speed = constrain(percent, 100, 0);

    int pulse_us = 1000 + (speed * 10);
    int level = (pulse_us * WRAP) / 20000;
    pwm_set_gpio_level(num, level);
}

//------------comutation-----------------
//init
#define BUTTON_PIN 5
#define LED_PIN 2
#define BATERY 26

float battery_charge(int *GPIO)
{
    
}

void button_clicked(int *GPIO)
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

led_on(int *GPIO)
{}