#include "arcanoid.h"
#include "constants.h"

#include "hardware/adc.h"
#include "hardware/pwm.h"
#include "pico/stdlib.h"

// Управляет направлением и мощностью двигателя каретки в диапазоне -255…255.
void drive(int pwm) {
    int level = constrain(pwm, -MAX_VEL, MAX_VEL);

    if (level > 0) {
        pwm_set_chan_level(motor1_slice, chan1, MAX_VEL);
        pwm_set_chan_level(motor2_slice, chan2, MAX_VEL - level);
    } else if (level < 0) {
        pwm_set_chan_level(motor1_slice, chan1, MAX_VEL + level);
        pwm_set_chan_level(motor2_slice, chan2, MAX_VEL);
    } else {
        // Два высоких уровня для используемого драйвера означают активное торможение.
        pwm_set_chan_level(motor1_slice, chan1, MAX_VEL);
        pwm_set_chan_level(motor2_slice, chan2, MAX_VEL);
    }
}

// Настраивает PWM-слайс, к которому подключён ESC или сервопривод.
void servo_init(uint gpio) {
    uint slice_num = pwm_gpio_to_slice_num(gpio);
    pwm_set_clkdiv(slice_num, SERVO_DIVIDER);
    pwm_set_wrap(slice_num, SERVO_WRAP);
    pwm_set_enabled(slice_num, true);
}

// Передаёт ESC длительность импульса от 1000 до 2000 микросекунд.
void esc_set_speed(uint pulse_us, uint gpio) {
    pulse_us = (uint)constrain((int)pulse_us, MIN_PULSE, MAX_PULSE);
    uint level = (pulse_us * (SERVO_WRAP + 1)) / 20000;
    uint channel = pwm_gpio_to_channel(gpio);
    pwm_set_chan_level(pwm_gpio_to_slice_num(gpio), channel, level);
}

// Оставлен для совместимости со старыми вызовами управления сервоприводом.
void write_ms(uint degree, uint gpio) {
    (void)degree;
    (void)gpio;
}

// Считывает сырое значение АЦП с указанного входа аккумулятора.
float battery_charge(uint gpio) {
    if (gpio < 26 || gpio > 29) {
        return -1.0f;
    }
    adc_init();
    adc_gpio_init(gpio);
    adc_select_input(gpio - 26);
    return (float)adc_read();
}

// Возвращает true для одного подтверждённого нажатия кнопки.
bool button_clicked(uint gpio) {
    if (gpio_get(gpio) != 0) {
        return false;
    }

    sleep_ms(20);
    if (gpio_get(gpio) != 0) {
        return false;
    }

    while (gpio_get(gpio) == 0) {
        sleep_ms(5);
    }
    return true;
}

// Ограничивает целое значение между нижней и верхней границами.
int constrain(int value, int min_value, int max_value) {
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}
