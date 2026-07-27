#ifndef BT_CLIENT_H
#define BT_CLIENT_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/socket.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/rfcomm.h>

// Открывает RFCOMM-соединение с HC-06 по MAC-адресу и номеру канала.
int bluetooth_connect(const char *dest, uint8_t channel);
// Передаёт строковую команду роботу и возвращает число отправленных байтов.
int bluetooth_send(int sock, const char *message);
// Закрывает ранее открытый Bluetooth-сокет.
void bluetooth_disconnect(int sock);

#endif
