#ifndef ARCNOID_H
#define ARCANOID_H

void fi(uint *pwm);
void bi(uint *pwm);
void push();
float battery_charge(int *GPIO);
void button_clicked(int *GPIO);
void led_on(int *GPIO);

#endif