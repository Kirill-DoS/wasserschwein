import cv2
import os
import numpy as np

# Импортируем твои классы из файлов в папке CV
from BallTracker import BallTracker
from ColorCalibrate import ColorCalibrator
from Polygon import PolygonMarker

def main():
    # 1. Список необходимых файлов .npy
    required_files = [
        'perimeter.npy', 
        'left_wall.npy', 
        'right_wall.npy', 
        'robot_beam.npy'
    ]
    
    # Проверяем наличие ВСЕХ файлов
    files_exist = all(os.path.exists(f) for f in required_files)

    if not files_exist:
        print("Файлы геометрии не найдены. Запуск разметки полигона...")
        marker = PolygonMarker()
        # Предполагаем, что внутри Polygon.py есть метод run(), 
        # который открывает камеру, дает разметить и сохраняет файлы
        marker.run() 
    else:
        print("Геометрия загружена успешно.")

    # 2. Запуск калибровки цвета
    # Создаем объект калибровщика. Он должен вернуть lower и upper границы HSV
    calibrator = ColorCalibrator(camera_index=0)
    color_lower, color_upper = calibrator.calibrate()
    print(f"Цвет мяча откалиброван: {color_lower} -> {color_upper}")

    # 3. Инициализация и запуск BallTracker
    # Передаем пути к файлам и настроенные цвета
    tracker = BallTracker(
        homography_path='perimeter.npy',
        wall_l_path='left_wall.npy',
        wall_r_path='right_wall.npy',
        beam_path='robot_beam.npy'
    )
    
    # Устанавливаем цвета, которые получили на шаге 2
    tracker.color_lower = color_lower
    tracker.color_upper = color_upper

    # Основной цикл работы
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 120) # Устанавливаем 60 FPS для C922

    print("Система запущена. Нажми 'ESC' для выхода.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Получаем данные: точка пересечения с балкой и точки траектории для рисования
        target_point, trajectory = tracker.get_prediction(frame)
        
        # Отрисовка (N точек зеленая линия, прогноз - синяя)
        processed_frame = tracker.draw_debug(frame, trajectory)
        
        cv2.imshow("Arkanoid Vision System", processed_frame)

        # Выход на ESC
        if cv2.waitKey(10) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
