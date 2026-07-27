import time

import cv2
import numpy as np


class BallTracker:
    # Загружает геометрию поля, настраивает фильтр движения и параметры прогноза мяча.
    def __init__(
        self,
        homography_path,
        wall_l_path,
        wall_r_path,
        beam_path,
        detection_timeout_s,
        field_size_mm,
        virtual_field_size,
        physics_params,
        tracker_params,
        color_lower,
        color_upper,
    ):
        self.M = np.load(homography_path)
        self.M_inv = np.linalg.inv(self.M)
        self.scale_mm = np.array(
            [field_size_mm[0] / virtual_field_size[0], field_size_mm[1] / virtual_field_size[1]],
            dtype=np.float32,
        )

        self.wall_l_mm = self._px_to_mm(np.load(wall_l_path))
        self.wall_r_mm = self._px_to_mm(np.load(wall_r_path))
        self.beam_mm = self._px_to_mm(np.load(beam_path))
        self.wall_l_x = float(np.min(self.wall_l_mm[:, 0]))
        self.wall_r_x = float(np.max(self.wall_r_mm[:, 0]))
        self.center_x = (self.wall_l_x + self.wall_r_x) / 2.0
        self.center_y = float(
            (np.min(self.wall_l_mm[:, 1]) + np.max(self.wall_r_mm[:, 1])) / 2.0
        )
        self.beam_y_mm = float(np.mean(self.beam_mm[:, 1]))

        self.curvature_k = float(physics_params["curvature_k"])
        self.friction = float(physics_params["friction"])
        self.restitution = float(physics_params["restitution"])
        self.dt = 1.0 / 30.0
        self.max_sim_steps = int(tracker_params["max_sim_steps"])
        self.min_radius_px = float(tracker_params["min_radius_px"])
        self.max_radius_px = float(tracker_params["max_radius_px"])
        self.min_area_px = float(tracker_params["min_area_px"])
        self.min_circularity = float(tracker_params["min_circularity"])
        self.min_prediction_speed_mm_s = float(tracker_params["min_prediction_speed_mm_s"])
        self.stop_speed_mm_s = float(tracker_params["stop_speed_mm_s"])
        self.detection_timeout_s = float(detection_timeout_s)
        self.last_detection_time = None

        self.kf = cv2.KalmanFilter(4, 2)
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        self.kf.transitionMatrix = np.array(
            [[1, 0, self.dt, 0], [0, 1, 0, self.dt], [0, 0, 1, 0], [0, 0, 0, 1]],
            np.float32,
        )
        self.kf.processNoiseCov = np.diag([0.2, 0.2, 5.0, 5.0]).astype(np.float32)
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.5
        self.kf_initialized = False

        self.color_lower = np.asarray(color_lower, dtype=np.uint8)
        self.color_upper = np.asarray(color_upper, dtype=np.uint8)
        self.history_px = []
        self.max_history = int(tracker_params["history_length"])
        self.last_detection_px = None

    # Обновляет шаг времени фильтра, ограничивая выбросы из-за зависшей камеры.
    def set_dt(self, dt):
        self.dt = max(0.005, min(0.05, float(dt)))
        self.kf.transitionMatrix[0, 2] = self.dt
        self.kf.transitionMatrix[1, 3] = self.dt

    # Переводит координаты исходного кадра в миллиметры поля по гомографии.
    def _px_to_mm(self, pts_px):
        pts_px = np.asarray(pts_px, dtype=np.float32).reshape(-1, 1, 2)
        return cv2.perspectiveTransform(pts_px, self.M).reshape(-1, 2) * self.scale_mm

    # Переводит миллиметры поля обратно в координаты исходного кадра для отладки.
    def _mm_to_px(self, pts_mm):
        pts_mm = np.asarray(pts_mm, dtype=np.float32).reshape(-1, 1, 2)
        pts_virtual = pts_mm / self.scale_mm
        return cv2.perspectiveTransform(pts_virtual, self.M_inv).reshape(-1, 2)

    # Ищет самый похожий на мяч круглый цветной объект и возвращает его центр.
    def _detect_ball(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.color_lower, self.color_upper)
        kernel = np.ones((5, 5), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            return None

        circularity = 4.0 * np.pi * area / (perimeter * perimeter)
        (x, y), radius = cv2.minEnclosingCircle(contour)
        if not (
            self.min_radius_px < radius < self.max_radius_px
            and area > self.min_area_px
            and circularity > self.min_circularity
        ):
            return None

        return np.array([[x], [y]], dtype=np.float32)

    # Сообщает, было ли реальное обнаружение мяча достаточно недавно для безопасного движения.
    def has_fresh_detection(self, now=None):
        if self.last_detection_time is None:
            return False
        if now is None:
            now = time.monotonic()
        return now - self.last_detection_time <= self.detection_timeout_s

    # Сбрасывает прогноз, чтобы старый мяч не превращался в новую ложную цель.
    def reset_tracking(self):
        self.kf_initialized = False
        self.last_detection_time = None
        self.last_detection_px = None
        self.history_px.clear()
        self.kf.statePost[:] = 0
        self.kf.statePre[:] = 0

    # Отражает координату и скорость от боковых стен, сохраняя коэффициент упругости.
    def _reflect_from_walls(self, pos_mm, vel_mm):
        if pos_mm[0] < self.wall_l_x:
            pos_mm[0] = self.wall_l_x + (self.wall_l_x - pos_mm[0])
            vel_mm[0] = abs(vel_mm[0]) * self.restitution
        elif pos_mm[0] > self.wall_r_x:
            pos_mm[0] = self.wall_r_x - (pos_mm[0] - self.wall_r_x)
            vel_mm[0] = -abs(vel_mm[0]) * self.restitution

    # Прогнозирует точку встречи мяча с рейкой либо возвращает None при небезопасном трекинге.
    def get_prediction(self, frame, now=None):
        if frame is None:
            return None, []
        if now is None:
            now = time.monotonic()

        detection_px = self._detect_ball(frame)
        if detection_px is not None:
            if not self.kf_initialized:
                self.kf.statePost[:2] = detection_px
                self.kf.statePre[:2] = detection_px
                self.kf_initialized = True
            self.kf.correct(detection_px)
            self.last_detection_px = detection_px.flatten().astype(int)
            self.last_detection_time = now
        elif not self.has_fresh_detection(now):
            self.reset_tracking()
            return None, []

        state = self.kf.predict()
        curr_px = state[:2].flatten().astype(np.float32)
        vel_px = state[2:].flatten().astype(np.float32)
        self.history_px.append(curr_px.astype(int))
        if len(self.history_px) > self.max_history:
            self.history_px.pop(0)

        pos_mm = self._px_to_mm([curr_px])[0]
        vel_mm = vel_px * self.scale_mm
        if np.linalg.norm(vel_mm) < self.min_prediction_speed_mm_s:
            return pos_mm.tolist(), [curr_px.astype(int).tolist()]

        trajectory_mm = [pos_mm.copy()]
        target_mm = pos_mm.copy()
        # Нормализация сохраняет прежнее трение при разных фактических FPS камеры.
        friction_multiplier = (1.0 - min(self.friction, 0.99)) ** (self.dt / (1.0 / 30.0))

        for _ in range(self.max_sim_steps):
            prev_pos_mm = pos_mm.copy()
            vel_mm *= friction_multiplier
            if self.curvature_k:
                vel_mm[0] += (self.curvature_k * (pos_mm[0] - self.center_x)) * self.dt
                vel_mm[1] += (self.curvature_k * (pos_mm[1] - self.center_y)) * self.dt

            pos_mm += vel_mm * self.dt
            self._reflect_from_walls(pos_mm, vel_mm)
            trajectory_mm.append(pos_mm.copy())

            if (prev_pos_mm[1] <= self.beam_y_mm <= pos_mm[1]) or (
                prev_pos_mm[1] >= self.beam_y_mm >= pos_mm[1]
            ):
                delta_y = pos_mm[1] - prev_pos_mm[1]
                if abs(delta_y) > 1e-3:
                    part = (self.beam_y_mm - prev_pos_mm[1]) / delta_y
                    target_mm = np.array(
                        [prev_pos_mm[0] + part * (pos_mm[0] - prev_pos_mm[0]), self.beam_y_mm],
                        dtype=np.float32,
                    )
                else:
                    target_mm = pos_mm.copy()
                break

            target_mm = pos_mm.copy()
            if np.linalg.norm(vel_mm) < self.stop_speed_mm_s:
                break

        trajectory_px = self._mm_to_px(trajectory_mm).astype(int).tolist()
        return target_mm.tolist(), trajectory_px

    # Рисует обнаруженный мяч, недавнюю траекторию и рассчитанный прогноз на кадре отладки.
    def draw_debug(self, frame, trajectory_px):
        if self.last_detection_px is not None and self.has_fresh_detection():
            cv2.circle(frame, tuple(self.last_detection_px), 12, (0, 255, 0), 2)

        for index in range(1, len(self.history_px)):
            cv2.line(frame, tuple(self.history_px[index - 1]), tuple(self.history_px[index]), (0, 255, 0), 2)

        for index in range(1, len(trajectory_px)):
            point_a = tuple(trajectory_px[index - 1])
            point_b = tuple(trajectory_px[index])
            if self._is_point_in_frame(point_a, frame) and self._is_point_in_frame(point_b, frame):
                cv2.line(frame, point_a, point_b, (255, 0, 0), 2)

        if trajectory_px:
            end_point = tuple(trajectory_px[-1])
            if self._is_point_in_frame(end_point, frame):
                cv2.circle(frame, end_point, 6, (0, 0, 255), -1)
        return frame

    # Проверяет, находится ли точка внутри кадра перед передачей её в OpenCV для рисования.
    def _is_point_in_frame(self, point, frame):
        return 0 <= point[0] < frame.shape[1] and 0 <= point[1] < frame.shape[0]
