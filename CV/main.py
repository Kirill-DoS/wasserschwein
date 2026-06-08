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

camID = 0
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
    for _ in range(5): cap.read()

    last_frame_time = time.time()
    last_bt_send_time = 0
    BT_SEND_INTERVAL = 0.04  # Отправляем команды не чаще чем раз в 40 мс, чтобы не забить буфер BT

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

    STOP_DIST_MM = 20.0     # Мертвая зона (в мм). Если погрешность меньше 2 см, робот не дергается
    KP = 1.3                # Коэффициент пропорциональности регулятора скорости

    try:
        while True:
            now = time.time()
            dt = now - last_frame_time
            last_frame_time = now
            if dt > 0.1: dt = 0.033

            ret, frame = cap.read()
            if not ret: break

            frame_small = cv2.resize(frame, (640, 360))
            scale_x, scale_y = frame.shape[1] / 640.0, frame.shape[0] / 360.0

            tracker.set_dt(dt)

            # target_mm возвращается СРАЗУ В МИЛЛИМЕТРАХ
            target_mm, trajectory_px = tracker.get_prediction(frame_small) # target point
            robot_mm = robot_tr.get_position(frame_small)

            ball_predicted_x =target_mm[0]
            current_robot_x, current_robot_vel = robot_ctrl.update_motion(ball_predicted_x)

            if robot_mm is not None and target_mm is not None:

                robot_ctrl.current_pos = robot_mm[0]
                ball_predicted_x = target_mm[0]
                _, current_robot_vel = robot_ctrl.update_motion(ball_predicted_x)

                error_x = ball_predicted_x - robot_mm[0]
                dist_x = abs(error_x)

                if dist_x < STOP_DIST_MM:
                    direction = "F"
                    speed = 0
                else:
                    # 4. ВАЖНО: Вместо KP * dist_x мы берем готовую плавную скорость из трапеции!
                    # Округляем её до целого числа для отправки роботу
                    speed = int(np.clip(current_robot_vel, 0, Max_Vel))
                    direction = "B" if error_x > 0 else "F"

                # Троттлинг BT: Отправляем команду только если прошел интервал времени
                # И ТОЛЬКО если параметры скорости или направления реально изменились
                if (now - last_bt_send_time > BT_SEND_INTERVAL) or (direction != last_direction) or (abs(speed - last_speed) > 15):
                    try:
                        ser.write(f"{direction} {speed}\n".encode())
                        last_direction = direction
                        last_speed = speed
                        last_bt_send_time = now
                        print(f"[CMD SENT] {direction} {speed:3d} | Err X: {error_x:+6.1f}mm")
                    except Exception as e:
                        print(f"⚠️ Ошибка отправки: {e}")
            else:
                if last_speed != 0:
                    try:
                        ser.write(b"F 0\n") # или f"F 0\n".encode()
                        last_speed = 0
                        print("[INFO] Мяч потерян! Робот остановлен.")
                    except Exception as e:
                        pass

            # Отрисовка графики (draw_debug принимает trajectory_px, внутри масштабирует под оригинальный frame)
            debug_frame = tracker.draw_debug(frame, trajectory_px, scale_x, scale_y)

            cv2.imshow("Arkanoid Vision", debug_frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except KeyboardInterrupt:
        print("\n🛑 Программа прервана пользователем (Ctrl+C)")

    finally:
        # Этот блок выполнится В ЛЮБОМ СЛУЧАЕ при выходе из try
        print("🧹 Очистка ресурсов и остановка робота...")
        try:
            # Отправляем команду стоп. Убедись, что формат совпадает с прошивкой ("F 0\n")
            ser.write(b"F 0\n")
            time.sleep(0.1) # Даем времени Bluetooth-модулю физически отправить байты
            ser.close()     # Закрываем порт
            cap.release()
            cv2.destroyAllWindows()
            ser.close()
            print("✅ Робот успешно остановлен, порт закрыт.")
        except Exception as e:
            print(f"⚠️ Не удалось отправить стоп при выходе: {e}")

if __name__ == "__main__":
    main()
