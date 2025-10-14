#ifndef ARCANOID_H
#define ARCANOID_H

#include "pico/stdlib.h"
//motor 
void motor_init(uint GPIO);
void drive(uint left, uint rigth, uint GPIO1, uint GPIO2);

//servo
void servo_init(uint GPIO);
void esc_set_speed(uint pulse_us, uint num);

//comutation
float battery_charge(uint GPIO);
void button_clicked(uint GPIO);
void led_on(uint GPIO, bool state);
int constrain(int value, int low_level, int high_level);

#endif