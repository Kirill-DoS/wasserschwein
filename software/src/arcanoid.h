#ifndef ARCNOID_H
#define ARCANOID_H

void fi(int *pwm);
void bi(int *pwm);
void servo_1_init(int *millisec);
void servo_2_init(int *millisec);
void esc_set_speed(int *percent);
float battery_charge(int *GPIO);
void button_clicked(int *GPIO);
void led_on(int *GPIO);

#endif