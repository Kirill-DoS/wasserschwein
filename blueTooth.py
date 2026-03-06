import serial
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
     print(f"Порт: {port.device}, Описание: {port.description}")
     
ser = serial.Serial("COM3", 9600)


# Send character 'S' to start the program
ser.write(bytes([ord('M'), 200]))
# ser.write('M200')
# # Read line   
# while True:
#     bs = ser.readline()
#     print(bs)



