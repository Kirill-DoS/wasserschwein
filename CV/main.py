import cv2
import os
import time
import numpy as np
import serial
from BallTracker import BallTracker
from RobotTracker import RobotTracker
from RobotController import RobotController
from ColorCalibrate import ColorCalibrator
from Polygon import PolygonMarker
from Config import Config

camID = 1
Max_Vel = 255
Max_Acc = 800
MIN_MOTOR_PWM = 35  # ✅ НОВОЕ: минимальная скорость для старта моторов

def main():
    config = Config()
    required_files = ['perimeter.npy', 'left_wall.npy', 'right_wall.npy', 'robot_beam.npy']

    if not all(os.path.exists(f) for f in required_files):
        print("📐 Файлы геометрии не найдены. Запуск разметки...")
        PolygonMarker(camID).run()
    else:
        print("✅ Геометрия загружена.")

    print("🎨 Запуск калибровки цвета...")
    calibrator = ColorCalibrator(camID)
    color_lower, color_upper = calibrator.calibrate()
    print(f"Цвет: lower={color_lower}, upper={color_upper}")

    config.set_color_bounds(color_lower, color_upper)
    config.save()
    time.sleep(0.5)

    tracker = BallTracker('perimeter.npy', 'left_wall.npy', 'right_wall.npy', 'robot_beam.npy')
    tracker.color_lower = color_lower
    tracker.color_upper = color_upper

    physics = config.get_physics_params()
    tracker.curvature_k = physics.get("curvature_k", 0.08)
    tracker.friction = physics.get("friction", 0.006)

    robot_ctrl = RobotController(max_vel=Max_Vel, max_acc=Max_Acc, dt=0.016)

    cap = cv2.VideoCapture(camID)
    if not cap.isOpened():
        print("❌ Не удалось открыть камеру!")
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
    for _ in range(5):
        cap.read()

    last_frame_time = time.time()
    last_bt_send_time = 0
    BT_SEND_INTERVAL = 0.04

    last_direction = ""
    last_speed = -1

    print("🚀 Система запущена. ESC для выхода.")

    # BT Init
    BT_PORT = '/dev/rfcomm0'
    try:
        ser = serial.Serial(BT_PORT, 9600, timeout=0.05)
        print(f"✅ BT подключён к {BT_PORT}")
    except serial.SerialException as e:
        print(f"❌ Ошибка BT: {e}")
        return

    robot_tr = RobotTracker(
        [100, 80, 80], [140, 255, 255],
        tracker.M, tracker.scale_mm,
        filter_len=3   # ← было по умолчанию 5
    )

    STOP_DIST_MM = 20.0

    try:
        while True:
            now = time.time()
            dt = now - last_frame_time
            last_frame_time = now
            if dt > 0.1:
                dt = 0.033

            ret, frame = cap.read()
            if not ret:
                break

            frame_small = cv2.resize(frame, (640, 360))
            scale_x, scale_y = frame.shape[1] / 640.0, frame.shape[0] / 360.0

            tracker.set_dt(dt)

            target_mm, trajectory_px = tracker.get_prediction(frame_small)
            robot_mm, robot_px = robot_tr.get_position(frame_small)

            if robot_mm is not None and target_mm is not None:
                # ✅ Передаём реальный dt в контроллер
                robot_ctrl.set_dt(dt)

                # ✅ МЯГКАЯ синхронизация вместо жёсткой перезаписи
                # Модель "подтягивается" к реальной позиции, но не прыгает
                robot_ctrl.sync_position(robot_mm[0], alpha=0.3)

                # Расчёт скорости
                _, current_robot_vel = robot_ctrl.update_motion(target_mm[0])

                error_x = target_mm[0] - robot_mm[0]
                dist_x = abs(error_x)

                if dist_x < STOP_DIST_MM:
                    direction = "F"
                    speed = 0
                    # ✅ Важно: при остановке обнуляем и скорость в модели
                    robot_ctrl.current_vel = 0.0
                else:
                    speed = int(np.clip(current_robot_vel, 0, Max_Vel))
                    if speed > 0 and speed < MIN_MOTOR_PWM:
                        speed = MIN_MOTOR_PWM
                    direction = "B" if error_x > 0 else "F"

                # Троттлинг BT
                if (now - last_bt_send_time > BT_SEND_INTERVAL) or \
                (direction != last_direction) or \
                (abs(speed - last_speed) > 15):
                    try:
                        ser.write(f"{direction} {speed}\n".encode())
                        last_direction = direction
                        last_speed = speed
                        last_bt_send_time = now
                        print(f"[CMD] {direction} {speed:3d} | Err: {error_x:+6.1f}mm | Vel: {current_robot_vel:+6.1f}mm/s | dt: {dt*1000:.0f}ms")
                    except Exception as e:
                        print(f"⚠️ Ошибка отправки: {e}")
            else:
                if last_speed != 0:
                    try:
                        ser.write(b"F 0\n")
                        last_speed = 0
                        print("[INFO] Мяч или робот потерян! Робот остановлен.")
                    except Exception as e:
                        pass

            # Отрисовка
            debug_frame = tracker.draw_debug(frame, trajectory_px, scale_x, scale_y)

            # Отрисовка робота зелёным квадратом
            if robot_px is not None:
                x_px, y_px, r_px = robot_px
                x_orig = int(x_px * scale_x)
                y_orig = int(y_px * scale_y)
                r_orig = int(r_px * max(scale_x, scale_y))

                cv2.rectangle(debug_frame,
                            (x_orig - r_orig, y_orig - r_orig),
                            (x_orig + r_orig, y_orig + r_orig),
                            (0, 255, 0), 2)

                if robot_mm is not None:
                    cv2.putText(debug_frame, f"Robot: {robot_mm[0]:.0f}mm",
                              (x_orig - r_orig, y_orig - r_orig - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.imshow("Arkanoid Vision", debug_frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except KeyboardInterrupt:
        print("\n🛑 Программа прервана пользователем (Ctrl+C)")

    finally:
        print("🧹 Очистка ресурсов и остановка робота...")
        try:
            ser.write(b"F 0\n")
            time.sleep(0.1)
            ser.close()
            cap.release()
            cv2.destroyAllWindows()
            print("✅ Робот успешно остановлен, порт закрыт.")
        except Exception as e:
            print(f"⚠️ Не удалось отправить стоп при выходе: {e}")

if __name__ == "__main__":
    main()
