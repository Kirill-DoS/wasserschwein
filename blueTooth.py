import serial

# Настройки порта
# В Ubuntu Bluetooth-устройства обычно висят на /dev/rfcomm0
port = "/dev/rfcomm0" 
baudrate = 9600 # Убедитесь, что на роботе такая же скорость
command = ("M")
speed = (100)
try:
    # Инициализация соединения
    ser = serial.Serial(port, baudrate, timeout=1)
    print(f"Подключено к {port}")
    
    while True:
        # Отправка команды (например, 'F' - вперед)

        if command.lower() == 'exit':
            break
            
        # Кодируем строку в байты и отправляем
        ser.write(bytes([ord(command), speed]))
        
        # Если робот что-то отвечает, читаем:
     #    if ser.in_waiting > 0:
     #        response = ser.readline().decode('utf-8').strip()
     #        print(f"Робот ответил: {response}")

    ser.close()
    print("Соединение закрыто.")

except Exception as e:
    print(f"Ошибка: {e}")

