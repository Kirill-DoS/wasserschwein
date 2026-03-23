import cv2
import numpy as np
import os
import math
from collections import deque

class BallTracker:
    """
    Класс для отслеживания мяча и определения координат для робота
    
    Основные функции:
    - Отслеживание мяча по цвету
    - Калибровка игрового поля
    - Фильтрация координат с помощью Калмана
    - Предсказание будущего положения мяча
    - Получение текущих и целевых координат для робота
    """
    
    def __init__(self, real_width=150.0, real_height=150.0, robot_pos=(30, 50), 
                 predict_dist=10.0, history_len=30, process_noise=1.2, measure_noise=0.01):
        """
        Инициализация трекера мяча
        
        Args:
            real_width: реальная ширина поля в см
            real_height: реальная высота поля в см
            robot_pos: позиция робота в см (x, y)
            predict_dist: расстояние предсказания в см
            history_len: длина истории траектории
            process_noise: шум процесса для фильтра Калмана
            measure_noise: шум измерения для фильтра Калмана
        """
        # Параметры поля
        self.real_w = real_width
        self.real_h = real_height
        self.robot_pos = robot_pos
        self.predict_dist = predict_dist
        self.history_len = history_len
        
        # Калибровка
        self.calib_file = "calibration.npy"
        self.calib_points = []
        self.M = None  # Матрица прямого преобразования (пиксели -> см)
        self.M_inv = None  # Обратная матрица (см -> пиксели)
        
        # Данные отслеживания
        self.pts_history = deque(maxlen=history_len)
        self.current_pos = None  # Текущие координаты мяча (см)
        self.current_speed = 0.0  # Текущая скорость (см/кадр)
        self.predicted_pos = None  # Предсказанная позиция (см)
        self.target_pos = None  # Целевая позиция для робота (см)
        
        # Флаги
        self.is_calibrated = False
        self.ball_detected = False
        
        # Загрузка калибровки
        self._load_calibration()
        
        # Инициализация фильтра Калмана
        self._init_kalman_filter(process_noise, measure_noise)
        
    def _init_kalman_filter(self, process_noise, measure_noise):
        """Инициализация фильтра Калмана"""
        self.kalman = cv2.KalmanFilter(4, 2)
        self.kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        self.kalman.transitionMatrix = np.array([[1, 0, 1, 0], 
                                                   [0, 1, 0, 1], 
                                                   [0, 0, 1, 0], 
                                                   [0, 0, 0, 1]], np.float32)
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * process_noise
        self.kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * measure_noise
        
    def _load_calibration(self):
        """Загрузка калибровки из файла"""
        if os.path.exists(self.calib_file):
            self.M = np.load(self.calib_file)
            self.M_inv = np.linalg.inv(self.M)
            self.is_calibrated = True
            
    def calibrate(self, points):
        """
        Калибровка поля по 4 углам
        
        Args:
            points: список из 4 точек (x, y) в пикселях в порядке: 
                   верхний-левый, верхний-правый, нижний-правый, нижний-левый
        """
        if len(points) != 4:
            raise ValueError("Необходимо 4 точки для калибровки")
            
        self.calib_points = points
        pts_src = np.array(points, dtype=np.float32)
        pts_dst = np.array([[0, 0], [self.real_w, 0], 
                           [self.real_w, self.real_h], [0, self.real_h]], dtype=np.float32)
        self.M = cv2.getPerspectiveTransform(pts_src, pts_dst)
        self.M_inv = np.linalg.inv(self.M)
        self.is_calibrated = True
        
        # Сохраняем калибровку
        np.save(self.calib_file, self.M)
        
    def reset_calibration(self):
        """Сброс калибровки"""
        self.M = None
        self.M_inv = None
        self.calib_points = []
        self.is_calibrated = False
        if os.path.exists(self.calib_file):
            os.remove(self.calib_file)
            
    def _pixel_to_cm(self, px, py):
        """Преобразование пикселей в сантиметры"""
        if self.M is None:
            return None, None
            
        p = np.array([[[px, py]]], dtype=np.float32)
        t = cv2.perspectiveTransform(p, self.M)
        rx, ry = t[0][0][0], t[0][0][1]
        
        # Коррекция высоты (опционально)
        current_h = 190.0 if 90.0 <= rx <= 110.0 else 200.0
        ratio = current_h / 200.0
        return 100.0 + (rx - 100.0) * ratio, 100.0 + (ry - 100.0) * ratio
        
    def _cm_to_pixel(self, rx_cm, ry_cm):
        """Преобразование сантиметров в пиксели (для визуализации)"""
        if self.M_inv is None:
            return None, None
            
        p = np.array([[[rx_cm, ry_cm]]], dtype=np.float32)
        t = cv2.perspectiveTransform(p, self.M_inv)
        return int(t[0][0][0]), int(t[0][0][1])
        
    def update(self, frame, color_hsv_range=None):
        """
        Обновление позиции мяча на новом кадре
        
        Args:
            frame: кадр из камеры (BGR)
            color_hsv_range: словарь с диапазонами HSV {'low': (h,s,v), 'high': (h,s,v)}
                             если None, использует стандартный оранжевый диапазон
        
        Returns:
            bool: обнаружен ли мяч на кадре
        """
        if not self.is_calibrated:
            self.ball_detected = False
            return False
            
        # Определяем диапазон HSV
        if color_hsv_range is None:
            # Стандартный оранжевый диапазон
            low_hsv = np.array([3, 139, 120])
            high_hsv = np.array([13, 255, 255])
        else:
            low_hsv = np.array(color_hsv_range['low'])
            high_hsv = np.array(color_hsv_range['high'])
            
        # Преобразуем в HSV и создаем маску
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, low_hsv, high_hsv)
        
        # Находим контуры
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not cnts:
            self.ball_detected = False
            return False
            
        # Берем самый большой контур
        c = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(c)
        
        if area < 30:  # Минимальная площадь контура
            self.ball_detected = False
            return False
            
        # Находим центр контура
        M_mom = cv2.moments(c)
        cx_px = int(M_mom["m10"] / M_mom["m00"])
        cy_px = int(M_mom["m01"] / M_mom["m00"])
        
        # Получаем сырые координаты в см
        rx_raw, ry_raw = self._pixel_to_cm(cx_px, cy_px)
        
        if rx_raw is None:
            self.ball_detected = False
            return False
            
        # Применяем фильтр Калмана
        self.kalman.correct(np.array([[np.float32(rx_raw)], [np.float32(ry_raw)]], np.float32))
        state = self.kalman.predict()
        
        # Сохраняем текущие координаты (сглаженные)
        self.current_pos = (float(state[0][0]), float(state[1][0]))
        self.current_speed = math.sqrt(float(state[2][0])**2 + float(state[3][0])**2)
        
        # Предсказываем будущее положение
        vx, vy = float(state[2][0]), float(state[3][0])
        if self.current_speed > 2.0:  # Если мяч движется достаточно быстро
            norm_vx, norm_vy = vx / self.current_speed, vy / self.current_speed
            px_cm = self.current_pos[0] + norm_vx * self.predict_dist
            py_cm = self.current_pos[1] + norm_vy * self.predict_dist
            self.predicted_pos = (px_cm, py_cm)
        else:
            self.predicted_pos = self.current_pos
            
        # Определяем целевую позицию для робота
        self._update_target_pos()
        
        # Сохраняем историю (в пикселях для визуализации)
        self.pts_history.appendleft((cx_px, cy_px))
        
        self.ball_detected = True
        return True
        
    def _update_target_pos(self):
        """
        Определение целевой позиции для робота
        Использует адаптивный порог: чем ближе мяч к роботу, тем чаще обновляется цель
        """
        if self.current_pos is None:
            return
            
        # Вычисляем расстояние от мяча до робота
        dist_to_robot = math.sqrt((self.current_pos[0] - self.robot_pos[0])**2 + 
                                  (self.current_pos[1] - self.robot_pos[1])**2)
        
        # Определяем порог срабатывания в зависимости от расстояния
        if dist_to_robot >= 120:
            threshold = 20
        elif 50 <= dist_to_robot < 120:
            threshold = 10
        elif 20 <= dist_to_robot < 50:
            threshold = 5
        else:
            threshold = 2
            
        # Если целевая позиция еще не определена, инициализируем
        if self.target_pos is None:
            self.target_pos = self.current_pos
            self._last_sent_pos = self.current_pos
            return
            
        # Вычисляем, насколько переместился мяч с последней отправки
        move_delta = math.sqrt((self.current_pos[0] - self._last_sent_pos[0])**2 + 
                              (self.current_pos[1] - self._last_sent_pos[1])**2)
        
        # Если мяч прошел достаточное расстояние, обновляем цель
        if move_delta >= threshold:
            # Используем предсказанную позицию для более точного наведения
            if self.predicted_pos:
                self.target_pos = self.predicted_pos
            else:
                self.target_pos = self.current_pos
            self._last_sent_pos = self.current_pos
            
    def get_current_position(self):
        """
        Получить текущие координаты мяча
        
        Returns:
            tuple: (x, y) в сантиметрах или None если мяч не обнаружен
        """
        return self.current_pos if self.ball_detected else None
        
    def get_target_position(self):
        """
        Получить целевую позицию для робота (куда двигаться)
        
        Returns:
            tuple: (x, y) в сантиметрах или None если мяч не обнаружен
        """
        return self.target_pos if self.ball_detected else None
        
    def get_predicted_position(self):
        """
        Получить предсказанную позицию мяча
        
        Returns:
            tuple: (x, y) в сантиметрах или None если мяч не обнаружен
        """
        return self.predicted_pos if self.ball_detected else None
        
    def get_speed(self):
        """
        Получить текущую скорость мяча
        
        Returns:
            float: скорость в см/кадр
        """
        return self.current_speed if self.ball_detected else 0.0
        
    def get_distance_to_robot(self):
        """
        Получить расстояние от мяча до робота
        
        Returns:
            float: расстояние в см или None если мяч не обнаружен
        """
        if not self.ball_detected or self.current_pos is None:
            return None
        return math.sqrt((self.current_pos[0] - self.robot_pos[0])**2 + 
                        (self.current_pos[1] - self.robot_pos[1])**2)
        
    def draw_debug_info(self, frame):
        """
        Отрисовка отладочной информации на кадре
        
        Args:
            frame: кадр для отрисовки
            
        Returns:
            frame: кадр с отрисованной информацией
        """
        if not self.is_calibrated:
            cv2.putText(frame, f"CALIBRATION NEEDED: {len(self.calib_points)}/4 points", 
                       (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            for p in self.calib_points:
                cv2.circle(frame, tuple(p), 6, (0, 0, 255), -1)
            return frame
            
        if not self.ball_detected:
            return frame
            
        # Конвертируем координаты в пиксели
        cx_px, cy_px = self._cm_to_pixel(self.current_pos[0], self.current_pos[1])
        
        if cx_px is None:
            return frame
            
        # Рисуем историю траектории (зеленый хвост)
        for i in range(1, len(self.pts_history)):
            cv2.line(frame, self.pts_history[i-1], self.pts_history[i], (0, 255, 0), 2)
            
        # Рисуем текущую позицию мяча
        cv2.circle(frame, (cx_px, cy_px), 8, (0, 0, 255), -1)
        
        # Рисуем предсказанную позицию
        if self.predicted_pos:
            px_cm, py_cm = self._cm_to_pixel(self.predicted_pos[0], self.predicted_pos[1])
            cv2.circle(frame, (px_cm, py_cm), 5, (255, 0, 0), -1)
            cv2.line(frame, (cx_px, cy_px), (px_cm, py_cm), (255, 0, 0), 2)
            
        # Рисуем целевую позицию для робота
        if self.target_pos:
            tx_px, ty_px = self._cm_to_pixel(self.target_pos[0], self.target_pos[1])
            cv2.circle(frame, (tx_px, ty_px), 10, (0, 255, 255), 2)
            
        # Рисуем позицию робота
        rx_px, ry_px = self._cm_to_pixel(self.robot_pos[0], self.robot_pos[1])
        cv2.circle(frame, (rx_px, ry_px), 12, (255, 0, 255), -1)
        
        # Добавляем текстовую информацию
        info_text = [
            f"Ball: {self.current_pos[0]:.1f}, {self.current_pos[1]:.1f} cm",
            f"Speed: {self.current_speed:.1f} cm/frame",
            f"Target: {self.target_pos[0]:.1f}, {self.target_pos[1]:.1f} cm",
            f"Dist to robot: {self.get_distance_to_robot():.1f} cm"
        ]
        
        for i, text in enumerate(info_text):
            cv2.putText(frame, text, (10, 30 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
        return frame
        
    def set_robot_position(self, x, y):
        """
        Установить позицию робота
        
        Args:
            x: координата X в см
            y: координата Y в см
        """
        self.robot_pos = (x, y)
        # Сбрасываем целевую позицию при перемещении робота
        self.target_pos = None
        
    def set_predict_distance(self, distance):
        """
        Установить расстояние предсказания
        
        Args:
            distance: расстояние в см
        """
        self.predict_dist = distance