#include "bt_client.h"

int bluetooth_connect(const char *dest, uint8_t channel) {
    struct sockaddr_rc addr = { 0 };
    int s, status;

    // Создание сокета RFCOMM
    s = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
    if (s < 0) {
        perror("Ошибка создания сокета");
        return -1;
    }

    // Параметры подключения
    addr.rc_family = AF_BLUETOOTH;
    addr.rc_channel = channel;
    str2ba(dest, &addr.rc_bdaddr); // Преобразование строки MAC в структуру

    // Соединение
    status = connect(s, (struct sockaddr *)&addr, sizeof(addr));
    if (status < 0) {
        perror("Ошибка подключения к HC-06");
        close(s);
        return -1;
    }

    return s;
}

int bluetooth_send(int sock, const char *message) {
    int bytes_sent = write(sock, message, strlen(message));
    if (bytes_sent < 0) {
        perror("Ошибка при отправке данных");
    }
    return bytes_sent;
}

void bluetooth_disconnect(int sock) {
    if (sock >= 0) {
        close(sock);
    }
}
