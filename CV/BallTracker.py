import cv2
import numpy as np

class BallTracker:
    def __init__(self, homography_path, wall_l_path, wall_r_path, beam_path):
        # 1. Загрузка матрицы гомографии
        self.M = np.load(homography_path)
        self.M_inv = np.linalg.inv(self.M)
        
        # Гомография из Polygon.py маппит в 800x600. Переводим в реальные мм (1500x1500)
        self.scale_xy = np.array([1500.0/800.0, 1500.0/600.0], dtype=np.float32)

        # 2. Загрузка геометрии и перевод в мм
        self.wall_l = self._to_mm(np.load(wall_l_path))
        self.wall_r = self._to_mm(np.load(wall_r_path))
        self.beam = self._to_mm(np.load(beam_path))
        
        # Границы стенок по X (учитываем небольшой наклон после гомографии)
        self.wall_l_x = np.min(self.wall_l[:, 0])
        self.wall_r_x = np.max(self.wall_r[:, 0])
        self.center_x = (self.wall_l_x + self.wall_r_x) / 2.0

        # 3. Физические параметры (настроены под регламент)
        # Выпуклость 35мм создаёт возвращающее ускорение к центру. 
        # a_x ≈ -g * (2*h / (W/2)^2) * dx ≈ -1.2 * dx (мм/с² на мм отклонения)
        self.curvature_k = 1.2          
        self.friction = 0.015           # Затухание скорости на шаг (качение)
        self.restitution = 0.82         # Потеря энергии при отскоке от стенки
        self.dt = 0.01                  # Шаг симуляции 10мс (стабильно для 60-120 FPS)
        self.max_sim_steps = 250        # Макс. шагов прогноза

        # 4. Фильтр Калмана [x, y, vx, vy]
        self.kf = cv2.KalmanFilter(4, 2)
        self.kf.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
        self.kf.transitionMatrix = np.array([[1,0,self.dt,0],[0,1,0,self.dt],[0,0,1,0],[0,0,0,1]], np.float32)
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.05
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 5.0
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)
        self.kf.statePost = np.zeros((4, 1), np.float32)
        self.kf_initialized = False

        # Цветовые пороги (по умолчанию оранжевый, перезаписываются из main.py)
        self.color_lower = np.array([0, 120, 120])
        self.color_upper = np.array([15, 255, 255])

        self.history = []
        self.max_history = 15

    def _to_mm(self, pts):
        """Перевод пикселей виртуальной гомографии в миллиметры"""
        pts = np.array(pts, dtype=np.float32).reshape(-1, 1, 2)
        pts_h = cv2.perspectiveTransform(pts, self.M).reshape(-1, 2)
        return pts_h * self.scale_xy

    def _to_pixel(self, pts):
        """Перевод миллиметров обратно в пиксели исходного кадра"""
        pts = np.array(pts, dtype=np.float32).reshape(-1, 1,2) / self.scale_xy
        pts_h = cv2.perspectiveTransform(pts, self.M_inv).reshape(-1, 2)
        return pts_h.astype(int)

    def _check_beam_intersection(self, p1, p2):
        """Проверяет пересечение отрезка p1->p2 с линией балки. Возвращает точку пересечения или None"""
        # Уравнение прямой балки: A*x + B*y + C = 0
        x1, y1 = self.beam[0]; x2, y2 = self.beam[1]
        A = y1 - y2; B = x2 - x1; C = -A*x1 - B*y1
        
        denom = A*(p2[0]-p1[0]) + B*(p2[1]-p1[1])
        if abs(denom) < 1e-5: return None
        
        t = -(A*p1[0] + B*p1[1] + C) / denom
        if 0.0 <= t <= 1.0:
            inter_x = p1[0] + t * (p2[0] - p1[0])
            inter_y = p1[1] + t * (p2[1] - p1[1])
            # Проверяем, попадает ли точка пересечения в отрезок балки
            if min(x1,x2)-10 <= inter_x <= max(x1,x2)+10:
                return np.array([inter_x, inter_y])
        return None

    def get_prediction(self, frame):
        # 1. Детекция мяча
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.color_lower, self.color_upper)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detection = None
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), r) = cv2.minEnclosingCircle(c)
            # Фильтр по размеру (мяч 43мм ~ 15-35px в зависимости от расстояния)
            if 10 < r < 50:
                detection = np.array([[x], [y]], dtype=np.float32)

        # 2. Обновление Калмана (исправлен порядок вызовов)
        if detection is not None:
            self.kf.correct(detection)
            if not self.kf_initialized:
                # Инициализация состояния при первом обнаружении
                self.kf.statePost[0] = detection[0]
                self.kf.statePost[1] = detection[1]
                self.kf.statePost[2] = 0.0
                self.kf.statePost[3] = 0.0
                self.kf_initialized = True
        else:
            # Если детекция пропала, Калман продолжит прогнозировать по инерции
            pass

        # Получаем сглаженное состояние в мм
        state = self.kf.predict()
        curr_mm = state[:2].flatten().astype(float)
        vel_mm = state[2:].flatten().astype(float)

        # Сохраняем историю для отладки
        curr_px = self._to_pixel([curr_mm])[0]
        self.history.append(curr_px)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        if not self.kf_initialized:
            return None, []

        # 3. Физическое моделирование траектории
        trajectory_px = [curr_px]
        pos = curr_mm.copy()
        vel = vel_mm.copy()

        for _ in range(self.max_sim_steps):
            prev_pos = pos.copy()

            # Применяем кривизну дна (возврат к центру поля)
            ax = -self.curvature_k * (pos[0] - self.center_x)
            ay = 0.0

            # Трение
            vel *= (1 - self.friction)

            # Интегрирование (полу-неявный Эйлер)
            vel[0] += ax * self.dt
            pos += vel * self.dt

            # Проверка пересечения с балкой робота
            inter = self._check_beam_intersection(prev_pos, pos)
            if inter is not None:
                trajectory_px.append(self._to_pixel([inter])[0])
                break  # Строго останавливаемся на линии робота

            # Отскок от стенок
            if pos[0] < self.wall_l_x:
                vel[0] = -vel[0] * self.restitution
                pos[0] = self.wall_l_x + 1.0
            elif pos[0] > self.wall_r_x:
                vel[0] = -vel[0] * self.restitution
                pos[0] = self.wall_r_x - 1.0

            trajectory_px.append(self._to_pixel([pos])[0])

            # Если мяч почти остановился
            if np.linalg.norm(vel) < 0.8:
                break

        return trajectory_px[-1], trajectory_px

    def draw_debug(self, frame, trajectory):
        # Зеленая линия реальной истории
        for i in range(1, len(self.history)):
            cv2.line(frame, tuple(self.history[i-1]), tuple(self.history[i]), (0, 255, 0), 2)
            
        # Синяя линия прогноза
        if len(trajectory) > 1:
            for i in range(1, len(trajectory)):
                cv2.line(frame, tuple(trajectory[i-1]), tuple(trajectory[i]), (255, 0, 0), 2)
            # Красная точка цели на балке
            cv2.circle(frame, tuple(trajectory[-1]), 6, (0, 0, 255), -1)
        return frame