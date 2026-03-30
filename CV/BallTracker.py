import cv2
import numpy as np

class BallTracker:
    def __init__(self, homography_path, wall_l_path, wall_r_path, beam_path, max_rebounds=3):
        # Загрузка калибровок (превращаем в метрические координаты сразу)
        self.M = np.load(homography_path)
        self.M_inv = np.linalg.inv(self.M)
        
        # Стенки и балка (переводим из пикселей в реальные координаты при инициализации)
        self.wall_l = self._to_real_coords(np.load(wall_l_path))
        self.wall_r = self._to_real_coords(np.load(wall_r_path))
        self.beam = self._to_real_coords(np.load(beam_path))
        
        self.max_rebounds = max_rebounds
        self.history = []
        self.max_history = 15
        
        # HSV фильтр (оранжево-красный гольф-мяч)
        self.color_lower = np.array([0, 120, 120])
        self.color_upper = np.array([15, 255, 255])

    def _to_real_coords(self, pts_pixel):
        """Преобразует массив точек из пикселей в метры [N, 2]"""
        pts_pixel = np.array(pts_pixel, dtype=np.float32).reshape(-1, 1, 2)
        real_pts = cv2.perspectiveTransform(pts_pixel, self.M)
        return real_pts.reshape(-1, 2)

    def _to_pixel_coords(self, pts_real):
        """Преобразует метры обратно в пиксели для отрисовки"""
        pts_real = np.array(pts_real, dtype=np.float32).reshape(-1, 1, 2)
        pixel_pts = cv2.perspectiveTransform(pts_real, self.M_inv)
        return pixel_pts.reshape(-1, 2).astype(int)

    def _intersect_lines(self, p1, p2, p3, p4):
        """Поиск точки пересечения двух отрезков (p1-p2) и (p3-p4)"""
        x1, y1 = p1; x2, y2 = p2
        x3, y3 = p3; x4, y4 = p4
        denom = (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)
        if denom == 0: return None, float('inf') # Параллельны
        ua = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / denom
        ub = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / denom
        if 0 <= ua and 0 <= ub <= 1:
            return np.array([x1 + ua*(x2-x1), y1 + ua*(y2-y1)]), ua
        return None, float('inf')

    def get_prediction(self, frame):
        """Основной метод: детекция + расчет траектории с рикошетами"""
        # 1. Поиск мяча (упрощенно)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.color_lower, self.color_upper)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not cnts: return None, []
        
        c = max(cnts, key=cv2.contourArea)
        ((x, y), r) = cv2.minEnclosingCircle(c)
        curr_pixel = np.array([x, y])
        
        # Обновляем историю
        self.history.append(curr_pixel.astype(int))
        if len(self.history) > self.max_history: self.history.pop(0)
        if len(self.history) < 3: return None, []

        # 2. Физика в реальных координатах
        p_now = self._to_real_coords([self.history[-1]])[0]
        p_prev = self._to_real_coords([self.history[-2]])[0]
        velocity = p_now - p_prev # Вектор скорости (м/кадр)
        
        # Если мяч почти не движется, не строим прогноз
        if np.linalg.norm(velocity) < 0.005: return None, []

        trajectory_points = [self.history[-1]] # Для отрисовки
        current_pos = p_now
        current_vel = velocity
        
        # ЦИКЛ РИКОШЕТОВ
        for _ in range(self.max_rebounds):
            # Проверяем пересечение со всеми преградами
            targets = [
                ('wall_l', self.wall_l),
                ('wall_r', self.wall_r),
                ('beam', self.beam)
            ]
            
            best_t = float('inf')
            hit_point = None
            hit_type = None

            for name, line in targets:
                p_inter, t = self._intersect_lines(current_pos, current_pos + current_vel * 100, line[0], line[1])
                if t < best_t and t > 0.01: # t > 0.01 чтобы не зациклиться в точке удара
                    best_t = t
                    hit_point = p_inter
                    hit_type = name

            if hit_point is not None:
                trajectory_points.append(self._to_pixel_coords([hit_point])[0])
                if hit_type == 'beam':
                    break # Конец пути
                
                # Отражение (стенки вертикальные -> инвертируем X скорость)
                # Если стенки строго параллельны оси Y, то просто:
                current_vel[0] = -current_vel[0] 
                current_pos = hit_point
            else:
                break

        return trajectory_points[-1], trajectory_points

    def draw_debug(self, frame, trajectory):
        # Зеленая история
        for i in range(1, len(self.history)):
            cv2.line(frame, tuple(self.history[i-1]), tuple(self.history[i]), (0, 255, 0), 1)
        
        # Синее предсказание (ломаная линия рикошетов)
        if len(trajectory) > 1:
            for i in range(1, len(trajectory)):
                cv2.line(frame, tuple(trajectory[i-1]), tuple(trajectory[i]), (255, 0, 0), 2)
            cv2.circle(frame, tuple(trajectory[-1]), 7, (255, 0, 0), -1)
            
        return frame
