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

void fi(uint *pwm)
{
    gpio_set_function(FI, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(FI);
    uint chan = pwm_gpio_to_channel(FI);

    pwm_set_clkdiv(slice_num, DIVIDER);
    pwm_set_wrap(slice_num, WRAP);
    pwm_set_chan_level(slice_num, chan, pwm);

    pwm_set_enabled(slice_num, 1);
}

void bi(uint *pwm)
{
    gpio_set_function(BI, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(BI);
    uint chan = pwm_gpio_to_channel(BI);

    pwm_config_set_clkdiv(slice_num, DIVIDER);
    pwm_set_wrap(slice_num, WRAP);
    pwm_set_chan_level(slice_num, chan, pwm);

    pwm_set_enabled(slice_num, 1);
}


//----------------uncolector motor---------
//servo init
#define SERVO1 12
#define SERVO2 13

void push()
{

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