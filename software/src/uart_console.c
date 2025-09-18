#include <stdio.h>
#include "pico/stdlib.h"

int main() {
    const int clk_sys = 125000000;
    // Инициализация USB serial
    stdio_init_all();
    
    // Ждем подключения serial
    sleep_ms(2000);
    
    printf("RP2040 Zero Console Started!\r\n");
    
    while (true) {
        printf("Hello rp2040 zero");

        sleep_ms(1000);
    }
    
    return 0;
}