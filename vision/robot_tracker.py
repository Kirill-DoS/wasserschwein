from collections import deque

import cv2
import numpy as np


class RobotTracker:
    # Настраивает поиск цветной метки робота и короткое сглаживание измерений камеры.
    def __init__(self, hsv_lower, hsv_upper, homography, scale_mm, tracker_params):
        self.lower = np.asarray(hsv_lower, dtype=np.uint8)
        self.upper = np.asarray(hsv_upper, dtype=np.uint8)
        self.homography = homography
        self.scale_mm = scale_mm
        self.history = deque(maxlen=int(tracker_params["filter_length"]))
        self.min_radius_px = float(tracker_params["min_radius_px"])
        self.max_radius_px = float(tracker_params["max_radius_px"])

    # Находит метку робота, переводит её координаты в миллиметры и сглаживает дрожание камеры.
    def get_position(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        kernel = np.ones((5, 5), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        contour = max(contours, key=cv2.contourArea)
        (x, y), radius = cv2.minEnclosingCircle(contour)
        if not self.min_radius_px < radius < self.max_radius_px:
            return None

        point_px = np.array([[x, y]], dtype=np.float32).reshape(-1, 1, 2)
        point_mm = cv2.perspectiveTransform(point_px, self.homography)[0, 0] * self.scale_mm
        self.history.append(point_mm)
        return np.median(np.asarray(self.history), axis=0)
