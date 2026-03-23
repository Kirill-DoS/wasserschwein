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

void motor_init();
void drive(int pwm);

//servo
void servo_init(uint GPIO);
void esc_set_speed(uint pulse_us, uint num);
void write_ms(uint degree, uint num);

//comutation
float battery_charge(uint GPIO);
void button_clicked(uint GPIO);
int constrain(int value, int low_level, int high_level);

#endif
