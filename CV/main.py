import cv2
import os
import time
import numpy as np
from BallTracker import BallTracker
from ColorCalibrate import ColorCalibrator
from Polygon import PolygonMarker

CamId = 1

def main():
    required_files = ['perimeter.npy', 'left_wall.npy', 'right_wall.npy', 'robot_beam.npy']
    if not all(os.path.exists(f) for f in required_files):
        print(" Файлы геометрии не найдены. Запуск разметки...")
        PolygonMarker().run()
    else:
        print("✅ Геометрия загружена.")

    print("🎨 Запуск калибровки цвета...")
    calibrator = ColorCalibrator(CamId)
    color_lower, color_upper = calibrator.calibrate()
    print(f" Цвет сохранён: lower={color_lower}, upper={color_upper}")

    # ⏱️ Пауза 0.5 сек, чтобы Windows гарантированно сняла блокировку с камеры
    print("⏳ Освобождение ресурса камеры...")
    time.sleep(0.5)

    tracker = BallTracker('perimeter.npy', 'left_wall.npy', 'right_wall.npy', 'robot_beam.npy')
    tracker.color_lower = color_lower
    tracker.color_upper = color_upper

    # 📷 Используем DirectShow для стабильности на Windows
    cap = cv2.VideoCapture(CamId, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ Не удалось открыть камеру после калибровки!")
        return
    
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("🚀 Система запущена. Нажми 'ESC' для выхода.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue  # Не прерываем цикл, просто ждём следующий кадр
            
        target, trajectory = tracker.get_prediction(frame)
        debug_frame = tracker.draw_debug(frame, trajectory)
        
        cv2.imshow("Arkanoid Vision", debug_frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()