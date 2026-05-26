import cv2
import numpy as np
from collections import deque

class RobotTracker:
    def __init__(self, hsv_lower, hsv_upper, M, scale_mm, filter_len=5):
        self.lower = np.array(hsv_lower)
        self.upper = np.array(hsv_upper)
        self.M = M
        self.scale_mm = scale_mm
        self.history = deque(maxlen=filter_len)  # медианный фильтр

    def get_position(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not cnts: return None

        c = max(cnts, key=cv2.contourArea)
        ((x, y), r) = cv2.minEnclosingCircle(c)
        if not (5 < r < 60): return None

        # Перевод в мм
        pts = np.array([[x, y]], dtype=np.float32).reshape(-1, 1, 2)
        mm = (cv2.perspectiveTransform(pts, self.M)[0, 0] * self.scale_mm)

        self.history.append(mm)
        return np.median(list(self.history), axis=0)  # сглаживание
