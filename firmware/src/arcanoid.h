#ifndef ARCANOID_H
#define ARCANOID_H

#include "pico/stdlib.h"
//motor
extern uint motor1_slice;
extern uint motor2_slice;
extern uint chan1;
extern uint chan2;
extern uint servo1_slice;
extern uint servo2_slice;

// Управляет направлением и мощностью двигателя каретки в диапазоне -255…255.
void drive(int pwm);
//servo
// Настраивает PWM-слайс, к которому подключён ESC или сервопривод.
void servo_init(uint GPIO);
// Передаёт ESC длительность импульса от 1000 до 2000 микросекунд.
void esc_set_speed(uint pulse_us, uint num);
// Оставлен для совместимости со старыми вызовами управления сервоприводом.
void write_ms(uint degree, uint num);

//comutation
// Считывает сырое значение АЦП с указанного входа аккумулятора.
float battery_charge(uint GPIO);
// Возвращает true для одного подтверждённого нажатия кнопки.
bool button_clicked(uint GPIO);
// Ограничивает целое значение между нижней и верхней границами.
int constrain(int value, int min_value, int max_value);

#endif
