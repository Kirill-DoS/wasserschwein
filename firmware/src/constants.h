#ifndef CONSTANTS_H
#define CONSTANTS_H
#include "hardware/clocks.h"
#include "generated_env.h"


//motor constants
#define SYS_FREQ clock_get_hz(clk_sys)
#define MOTOR_WRAP CFG_PICO_MOTOR_WRAP
#define MOTOR_FREQ CFG_PICO_MOTOR_FREQ_HZ
#define MOTOR_DIVIDER (SYS_FREQ / (MOTOR_FREQ * (MOTOR_WRAP + 1)))  // = 48.0
// for trapezoid acceleratoin
#define a_max 1.5
#define m_robot 700 // gramms
#define MAX_VEL CFG_MOTOR_MAX_PWM

//servo init
#define SERVO_WRAP CFG_PICO_SERVO_WRAP
#define SERVO_DIVIDER CFG_PICO_SERVO_DIVIDER
#define MAX_PULSE CFG_PICO_ESC_MAX_PULSE
#define ESC1_TARGET_PULSE CFG_PICO_ESC1_TARGET_PULSE
#define ESC2_TARGET_PULSE CFG_PICO_ESC2_TARGET_PULSE
#define MIN_PULSE CFG_PICO_ESC_MIN_PULSE
#define CALIBRATE_ESC_ON_BOOT CFG_PICO_CALIBRATE_ESC_ON_BOOT

// Защита от зависания компьютера или обрыва Bluetooth: мотор тормозит без новой команды.
#define COMMAND_TIMEOUT_MS CFG_PICO_COMMAND_TIMEOUT_MS

//pins
#define UART_ID uart0
#define BAUDRATE CFG_PICO_UART_BAUDRATE
#define TX CFG_PICO_PIN_TX
#define RX CFG_PICO_PIN_RX
#define LED CFG_PICO_PIN_LED
#define SERVO1 CFG_PICO_PIN_SERVO1
#define SERVO2 CFG_PICO_PIN_SERVO2
#define L CFG_PICO_PIN_MOTOR_LEFT
#define R CFG_PICO_PIN_MOTOR_RIGHT
#define BAT CFG_PICO_PIN_BATTERY
#define BUTTON CFG_PICO_PIN_BUTTON

#endif
