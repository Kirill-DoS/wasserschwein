#include "bt_client.h"

#include <string.h>
#include <unistd.h>

// Открывает RFCOMM-соединение с HC-06 по MAC-адресу и номеру канала.
int bluetooth_connect(const char *dest, uint8_t channel) {
    struct sockaddr_rc addr = {0};
    int socket_fd = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (socket_fd < 0) {
        perror("Ошибка создания Bluetooth-сокета");
        return -1;
    }

    addr.rc_family = AF_BLUETOOTH;
    addr.rc_channel = channel;
    str2ba(dest, &addr.rc_bdaddr);
    if (connect(socket_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("Ошибка подключения к HC-06");
        close(socket_fd);
        return -1;
    }
    return socket_fd;
}

// Передаёт строковую команду роботу и возвращает число отправленных байтов.
int bluetooth_send(int socket_fd, const char *message) {
    int bytes_sent = (int)write(socket_fd, message, strlen(message));
    if (bytes_sent < 0) {
        perror("Ошибка при отправке данных");
    }
    return bytes_sent;
}

// Закрывает ранее открытый Bluetooth-сокет.
void bluetooth_disconnect(int socket_fd) {
    if (socket_fd >= 0) {
        close(socket_fd);
    }
}
