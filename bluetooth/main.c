#include "bt_client.h"

#include <stdio.h>
#include <string.h>

// Подключается к HC-06 и передаёт одну введённую оператором команду с переводом строки.
int main(void) {
    const char *hc06_addr = "98:D3:11:FD:1C:0B";
    char command[32] = {0};
    int socket_fd = bluetooth_connect(hc06_addr, 1);
    if (socket_fd < 0) {
        return 1;
    }

    printf("Подключено к %s. Введите, например, F 100 или S: ", hc06_addr);
    if (fgets(command, sizeof(command), stdin) == NULL) {
        bluetooth_disconnect(socket_fd);
        return 1;
    }
    size_t command_length = strlen(command);
    if (command_length == 0 || command[command_length - 1] != '\n') {
        if (command_length >= sizeof(command) - 1) {
            fprintf(stderr, "Команда слишком длинная\n");
            bluetooth_disconnect(socket_fd);
            return 1;
        }
        command[command_length++] = '\n';
        command[command_length] = '\0';
    }

    int result = bluetooth_send(socket_fd, command);
    bluetooth_disconnect(socket_fd);
    return result < 0 ? 1 : 0;
}
