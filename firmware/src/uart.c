#include "uart.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

#include "arcanoid.h"
#include "constants.h"
#include "hardware/uart.h"
#include "pico/stdlib.h"

bool is_cmd_ready = false;
int uart_idx = 0;
char uart_buf[MAX_SIZE] = {0};
static bool command_overflow = false;
static uint64_t last_valid_command_us = 0;
static bool watchdog_has_stopped = false;

// Запоминает время последней корректной команды для независимой защиты от потери связи.
static void mark_valid_command(void) {
    last_valid_command_us = time_us_64();
    watchdog_has_stopped = false;
}

// Завершает команду ошибкой и переводит каретку в торможение.
static void reject_command(const char *message) {
    drive(0);
    uart_puts(UART_ID, message);
    clear_buf();
}

// Считывает доступные байты UART до полной команды, оканчивающейся переводом строки.
void get_uart_buf(void) {
    while (uart_is_readable(UART_ID) && !is_cmd_ready) {
        char character = uart_getc(UART_ID);
        if (character == '\r') {
            continue;
        }
        if (character == '\n') {
            if (command_overflow || uart_idx == 0) {
                reject_command("ERR command too long or empty\n");
                command_overflow = false;
                continue;
            }
            uart_buf[uart_idx] = '\0';
            is_cmd_ready = true;
            return;
        }
        if (uart_idx >= MAX_SIZE - 1) {
            command_overflow = true;
            continue;
        }
        uart_buf[uart_idx++] = character;
    }
}

// Выводит принятую команду в UART для ручной диагностики.
void print_uart_buf(void) {
    uart_puts(UART_ID, "UART buffer: ");
    uart_puts(UART_ID, uart_buf);
    uart_puts(UART_ID, "\n");
}

// Преобразует числовую часть команды и убеждается, что после неё нет лишних символов.
static bool parse_value(const char *text, int *value) {
    char *end_ptr;
    while (isspace((unsigned char)*text)) {
        text++;
    }
    if (*text == '\0') {
        return false;
    }

    long parsed = strtol(text, &end_ptr, 10);
    while (isspace((unsigned char)*end_ptr)) {
        end_ptr++;
    }
    if (*end_ptr != '\0' || parsed < -2147483647L || parsed > 2147483647L) {
        return false;
    }
    *value = (int)parsed;
    return true;
}

// Проверяет и выполняет принятую текстовую команду F/B/L/R/S.
void parse_uart_buf(void) {
    char command = (char)toupper((unsigned char)uart_buf[0]);
    int value = 0;

    if (command == 'S' && uart_buf[1] == '\0') {
        drive(0);
        esc_set_speed(MIN_PULSE, SERVO1);
        esc_set_speed(MIN_PULSE, SERVO2);
        mark_valid_command();
        uart_puts(UART_ID, "OK stop\n");
        return;
    }

    if (!parse_value(&uart_buf[1], &value)) {
        reject_command("ERR invalid value\n");
        return;
    }

    switch (command) {
        case 'F':
            if (value < 0 || value > MAX_VEL) {
                reject_command("ERR motor range 0..255\n");
                return;
            }
            drive(value);
            break;
        case 'B':
            if (value < 0 || value > MAX_VEL) {
                reject_command("ERR motor range 0..255\n");
                return;
            }
            drive(-value);
            break;
        case 'L':
            if (value < MIN_PULSE || value > MAX_PULSE) {
                reject_command("ERR ESC range 1000..2000\n");
                return;
            }
            esc_set_speed((uint)value, SERVO2);
            break;
        case 'R':
            if (value < MIN_PULSE || value > MAX_PULSE) {
                reject_command("ERR ESC range 1000..2000\n");
                return;
            }
            esc_set_speed((uint)value, SERVO1);
            break;
        default:
            reject_command("ERR unknown command\n");
            return;
    }

    mark_valid_command();
    uart_puts(UART_ID, "OK\n");
}

// Останавливает каретку, если допустимая команда давно не приходила.
void uart_safety_watchdog(void) {
    if (last_valid_command_us == 0 || watchdog_has_stopped) {
        return;
    }
    if (time_us_64() - last_valid_command_us > (uint64_t)COMMAND_TIMEOUT_MS * 1000u) {
        drive(0);
        watchdog_has_stopped = true;
        uart_puts(UART_ID, "SAFE STOP: command timeout\n");
    }
}
