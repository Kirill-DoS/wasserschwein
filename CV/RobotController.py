class RobotController:
    def __init__(self, max_vel, max_acc, dt):
        self.max_vel = max_vel
        self.max_acc = max_acc
        self.dt = dt
        self.current_vel = 0.0
        self.current_pos = 0.0

        # ✅ ИСПРАВЛЕНО: правильные коэффициенты
        self.Kp = 7.0
        self.damping = 2.0          # сильное гашение, но только при торможении
        self.damping_zone_mm = 150  # зона, где включается damping

    def set_dt(self, dt):
        """Обновляем dt каждый кадр под реальное значение"""
        self.dt = max(0.005, min(0.05, dt))

    def sync_position(self, real_pos, alpha=0.3):
        """Мягкая синхронизация с реальной позицией (фильтр низких частот)"""
        # alpha=0.3 → 30% реальной позиции + 70% модели
        self.current_pos = self.current_pos * (1 - alpha) + real_pos * alpha

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
