import cv2
import os
import time
import numpy as np
from BallTracker import BallTracker
from ColorCalibrate import ColorCalibrator
from Polygon import PolygonMarker
from Config import Config

camID = 1

def main():
    config = Config()
    required_files = ['perimeter.npy', 'left_wall.npy', 'right_wall.npy', 'robot_beam.npy']
    if not all(os.path.exists(f) for f in required_files):
        print("📐 Файлы геометрии не найдены. Запуск разметки...")
        PolygonMarker(camID).run()
    else:
        print("✅ Геометрия загружена.")

    print("🎨 Запуск калибровки цвета...")
    calibrator = ColorCalibrator(camID, config)
    color_lower, color_upper = calibrator.calibrate()
    print(f" Цвет: lower={color_lower}, upper={color_upper}")

    config.set_color_bounds(color_lower, color_upper)
    config.save()

    time.sleep(0.5)
    tracker = BallTracker('perimeter.npy', 'left_wall.npy', 'right_wall.npy', 'robot_beam.npy')
    tracker.color_lower = color_lower
    tracker.color_upper = color_upper

    physics = config.get_physics_params()
    tracker.curvature_k = physics.get("curvature_k", 0.08)
    tracker.friction = physics.get("friction", 0.006)
    tracker.restitution = physics.get("restitution", 0.82)

    cap = cv2.VideoCapture(camID)
    if not cap.isOpened():
        print("❌ Не удалось открыть камеру!")
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)

    for _ in range(5): cap.read()  # Сброс буфера

    last_frame_time = time.time()
    print("🚀 Система запущена. ESC для выхода.")

    while True:
        now = time.time()
        dt = now - last_frame_time
        last_frame_time = now
        if dt > 0.1: dt = 0.033

        ret, frame = cap.read()
        if not ret: break

        frame_small = cv2.resize(frame, (640, 360))
        scale_x, scale_y = frame.shape[1] / 640.0, frame.shape[0] / 360.0

        tracker.set_dt(dt)
        target, trajectory = tracker.get_prediction(frame_small)

        # Масштабируем траекторию под оригинальный кадр
        trajectory_scaled = [[int(p[0]*scale_x), int(p[1]*scale_y)] for p in trajectory]
        debug_frame = tracker.draw_debug(frame, trajectory_scaled, scale_x, scale_y)

        cv2.imshow("Arkanoid Vision", debug_frame)
        if cv2.waitKey(1) & 0xFF == 27: break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
