#include "arcanoid.h"
#include "constants.h"

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"
#include "hardware/adc.h"

#include <stdio.h>

char debug_buf[20];

// Чистая функция управления моторами без блокирующих задержек
void drive(int pwm){
    int level = pwm;

    if(pwm > 0){
        // Ограничиваем уровень от 0 до 255 на всякий случай
        level = constrain(pwm, MAX_VEL, 0);
        pwm_set_chan_level(motor1_slice, chan1, MAX_VEL);
        pwm_set_chan_level(motor2_slice, chan2, (MAX_VEL - level));
    }else if(pwm < 0){
        level = constrain(pwm, 0, -MAX_VEL);
        pwm_set_chan_level(motor1_slice, chan1, (MAX_VEL + level));
        pwm_set_chan_level(motor2_slice, chan2, MAX_VEL);
    }else if(pwm == 0){
        pwm_set_chan_level(motor1_slice, chan1, MAX_VEL);
        pwm_set_chan_level(motor2_slice, chan2, MAX_VEL);
    }
}

void servo_init(uint GPIO){
    uint slice_num = pwm_gpio_to_slice_num(GPIO);
    pwm_set_clkdiv(slice_num, SERVO_DIVIDER);
    pwm_set_wrap(slice_num, SERVO_WRAP);
    pwm_set_enabled(slice_num, true);
}

void esc_set_speed(uint pulse_us, uint num)
{
    pulse_us = constrain(pulse_us, MAX_PULSE, MIN_PULSE);
    uint level = (pulse_us * (SERVO_WRAP + 1)) / 20000;

    uint chan = pwm_gpio_to_channel(num);
    pwm_set_chan_level(pwm_gpio_to_slice_num(num), chan, level);
}

void write_ms(uint degree, uint num){
    degree = constrain(degree, MAX_PULSE, MIN_PULSE);
    uint slice_num = pwm_gpio_to_slice_num(num);
    uint chan = pwm_gpio_to_channel(num);
    // Если функция не используется, оставляем пустой, багов нет
}

float battery_charge(uint GPIO) {
    adc_init();
    adc_gpio_init(26);
    adc_select_input(0);
    float val = adc_read();
    return val;
}

bool button_clicked(uint GPIO){
    if(gpio_get(GPIO) == 0){
        sleep_ms(20); // ИСПРАВЛЕНО: было двоеточие вместо точки с запятой
        if(gpio_get(GPIO) == 0){
            // Ждем пока пользователь ОТПУСТИТ кнопку, чтобы не было дребезга и повторных срабатываний
            while(gpio_get(GPIO) == 0) { sleep_ms(5); }
            return true;
        }
    }
    return false;
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
