#ifndef BT_CLIENT_H
#define BT_CLIENT_H

#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/rfcomm.h>

int bluetooth_connect(const char *dest, uint8_t channel);
int bluetooth_send(int sock, const char *message);
void bluetooth_disconnect(int sock);

#endif
