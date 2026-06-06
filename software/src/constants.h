#ifndef CONSTANTS_H
#define CONSTANTS_H
#include "hardware/clocks.h"


//motor constants
#define SYS_FREQ clock_get_hz(clk_sys)
#define MOTOR_WRAP 255
#define MOTOR_FREQ 5000  // 5 kHz
#define MOTOR_DIVIDER (SYS_FREQ / (MOTOR_FREQ * (MOTOR_WRAP + 1)))  // = 48.0

//servo init
#define SERVO_WRAP 19999
#define SERVO_DIVIDER 125.0f
#define MAX_PULSE 2000
#define ESC1_TARGET_PULSE 1200
#define ESC2_TARGET_PULSE 1020
#define MIN_PULSE 1000

//pins
#define UART_ID uart0
#define BAUDRATE 9600
#define TX 0
#define RX 1
#define LED 2
#define SERVO1 12
#define SERVO2 13
#define L 10
#define R 11
#define BAT 26
#define BUTTON 5

#endif
