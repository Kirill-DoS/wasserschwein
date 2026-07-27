import argparse

import serial


# Проверяет команду оператора и формирует строку, которую понимает прошивка Pico.
def build_command(command, value=None):
    command = command.upper()
    if command == "S" and value is None:
        return "S\n"
    if command in {"F", "B"} and value is not None and 0 <= value <= 255:
        return f"{command} {value}\n"
    if command in {"L", "R"} and value is not None and 1000 <= value <= 2000:
        return f"{command} {value}\n"
    raise ValueError("Допустимы S, F/B 0..255 и L/R 1000..2000")


# Открывает Bluetooth-порт, отправляет одну команду и печатает короткий ответ контроллера.
def send_manual_command(port, baudrate, command, value):
    message = build_command(command, value)
    with serial.Serial(port, baudrate, timeout=1) as serial_port:
        serial_port.write(message.encode("ascii"))
        response = serial_port.readline().decode("utf-8", errors="replace").strip()
    print(f"→ {message.strip()}")
    if response:
        print(f"← {response}")


# Разбирает аргументы командной строки для безопасной ручной проверки связи с роботом.
def main():
    parser = argparse.ArgumentParser(description="Отправка одной команды роботу по Bluetooth")
    parser.add_argument("command", choices=("F", "B", "L", "R", "S"))
    parser.add_argument("value", nargs="?", type=int)
    parser.add_argument("--port", default="/dev/rfcomm0")
    parser.add_argument("--baudrate", default=9600, type=int)
    args = parser.parse_args()
    send_manual_command(args.port, args.baudrate, args.command, args.value)


if __name__ == "__main__":
    main()
