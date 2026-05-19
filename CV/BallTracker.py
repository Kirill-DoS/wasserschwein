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

        self.curvature_k = 0.08
        self.friction = 0.006
        self.restitution = 0.82
        self.dt = 0.016
        self.max_sim_steps = 40

        self.kf = cv2.KalmanFilter(4, 2)
        self.kf.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
        self.kf.transitionMatrix = np.array([[1,0,self.dt,0],[0,1,0,self.dt],[0,0,1,0],[0,0,0,1]], np.float32)

        self.kf.processNoiseCov = np.diag([0.1, 0.1, 20.0, 20.0]).astype(np.float32)
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.25
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
        return cv2.perspectiveTransform(pts_virt, self.M_inv).reshape(-1, 2).astype(int)

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

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.color_lower, self.color_upper)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detection_px = None
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), r) = cv2.minEnclosingCircle(c)
            if 3 < r < 50:  # Подстроено под 640x360
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
        if len(self.history_px) > self.max_history: self.history_px.pop(0)

        if not self.kf_initialized: return curr_px.tolist(), [curr_px.tolist()]
        if np.linalg.norm(vel_px) < 5.0: return curr_px.tolist(), [curr_px.tolist()]

        pos_px = curr_px.copy()
        vel_sim = vel_px.copy()
        trajectory_px = [curr_px.tolist()]

        for _ in range(self.max_sim_steps):
            vel_sim *= (1.0 - self.friction)

            # Радиальная кривизна (дом = отталкивает от центра по обеим осям)
            if self.curvature_k != 0:
                pos_mm = self._px_to_mm([pos_px])[0]
                dx = pos_mm[0] - self.center_x
                dy = pos_mm[1] - self.center_y
                vel_sim[0] += (self.curvature_k * dx / self.scale_mm[0]) * self.dt
                vel_sim[1] += (self.curvature_k * dy / self.scale_mm[1]) * self.dt

            pos_px += vel_sim * self.dt
            trajectory_px.append(pos_px.tolist())

            check_mm = self._px_to_mm([pos_px])[0]
            if check_mm[0] < self.wall_l_x or check_mm[0] > self.wall_r_x: break
            if np.linalg.norm(vel_sim) < 2.0: break

        return trajectory_px[-1], trajectory_px

    def draw_debug(self, frame, trajectory, scale_x=1.0, scale_y=1.0):
        def to_int_tuple(pt):
            return tuple(int(round(c)) for c in pt)

        # Масштабируем внутренние координаты под оригинальный кадр
        if self.last_detection_px is not None:
            x = int(self.last_detection_px[0] * scale_x)
            y = int(self.last_detection_px[1] * scale_y)
            cv2.circle(frame, (x, y), 12, (0, 255, 0), 2)

        for i in range(1, len(self.history_px)):
            p1 = (int(self.history_px[i-1][0]*scale_x), int(self.history_px[i-1][1]*scale_y))
            p2 = (int(self.history_px[i][0]*scale_x), int(self.history_px[i][1]*scale_y))
            cv2.line(frame, p1, p2, (0, 255, 0), 2)

        if len(trajectory) > 1:
            for i in range(1, len(trajectory)):
                p1 = to_int_tuple(trajectory[i-1])
                p2 = to_int_tuple(trajectory[i])
                if (0 <= p1[0] < frame.shape[1] and 0 <= p1[1] < frame.shape[0] and
                    0 <= p2[0] < frame.shape[1] and 0 <= p2[1] < frame.shape[0]):
                    cv2.line(frame, p1, p2, (255, 0, 0), 2)
            end_pt = to_int_tuple(trajectory[-1])
            if 0 <= end_pt[0] < frame.shape[1] and 0 <= end_pt[1] < frame.shape[0]:
                cv2.circle(frame, end_pt, 6, (0, 0, 255), -1)
        elif len(trajectory) == 1:
            pt = to_int_tuple(trajectory[0])
            if 0 <= pt[0] < frame.shape[1] and 0 <= pt[1] < frame.shape[0]:
                cv2.circle(frame, pt, 6, (255, 0, 0), -1)
        return frame
