class RobotController:
    def __init__(self, max_vel, max_acc, dt):
        self.max_vel = max_vel
        self.max_acc = max_acc
        self.dt = dt
        self.target_pos = 0.0

        self.current_vel = 0.0
        self.current_pos = 0.0

    def update_motion(self, target_pos):
        # ИСПРАВЛЕНО: добавлены self. и скобки для приоритета операции деления
        self.S_brake = (self.current_vel * self.current_vel) / (2 * self.max_acc)
        self.dist_to_target = target_pos - self.current_pos

        # Работаем через модуль расстояния, чтобы корректно определять разгон/торможение
        abs_dist = abs(self.dist_to_target)

        if abs_dist > self.S_brake:
            self.current_vel += self.max_acc * self.dt
            if self.current_vel > self.max_vel:
                self.current_vel = self.max_vel
        else:
            self.current_vel -= self.max_acc * self.dt
            if self.current_vel < 0:
                self.current_vel = 0.0

        # ИСПРАВЛЕНО: движение в зависимости от направления к цели и знак умножения на dt вместо плюса
        if self.dist_to_target > 0:
            self.current_pos += self.current_vel * self.dt
        else:
            self.current_pos -= self.current_vel * self.dt

        return self.current_pos, self.current_vel
