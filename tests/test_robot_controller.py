import unittest

from CV.RobotController import RobotController


class RobotControllerTest(unittest.TestCase):
    # Создаёт одинаковый регулятор перед каждым тестом его поведения.
    def setUp(self):
        self.controller = RobotController(
            max_speed_mm_s=1000,
            max_acc_mm_s2=500,
            max_pwm=255,
            deadband_mm=20,
        )

    # Проверяет, что рядом с целью регулятор не создаёт мелкие дёргающие команды.
    def test_deadband_stops_the_robot(self):
        speed, pwm = self.controller.update_motion(target_pos_mm=1010, current_pos_mm=1000, dt=0.02)
        self.assertEqual(speed, 0.0)
        self.assertEqual(pwm, 0)

    # Проверяет, что одно обновление скорости не превышает разрешённое ускорение.
    def test_acceleration_is_limited(self):
        speed, pwm = self.controller.update_motion(target_pos_mm=2000, current_pos_mm=0, dt=0.02)
        self.assertAlmostEqual(speed, 10.0)
        self.assertEqual(pwm, 3)

    # Проверяет, что скорость и PWM никогда не выходят за заданные пределы.
    def test_speed_and_pwm_are_capped(self):
        speed = 0.0
        pwm = 0
        for _ in range(200):
            speed, pwm = self.controller.update_motion(target_pos_mm=10000, current_pos_mm=0, dt=0.05)
        self.assertLessEqual(speed, 1000)
        self.assertLessEqual(pwm, 255)

    # Проверяет, что после остановки внутреннее состояние не сохраняет старую скорость.
    def test_reset_clears_commanded_speed(self):
        self.controller.update_motion(target_pos_mm=2000, current_pos_mm=0, dt=0.05)
        self.controller.reset()
        speed, pwm = self.controller.update_motion(target_pos_mm=0, current_pos_mm=0, dt=0.05)
        self.assertEqual(speed, 0.0)
        self.assertEqual(pwm, 0)


if __name__ == "__main__":
    unittest.main()
