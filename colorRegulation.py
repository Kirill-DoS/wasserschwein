import cv2
import numpy as np
import os

# Файл для сохранения настроек
CONFIG_FILE = "textolite_hsv.npy"

def nothing(x): pass

# Загрузка старых настроек, если есть
if os.path.exists(CONFIG_FILE):
    initial_values = np.load(CONFIG_FILE)
else:
    # Дефолтные значения для текстолита (грязно-желтый)
    initial_values = [20, 50, 50, 40, 255, 255]

cv2.namedWindow("Trackbars")
cv2.resizeWindow("Trackbars", 400, 300)

# Создаем ползунки
cv2.createTrackbar("L-H", "Trackbars", initial_values[0], 180, nothing)
cv2.createTrackbar("L-S", "Trackbars", initial_values[1], 255, nothing)
cv2.createTrackbar("L-V", "Trackbars", initial_values[2], 255, nothing)
cv2.createTrackbar("U-H", "Trackbars", initial_values[3], 180, nothing)
cv2.createTrackbar("U-S", "Trackbars", initial_values[4], 255, nothing)
cv2.createTrackbar("U-V", "Trackbars", initial_values[5], 255, nothing)

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW) # Индекс 1 для твоей Logitech
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("Нажми 'S' для сохранения настроек и 'Q' для выхода.")

while True:
    ret, frame = cap.read()
    if not ret: break

    # Размытие для уменьшения шума (текстолит часто "шумит" из-за текстуры)
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Считываем значения
    lh = cv2.getTrackbarPos("L-H", "Trackbars")
    ls = cv2.getTrackbarPos("L-S", "Trackbars")
    lv = cv2.getTrackbarPos("L-V", "Trackbars")
    uh = cv2.getTrackbarPos("U-H", "Trackbars")
    us = cv2.getTrackbarPos("U-S", "Trackbars")
    uv = cv2.getTrackbarPos("U-V", "Trackbars")

    lower = np.array([lh, ls, lv])
    upper = np.array([uh, us, uv])

    mask = cv2.inRange(hsv, lower, upper)
    
    # Морфология (убираем мелкие точки и соединяем разрывы)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Показываем результат (оригинал и маска)
    result = cv2.bitwise_and(frame, frame, mask=mask)
    
    cv2.imshow("Original", frame)
    cv2.imshow("Mask", mask)
    cv2.imshow("Result (Filtered)", result)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    if key == ord('s'):
        values = [lh, ls, lv, uh, us, uv]
        np.save(CONFIG_FILE, values)
        print(f"Настройки сохранены в {CONFIG_FILE}!")

cap.release()
cv2.destroyAllWindows()
