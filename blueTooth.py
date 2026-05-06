import serial
import time

# ==================== НАСТРОЙКИ ====================
port = "/dev/rfcomm0"      # Bluetooth-порт в Ubuntu
baudrate = 9600            # Скорость (должна совпадать с роботом)
command = "F"              # Команда: F-вперед, B-назад, L-влево, R-вправо, S-стоп
speed = 100                # Скорость 0-255
# ==================================================

try:
    # Открываем соединение
    ser = serial.Serial(port, baudrate, timeout=1)
    print(f"✓ Подключено к {port}")
    print(f"✓ Скорость: {baudrate} бод")
    print("Нажмите Ctrl+C для выхода\n")

    while True:
        # Формируем строку команды (как в телефоне: "F100")
        message = f"{command}{speed}"

        # Отправляем как строку (байты ASCII)
        ser.write(message.encode())

        print(f"→ Отправлено: '{message}' (байты: {list(message.encode())})")

        # Ждем ответа от робота (если есть)
        time.sleep(0.1)  # Небольшая задержка для ответа

        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(f"← Ответ робота: '{response}'")

        # Пауза между командами (чтобы не завалить робота)
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n✗ Остановлено пользователем (Ctrl+C)")

except serial.SerialException as e:
    print(f"\n✗ Ошибка порта: {e}")
    print("Проверьте:")
    print("  - Включен ли Bluetooth на роботе")
    print("  - Правильный ли порт (проверьте: ls /dev/rfcomm*)")
    print("  - Подключены ли вы: sudo rfcomm bind 0 XX:XX:XX:XX:XX:XX")

except Exception as e:
    print(f"\n✗ Ошибка: {e}")

finally:
    # Закрываем порт при любом выходе
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("✓ Соединение закрыто")
