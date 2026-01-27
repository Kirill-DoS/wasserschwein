import serial

ser = serial.Serial('COM3', baudrate=9600, timeout=1)
ser.write(bytes([ord('M'), 200]))
data = ser.readline()
ser.close()