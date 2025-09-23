#ifndef ARCNOID_H
#define ARCANOID_H

void fi(int *pwm);
void bi(int *pwm);

//servo
void servo_1_init();
void servo_2_init();
void esc_set_speed(int *percent, int num);

//comutation
float battery_charge(int *GPIO);
void button_clicked(int *GPIO);
void led_on(int *GPIO);
int constrain(int value, int high_level, int low_level);

#endif