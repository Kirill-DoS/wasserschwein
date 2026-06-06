import cv2
import numpy as np

class BallTracker:
    def __init__(self, homography_path, wall_l_path, wall_r_path, beam_path):
        self.M = np.load(homography_path)
        self.M_inv = np.linalg.inv(self.M)
        self.scale_mm = np.array([1500.0/800.0, 1500.0/600.0], dtype=np.float32)

        self.wall_l_mm = self._px_to_mm(np.load(wall_l_path))
        self.wall_r_mm = self._px_to_mm(np.load(wall_r_path))
        self.beam_mm = self._px_to_mm(np.load(beam_path))

        self.wall_l_x = np.min(self.wall_l_mm[:, 0])
        self.wall_r_x = np.max(self.wall_r_mm[:, 0])
        self.center_x = (self.wall_l_x + self.wall_r_x) / 2.0
        self.center_y = (np.min(self.wall_l_mm[:, 1]) + np.max(self.wall_r_mm[:, 1])) / 2.0

        # Координата Y нашей балки в мм, где стоит робот (берем среднее по точкам балки)
        self.beam_y_mm = np.mean(self.beam_mm[:, 1])

        self.curvature_k = 0.08
        self.friction = 0.006
        self.dt = 0.016
        self.max_sim_steps = 60  # Немного увеличили, чтобы точно долетало до балки

        self.kf = cv2.KalmanFilter(4, 2)
        self.kf.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
        self.kf.transitionMatrix = np.array([[1,0,self.dt,0],[0,1,0,self.dt],[0,0,1,0],[0,0,0,1]], np.float32)

        # Снизили шум процесса (Process Noise), чтобы траектория была стабильнее и меньше дергалась
        self.kf.processNoiseCov = np.diag([0.2, 0.2, 5.0, 5.0]).astype(np.float32)
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.5
        self.kf_initialized = False

        self.color_lower = np.array([0, 120, 120])
        self.color_upper = np.array([15, 255, 255])
        self.history_px = []
        self.max_history = 10
        self.last_detection_px = None

    def set_dt(self, dt):
        self.dt = max(0.005, min(0.05, dt))
        self.kf.transitionMatrix[0, 2] = self.dt
        self.kf.transitionMatrix[1, 3] = self.dt

    def _px_to_mm(self, pts_px):
        pts_px = np.array(pts_px, dtype=np.float32).reshape(-1, 1, 2)
        return cv2.perspectiveTransform(pts_px, self.M).reshape(-1, 2) * self.scale_mm

    def _mm_to_px(self, pts_mm):
        pts_mm = np.array(pts_mm, dtype=np.float32).reshape(-1, 1, 2)
        pts_virt = pts_mm / self.scale_mm
        return cv2.perspectiveTransform(pts_virt, self.M_inv).reshape(-1, 2)

    def get_prediction(self, frame):
        """
        Возвращает:
        target_mm: [x, y] в мм (точка встречи на балке робота)
        trajectory_px: список точек в пикселях для красивой отрисовки debug-линий
        """
        if frame is None:
            return None, []

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.color_lower, self.color_upper)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detection_px = None
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), r) = cv2.minEnclosingCircle(c)
            if 3 < r < 50:
                detection_px = np.array([[x], [y]], dtype=np.float32)

        if detection_px is not None:
            if not self.kf_initialized:
                self.kf.statePost[:2] = detection_px
                self.kf_initialized = True
            self.kf.correct(detection_px)
            self.last_detection_px = detection_px.flatten().astype(int)

        state = self.kf.predict()
        curr_px = state[:2].flatten().astype(np.float32)
        vel_px = state[2:].flatten()

        self.history_px.append(curr_px.astype(int))
        if len(self.history_px) > self.max_history:
            self.history_px.pop(0)

        # Переводим текущие px координаты и скорость фильтра Калмана в МИЛЛИМЕТРЫ
        pos_mm = self._px_to_mm([curr_px])[0]
        vel_mm = vel_px * self.scale_mm  # скорость из px/sec в мм/sec

        if not self.kf_initialized or np.linalg.norm(vel_mm) < 10.0:
            return pos_mm.tolist(), [curr_px.astype(int).tolist()]

        # Симуляция физики ПОЛНОСТЬЮ в миллиметрах
        trajectory_mm = [pos_mm.copy()]
        target_mm = pos_mm.copy()

        for _ in range(self.max_sim_steps):
            prev_y = pos_mm[1]

            # Применяем трение
            vel_mm *= (1.0 - self.friction)

            # Применяем радиальную кривизну стола
            if self.curvature_k != 0:
                dx = pos_mm[0] - self.center_x
                dy = pos_mm[1] - self.center_y
                vel_mm[0] += (self.curvature_k * dx) * self.dt
                vel_mm[1] += (self.curvature_k * dy) * self.dt

            # Шаг движения в мм
            pos_mm += vel_mm * self.dt
            trajectory_mm.append(pos_mm.copy())

            # ПРОВЕРКА 1: Пересек ли мяч линию нашей балки по оси Y? (Точка встречи)
            # Условие обрабатывает движение мяча как сверху вниз, так и снизу вверх к балке
            if (prev_y <= self.beam_y_mm <= pos_mm[1]) or (prev_y >= self.beam_y_mm >= pos_mm[1]):
                # Находим точный X в момент пересечения Y-линии балки через пропорцию
                if abs(pos_mm[1] - prev_y) > 1e-3:
                    pct = (self.beam_y_mm - prev_y) / (pos_mm[1] - prev_y)
                    exact_x = trajectory_mm[-2][0] + pct * (pos_mm[0] - trajectory_mm[-2][0])
                    target_mm = np.array([exact_x, self.beam_y_mm], dtype=np.float32)
                else:
                    target_mm = pos_mm.copy()
                break
            else:
                target_mm = pos_mm.copy()

            # ПРОВЕРКА 2: Вылет за боковые стены стола
            if pos_mm[0] < self.wall_l_x or pos_mm[0] > self.wall_r_x:
                break

            # ПРОВЕРКА 3: Мяч остановился
            if np.linalg.norm(vel_mm) < 5.0:
                break

        # Переводим массив траектории в пиксели ОДНИМ махом только для отрисовки графики
        trajectory_px = self._mm_to_px(trajectory_mm).astype(int).tolist()

        return target_mm.tolist(), trajectory_px

    def draw_debug(self, frame, trajectory_px, scale_x=1.0, scale_y=1.0):
        # Отрисовка детекта
        if self.last_detection_px is not None:
            x = int(self.last_detection_px[0] * scale_x)
            y = int(self.last_detection_px[1] * scale_y)
            cv2.circle(frame, (x, y), 12, (0, 255, 0), 2)

        # Отрисовка истории хвоста
        for i in range(1, len(self.history_px)):
            p1 = (int(self.history_px[i-1][0]*scale_x), int(self.history_px[i-1][1]*scale_y))
            p2 = (int(self.history_px[i][0]*scale_x), int(self.history_px[i][1]*scale_y))
            cv2.line(frame, p1, p2, (0, 255, 0), 2)

        # Отрисовка предсказанной линии
        if len(trajectory_px) > 1:
            for i in range(1, len(trajectory_px)):
                p1 = (int(trajectory_px[i-1][0]*scale_x), int(trajectory_px[i-1][1]*scale_y))
                p2 = (int(trajectory_px[i][0]*scale_x), int(trajectory_px[i][1]*scale_y))
                if (0 <= p1[0] < frame.shape[1] and 0 <= p1[1] < frame.shape[0] and
                    0 <= p2[0] < frame.shape[1] and 0 <= p2[1] < frame.shape[0]):
                    cv2.line(frame, p1, p2, (255, 0, 0), 2)

            # Конечная точка симуляции (красный кружок)
            end_pt = (int(trajectory_px[-1][0]*scale_x), int(trajectory_px[-1][1]*scale_y))
            if 0 <= end_pt[0] < frame.shape[1] and 0 <= end_pt[1] < frame.shape[0]:
                cv2.circle(frame, end_pt, 6, (0, 0, 255), -1)
        return frame
