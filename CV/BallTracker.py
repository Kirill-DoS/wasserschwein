import cv2
import numpy as np

class BallTracker:
    def __init__(self, homography_path, wall_l_path, wall_r_path, beam_path):
        # 1. Загрузка гомографии и масштаба
        self.M = np.load(homography_path)
        self.M_inv = np.linalg.inv(self.M)
        # Виртуальные 800x600 -> реальные 1500x1500 мм (по PolygonReglament.csv)
        self.scale_mm = np.array([1500.0/800.0, 1500.0/600.0], dtype=np.float32)

        # 2. Геометрия сразу в миллиметрах
        self.wall_l_mm = self._px_to_mm(np.load(wall_l_path))
        self.wall_r_mm = self._px_to_mm(np.load(wall_r_path))
        self.beam_mm = self._px_to_mm(np.load(beam_path))
        
        self.wall_l_x = np.min(self.wall_l_mm[:, 0])
        self.wall_r_x = np.max(self.wall_r_mm[:, 0])
        self.center_x = (self.wall_l_x + self.wall_r_x) / 2.0

        # 3. Физика (регламент: выпуклость 35мм, отскок, трение)
        self.curvature_k = 1.2
        self.friction = 0.015
        self.restitution = 0.82
        self.dt = 0.016  # Шаг ~60 FPS
        self.max_sim_steps = 200

        # 4. Калман в пикселях (стабильнее для детекции)
        self.kf = cv2.KalmanFilter(4, 2)
        self.kf.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
        self.kf.transitionMatrix = np.array([[1,0,self.dt,0],[0,1,0,self.dt],[0,0,1,0],[0,0,0,1]], np.float32)
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.05
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 5.0
        self.kf_initialized = False

        # Цвета (перезаписываются из main.py)
        self.color_lower = np.array([0, 120, 120])
        self.color_upper = np.array([15, 255, 255])

        self.history_px = []
        self.max_history = 15
        self.last_detection_px = None  # Для отрисовки текущего мяча

    def _px_to_mm(self, pts_px):
        pts_px = np.array(pts_px, dtype=np.float32).reshape(-1, 1, 2)
        pts_virt = cv2.perspectiveTransform(pts_px, self.M).reshape(-1, 2)
        return pts_virt * self.scale_mm

    def _mm_to_px(self, pts_mm):
        pts_mm = np.array(pts_mm, dtype=np.float32).reshape(-1, 1, 2)
        pts_virt = pts_mm / self.scale_mm
        pts_px = cv2.perspectiveTransform(pts_virt, self.M_inv).reshape(-1, 2)
        return pts_px.astype(int)

    def _line_intersection(self, p1, p2, p3, p4):
        x1, y1 = p1; x2, y2 = p2
        x3, y3 = p3; x4, y4 = p4
        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if abs(denom) < 1e-5: return None, float('inf')
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
        if 0 <= ua <= 1 and 0 <= ub <= 1:
            return np.array([x1 + ua*(x2-x1), y1 + ua*(y2-y1)]), ua 
        return None, float('inf')

    def get_prediction(self, frame):
        if frame is None: return [0, 0], [[0, 0]]

        # 1. Детекция
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.color_lower, self.color_upper)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detection_px = None
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), r) = cv2.minEnclosingCircle(c)
            if 10 < r < 50:  # Фильтр шума (мяч 43мм)
                detection_px = np.array([[x], [y]], dtype=np.float32)

        # 2. Калман
        if detection_px is not None:
            if not self.kf_initialized:
                self.kf.statePost[0,0] = detection_px[0,0]
                self.kf.statePost[1,0] = detection_px[1,0]
                self.kf.statePost[2,0] = 0.0
                self.kf.statePost[3,0] = 0.0
                self.kf_initialized = True
            self.kf.correct(detection_px)
            self.last_detection_px = detection_px.flatten().astype(int)

        state = self.kf.predict()
        curr_px = state[:2].flatten().astype(int)
        vel_px = state[2:].flatten()

        # История для отрисовки
        self.history_px.append(curr_px)
        if len(self.history_px) > self.max_history:
            self.history_px.pop(0)

        # Если фильтр ещё не готов, возвращаем текущую точку (чтобы draw_debug что-то нарисовал)
        if not self.kf_initialized:
            return curr_px, [curr_px]

        # 3. Физика в миллиметрах
        curr_mm = self._px_to_mm([curr_px])[0]
        vel_mm = vel_px * self.scale_mm

        if np.linalg.norm(vel_mm) < 0.5:
            return curr_px, [curr_px]

        trajectory_px = [curr_px]
        pos_mm = curr_mm.copy()
        vel_mm = vel_mm.copy()

        for _ in range(self.max_sim_steps):
            prev_pos_mm = pos_mm.copy()
            ax = -self.curvature_k * (pos_mm[0] - self.center_x)
            vel_mm *= (1.0 - self.friction)
            vel_mm[0] += ax * self.dt
            pos_mm += vel_mm * self.dt

            # Пересечение с балкой
            inter_mm, t = self._line_intersection(prev_pos_mm, pos_mm, self.beam_mm[0], self.beam_mm[1])
            if inter_mm is not None and 0 <= t <= 1:
                b1, b2 = self.beam_mm[0], self.beam_mm[1]
                if min(b1[0], b2[0]) - 30 <= inter_mm[0] <= max(b1[0], b2[0]) + 30:
                    trajectory_px.append(self._mm_to_px([inter_mm])[0])
                    break

            # Отскок от стенок
            if pos_mm[0] < self.wall_l_x:
                vel_mm[0] = -vel_mm[0] * self.restitution
                pos_mm[0] = self.wall_l_x + 1.0
            elif pos_mm[0] > self.wall_r_x:
                vel_mm[0] = -vel_mm[0] * self.restitution
                pos_mm[0] = self.wall_r_x - 1.0

            trajectory_px.append(self._mm_to_px([pos_mm])[0])
            if np.linalg.norm(vel_mm) < 0.8: break

        return trajectory_px[-1], trajectory_px

    def draw_debug(self, frame, trajectory):
        # 1. Обводка текущего мяча (зелёный круг + опционально квадрат)
        if self.last_detection_px is not None:
            x, y = self.last_detection_px
            cv2.circle(frame, (int(x), int(y)), 12, (0, 255, 0), 2)
            # Квадрат вокруг мяча (раскомментировать если нужен именно квадрат)
            # cv2.rectangle(frame, (x-15, y-15), (x+15, y+15), (0, 255, 0), 2)

        # 2. Зелёная линия пройденного пути
        for i in range(1, len(self.history_px)):
            cv2.line(frame, tuple(self.history_px[i-1]), tuple(self.history_px[i]), (0, 255, 0), 2)
            
        # 3. Синяя линия прогноза
        if len(trajectory) > 1:
            for i in range(1, len(trajectory)):
                cv2.line(frame, tuple(trajectory[i-1]), tuple(trajectory[i]), (255, 0, 0), 2)
            cv2.circle(frame, tuple(trajectory[-1]), 6, (0, 0, 255), -1)
        elif len(trajectory) == 1:
            cv2.circle(frame, tuple(trajectory[0]), 6, (255, 0, 0), -1)
            
        return frame