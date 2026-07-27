import math


class RobotController:
    # Создаёт регулятор положения в физических единицах и параметры перевода в PWM.
    def __init__(
        self,
        max_speed_mm_s,
        max_acc_mm_s2,
        max_pwm=255,
        deadband_mm=20.0,
    ):
        self.max_speed_mm_s = float(max_speed_mm_s)
        self.max_acc_mm_s2 = float(max_acc_mm_s2)
        self.max_pwm = int(max_pwm)
        self.deadband_mm = float(deadband_mm)
        self.current_pos_mm = 0.0
        self.commanded_speed_mm_s = 0.0

    # Сбрасывает внутреннюю командную скорость после аварийной остановки или потери трекинга.
    def reset(self):
        self.commanded_speed_mm_s = 0.0

    # Ограничивает изменение скорости, чтобы команда не требовала мгновенного разгона мотора.
    def _limit_acceleration(self, desired_speed_mm_s, dt):
        max_delta = self.max_acc_mm_s2 * dt
        delta = desired_speed_mm_s - self.commanded_speed_mm_s
        delta = max(-max_delta, min(max_delta, delta))
        self.commanded_speed_mm_s += delta
        return self.commanded_speed_mm_s

    # Переводит требуемую линейную скорость каретки в диапазон PWM контроллера 0…max_pwm.
    def _speed_to_pwm(self, speed_mm_s):
        if self.max_speed_mm_s <= 0:
            return 0
        pwm = round(abs(speed_mm_s) / self.max_speed_mm_s * self.max_pwm)
        return int(max(0, min(self.max_pwm, pwm)))

    # Рассчитывает знаковую скорость и PWM по целевой и измеренной камерой позиции робота.
    def update_motion(self, target_pos_mm, current_pos_mm, dt):
        self.current_pos_mm = float(current_pos_mm)
        dt = max(0.001, min(0.1, float(dt)))
        error_mm = float(target_pos_mm) - self.current_pos_mm

        if abs(error_mm) <= self.deadband_mm:
            self.reset()
            return 0.0, 0

        # Формула гарантирует, что при текущем ускорении остаётся место для торможения.
        braking_limited_speed = math.sqrt(2.0 * self.max_acc_mm_s2 * abs(error_mm))
        desired_speed_mm_s = math.copysign(
            min(self.max_speed_mm_s, braking_limited_speed), error_mm
        )

        commanded_speed_mm_s = self._limit_acceleration(desired_speed_mm_s, dt)
        if abs(commanded_speed_mm_s) < 1e-6:
            commanded_speed_mm_s = 0.0
            self.commanded_speed_mm_s = 0.0

        return commanded_speed_mm_s, self._speed_to_pwm(commanded_speed_mm_s)
