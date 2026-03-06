import cv2
import numpy as np
import os
import math
from collections import deque

# --- НАСТРОЙКИ ---
REAL_W, REAL_H = 150.0, 150.0
CALIB_FILE = "calibration.npy"
ROBOT_POS = (30, 50) 
PREDICT_DIST = 10.0  
HISTORY_LEN = 30     

# Инициализация переменных до цикла
calib_points = []
matrix_M = None
last_sent_pos = None
pts_history = deque(maxlen=HISTORY_LEN) # Добавили инициализацию хвоста

# Настройки Калмана для РЕЗКОСТИ
PROCESS_NOISE = 1.2  # Еще чуть выше для мгновенной реакции
MEASURE_NOISE = 0.01 

kalman = cv2.KalmanFilter(4, 2)
kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
kalman.processNoiseCov = np.eye(4, dtype=np.float32) * PROCESS_NOISE
kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * MEASURE_NOISE


def nothing(x): pass

def mouse_callback(event, x, y, flags, param):
    global calib_points, matrix_M
    if event == cv2.EVENT_LBUTTONDOWN and len(calib_points) < 4:
        calib_points.append([x, y])
        if len(calib_points) == 4:
            pts_src = np.array(calib_points, dtype=np.float32)
            pts_dst = np.array([[0, 0], [REAL_W, 0], [REAL_W, REAL_H], [0, REAL_H]], dtype=np.float32)
            matrix_M = cv2.getPerspectiveTransform(pts_src, pts_dst)
            np.save(CALIB_FILE, matrix_M)

def get_real_coords(px, py, M):
    p = np.array([[[px, py]]], dtype=np.float32)
    t = cv2.perspectiveTransform(p, M)
    rx, ry = t[0][0][0], t[0][0][1]
    current_h = 190.0 if 90.0 <= rx <= 110.0 else 200.0
    ratio = current_h / 200.0
    return 100.0 + (rx - 100.0) * ratio, 100.0 + (ry - 100.0) * ratio

def get_pixel_coords(rx_cm, ry_cm, M_inv):
    """Обратное преобразование: из СМ в ПИКСЕЛИ для отрисовки"""
    p = np.array([[[rx_cm, ry_cm]]], dtype=np.float32)
    t = cv2.perspectiveTransform(p, M_inv)
    return int(t[0][0][0]), int(t[0][0][1])

if os.path.exists(CALIB_FILE):
    matrix_M = np.load(CALIB_FILE)

prev_rx, prev_ry = None, None

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

cv2.namedWindow("Main Frame")
cv2.setMouseCallback("Main Frame", mouse_callback)
cv2.namedWindow("Settings")
cv2.createTrackbar("Ball_L_H", "Settings", 3, 180, nothing)
cv2.createTrackbar("Ball_L_S", "Settings", 139, 255, nothing)
cv2.createTrackbar("Ball_L_V", "Settings", 120, 255, nothing)
cv2.createTrackbar("Ball_U_H", "Settings", 13, 180, nothing)

while True:
    ret, frame = cap.read()
    if not ret: break
    
    if matrix_M is None:
        cv2.putText(frame, f"CLICK 4 CORNERS: {len(calib_points)}/4", (50, 80), 0, 1, (0,0,255), 2)
        for p in calib_points: cv2.circle(frame, tuple(p), 6, (0,0,255), -1)
    else:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([cv2.getTrackbarPos("Ball_L_H", "Settings"), 139, 120]), 
                               np.array([cv2.getTrackbarPos("Ball_U_H", "Settings"), 255, 255]))
        
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(c) > 30:
                M_mom = cv2.moments(c)
                cx_px, cy_px = int(M_mom["m10"]/M_mom["m00"]), int(M_mom["m01"]/M_mom["m00"])
                
                # 1. Получаем "сырые" см и кормим Калману
                rx_raw, ry_raw = get_real_coords(cx_px, cy_px, matrix_M)
                kalman.correct(np.array([[np.float32(rx_raw)], [np.float32(ry_raw)]], np.float32))
                
                # 2. Извлекаем данные из предсказания Калмана
                state = kalman.predict()
                rx, ry = float(state[0][0]), float(state[1][0]) # Сглаженные X и Y
                vx, vy = float(state[2][0]), float(state[3][0]) # Скорости VX и VY
                
                # 3. Расчет вектора предсказания
                speed = math.sqrt(vx**2 + vy**2)
                if speed > 2.0: # Порог срабатывания линии (см/кадр)
                    norm_vx, norm_vy = vx/speed, vy/speed
                    px_cm, py_cm = rx + norm_vx * PREDICT_DIST, ry + norm_vy * PREDICT_DIST
                    
                    # Обратный перевод в пиксели для рисования
                    M_inv = np.linalg.inv(matrix_M)
                    p_point = np.array([[[px_cm, py_cm]]], dtype=np.float32)
                    t_px = cv2.perspectiveTransform(p_point, M_inv)
                    ppx, ppy = int(t_px[0][0][0]), int(t_px[0][0][1])
                    
                    cv2.line(frame, (cx_px, cy_px), (ppx, ppy), (255, 0, 0), 3)
                    cv2.circle(frame, (ppx, ppy), 5, (255, 0, 0), -1)

                # 4. Отрисовка хвоста (теперь pts_history инициализирован)
                pts_history.appendleft((cx_px, cy_px))
                for i in range(1, len(pts_history)):
                    cv2.line(frame, pts_history[i-1], pts_history[i], (0, 255, 0), 2)
                    
                cv2.putText(frame, f"Real: {rx:.1f}, {ry:.1f} cm", (cx_px, cy_px-20), 0, 0.6, (0,255,0), 2)

            # --- БЛОК ЛОГИКИ ОТПРАВКИ КОРРЕКТИРОВКИ ---
        # Считаем расстояние от мяча до робота
        dist_to_robot = math.sqrt((rx - ROBOT_POS[0])**2 + (ry - ROBOT_POS[1])**2)

        # 1. Определяем порог срабатывания (твоя "экспонента")
        if dist_to_robot >= 120:
            threshold = 20
        elif 50 <= dist_to_robot < 120:
            threshold = 10
        elif 20 <= dist_to_robot < 50:
            threshold = 5
        else:
            threshold = 2 # Очень близко — шлем почти постоянно

        # 2. Проверяем, нужно ли отправлять данные
        if last_sent_pos is None:
            # Самая первая отправка при обнаружении мяча
            print(f"FIRST_DETECT: X={rx:.1f}, Y={ry:.1f}")
            last_sent_pos = (rx, ry)
        else:
            # Считаем, сколько реально прошел мяч с момента последней отправки
            move_delta = math.sqrt((rx - last_sent_pos[0])**2 + (ry - last_sent_pos[1])**2)
            
            if move_delta >= threshold:
                # ВОТ ЗДЕСЬ ПРОИСХОДИТ ОТПРАВКА
                print(f"CORRECTION: X={rx:.1f}, Y={ry:.1f} | DistToRobot={dist_to_robot:.1f} | Thr={threshold}")
                
                # Обновляем последнюю отправленную позицию
                last_sent_pos = (rx, ry)
                
    cv2.imshow("Main Frame", frame)
    key = cv2.waitKey(1)
    if key == ord('q'): break
    if key == ord('r'):
        matrix_M = None
        calib_points = []
        if os.path.exists(CALIB_FILE): os.remove(CALIB_FILE)

cap.release()
cv2.destroyAllWindows()