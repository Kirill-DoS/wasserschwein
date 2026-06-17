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
Max_Acc = 600

def main():
    config = Config()
    required_files = ['perimeter.npy', 'left_wall.npy', 'right_wall.npy', 'robot_beam.npy']
    if not all(os.path.exists(f) for f in required_files):
        print("📐 Файлы геометрии не найдены. Запуск разметки...")
        PolygonMarker(camID).run()
    else:
        print("✅ Геометрия загружена.")

    print("🎨 Запуск калибровки цвета... ")
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
    tracker.curvature_k = physics.get("curvature_k", 0.00)
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
    BT_SEND_INTERVAL = 0.04  # Отправляем команды не чаще чем раз в 40 мс

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

    robot_tr = RobotTracker([100, 80, 80], [140, 255, 255], tracker.M, tracker.scale_mm)

    STOP_DIST_MM = 10.0  # Мертвая зона (в мм)

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

            # Теперь получаем 3 значения, включая флаг долгой потери
            target_mm, trajectory_px, is_lost_long_time = tracker.get_prediction(frame_small)
            robot_mm = robot_tr.get_position(frame_small)

            if robot_mm is not None and target_mm is not None:
                robot_ctrl.current_pos = robot_mm[0]

                # 🔴 ГЛАВНОЕ ИСПРАВЛЕНИЕ: Проверяем флаг долгой потери
                if is_lost_long_time:
                    # Мяч потерян давно - останавливаемся и сбрасываем скорость
                    if last_speed != 0:
                        try:
                            ser.write(b"F 0\n")
                            last_speed = 0
                            last_direction = "F"
                            robot_ctrl.current_vel = 0.0  # Сброс инерции контроллера
                            print(f"[INFO] Мяч потерян давно! Стоп. Lost: {is_lost_long_time}")
                        except Exception as e:
                            print(f"⚠️ Ошибка отправки: {e}")
                else:
                    # Мяч виден (или потерян недавно) - едем к предсказанной точке
                    ball_predicted_x = target_mm[0]
                    _, current_robot_vel = robot_ctrl.update_motion(ball_predicted_x)

                    error_x = ball_predicted_x - robot_mm[0]
                    dist_x = abs(error_x)

                    if dist_x < STOP_DIST_MM:
                        direction = "F"
                        speed = 0
                    else:
                        speed = int(np.clip(abs(current_robot_vel), 0, Max_Vel))
                        direction = "F" if current_robot_vel > 0 else "B"

                    # Троттлинг BT
                    if (now - last_bt_send_time > BT_SEND_INTERVAL) or (direction != last_direction) or (abs(speed - last_speed) > 15):
                        try:
                            ser.write(f"{direction} {speed}\n".encode())
                            last_direction = direction
                            last_speed = speed
                            last_bt_send_time = now
                            print(f"[CMD SENT] {direction} {speed:3d} | Err X: {error_x:+6.1f}mm | Lost: {is_lost_long_time}")
                        except Exception as e:
                            print(f"⚠️ Ошибка отправки: {e}")
            else:
                # Робот потерян из виду - экстренная остановка
                if last_speed != 0:
                    try:
                        ser.write(b"F 0\n")
                        last_speed = 0
                        robot_ctrl.current_vel = 0.0
                        print("[INFO] Робот потерян! Остановка.")
                    except Exception as e:
                        pass

            # Отрисовка графики
            debug_frame = tracker.draw_debug(frame, trajectory_px, scale_x, scale_y)

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
