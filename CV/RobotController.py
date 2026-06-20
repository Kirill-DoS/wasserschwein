class RobotController:
    def __init__(self, max_vel, max_acc, dt):
        self.max_vel = max_vel
        self.max_acc = max_acc
        self.dt = dt
        self.current_vel = 0.0
        self.current_pos = 0.0

        self.Kp = 7.0
        self.damping = 3.0          # сильное гашение, но только при торможении
        self.damping_zone_mm = 150  # зона, где включается damping

    def update_motion(self, target_pos):
        self.dist_to_target = target_pos - self.current_pos
        abs_dist = abs(self.dist_to_target)

        # Целевая скорость по P-регулятору
        target_vel = self.Kp * abs_dist
        if target_vel > self.max_vel:
            target_vel = self.max_vel

        # Ограничение ускорением
        max_vel_change = self.max_acc * self.dt

        if self.current_vel < target_vel:
            self.current_vel += max_vel_change
            if self.current_vel > target_vel:
                self.current_vel = target_vel
        else:
            self.current_vel -= max_vel_change
            if self.current_vel < target_vel:
                self.current_vel = target_vel

        # ✅ УМНЫЙ DAMPING: работает только вблизи цели
        if abs_dist < self.damping_zone_mm:
            # Чем ближе к цели, тем сильнее гасим
            damping_factor = self.damping * (1.0 - abs_dist / self.damping_zone_mm)
            self.current_vel *= (1.0 - damping_factor * self.dt)

        # Минимальная скорость
        if self.current_vel < 0.5:
            self.current_vel = 0.0

        # Движение
        if self.dist_to_target > 0:
            self.current_pos += self.current_vel * self.dt
        else:
            self.current_pos -= self.current_vel * self.dt

        return self.current_pos, self.current_vel
