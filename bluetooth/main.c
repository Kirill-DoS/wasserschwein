#include "bt_client.h"
#include <stdio.h>

int main() {
    // ЗАМЕНИТЕ на ваш реальный MAC-адрес модуля HC-06
    const char *hc06_addr = "98:D3:11:FD:1C:0B";
    char *str;
    int sock = bluetooth_connect(hc06_addr, 1);
    if (sock < 0) return 1;

    printf("Подключено к %s\n", hc06_addr);

    scanf("%s", str);

    // Отправка команды
    bluetooth_send(sock, str);


    return 0;
}
