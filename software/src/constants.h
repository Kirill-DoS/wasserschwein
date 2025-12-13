#ifndef CONSTANTS_H
#define CONSTANTS_H
#include "hardware/clocks.h"

//motor constants
#define SYS_FREQ clock_get_hz(clk_sys)
#define MOTOR_WRAP 255
#define MOTOR_FREQ 10000  // 10 kHz
#define MOTOR_DIVIDER (SYS_FREQ / (MOTOR_FREQ * (MOTOR_WRAP + 1)))  // = 48.0

//servo init
#define SERVO_WRAP 19999
#define SERVO_DIVIDER 125.0f

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

#endif
