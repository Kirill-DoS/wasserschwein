import json
import time
from pathlib import Path

import cv2
import serial

from BallTracker import BallTracker
from ColorCalibrate import ColorCalibrator
from Config import Config
from Polygon import PolygonMarker
from RobotController import RobotController
from RobotTracker import RobotTracker


BASE_DIR = Path(__file__).resolve().parent
CAMERA_ID = 0
BT_PORT = "/dev/rfcomm0"
BT_BAUDRATE = 9600
COMMAND_RESEND_INTERVAL_S = 0.10
GEOMETRY_FILES = ("perimeter.npy", "left_wall.npy", "right_wall.npy", "robot_beam.npy", "geometry.json")


# Возвращает полный путь к файлу калибровки, чтобы запуск не зависел от текущей папки терминала.
def project_path(filename):
    return BASE_DIR / filename


# Настраивает камеру и оставляет единое разрешение для калибровки и рабочего трекинга.
def configure_camera(camera_id, camera_params):
    capture = cv2.VideoCapture(camera_id)
    if not capture.isOpened():
        raise RuntimeError(f"❌ Не удалось открыть камеру {camera_id}")

    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(camera_params["width"]))
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(camera_params["height"]))
    capture.set(cv2.CAP_PROP_FPS, int(camera_params["fps"]))
    for _ in range(5):
        capture.read()
    return capture


# Проверяет, что кадр камеры имеет то же разрешение, в котором была построена гомография.
def geometry_matches_frame(frame):
    metadata_path = project_path("geometry.json")
    try:
        with metadata_path.open("r", encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
    except (OSError, json.JSONDecodeError):
        return False

    return (
        metadata.get("frame_width") == frame.shape[1]
        and metadata.get("frame_height") == frame.shape[0]
    )


# Отправляет стоп-команду и возвращает результат записи в Bluetooth-порт.
def send_stop(serial_port):
    if serial_port is None or not serial_port.is_open:
        return False
    try:
        serial_port.write(b"S\n")
        return True
    except serial.SerialException as error:
        print(f"⚠️ Не удалось отправить стоп-команду: {error}")
        return False


# Отправляет одну строковую команду роботу и сообщает, удалось ли записать её в Bluetooth-порт.
def send_command(serial_port, direction, pwm):
    try:
        serial_port.write(f"{direction} {pwm}\n".encode("ascii"))
        return True
    except serial.SerialException as error:
        print(f"⚠️ Ошибка отправки команды: {error}")
        return False


# Запускает калибровку, трекинг и замкнутое управление кареткой робота.
def main():
    config = Config(project_path("config.json"))
    camera_params = config.get_camera_params()
    geometry_paths = [project_path(filename) for filename in GEOMETRY_FILES]

    if not all(path.exists() for path in geometry_paths):
        print("📐 Нет полной калибровки поля. Запускаю разметку.")
        PolygonMarker(
            CAMERA_ID,
            frame_size=(camera_params["width"], camera_params["height"]),
            output_dir=BASE_DIR,
        ).run()
        if not all(path.exists() for path in geometry_paths):
            raise RuntimeError("Калибровка не завершена: рабочий запуск отменён ради безопасности")

    calibrator = ColorCalibrator(
        CAMERA_ID,
        config=config,
        frame_size=(camera_params["width"], camera_params["height"]),
    )
    color_lower, color_upper = calibrator.calibrate()

    safety_params = config.get_safety_params()
    tracker = BallTracker(
        project_path("perimeter.npy"),
        project_path("left_wall.npy"),
        project_path("right_wall.npy"),
        project_path("robot_beam.npy"),
        detection_timeout_s=safety_params["ball_timeout_s"],
    )
    tracker.color_lower = color_lower
    tracker.color_upper = color_upper
    physics = config.get_physics_params()
    tracker.curvature_k = float(physics["curvature_k"])
    tracker.friction = float(physics["friction"])
    tracker.restitution = float(physics["restitution"])

    controller_params = config.get_controller_params()
    robot_controller = RobotController(
        max_speed_mm_s=controller_params["max_speed_mm_s"],
        max_acc_mm_s2=controller_params["max_acc_mm_s2"],
        max_pwm=controller_params["max_pwm"],
        deadband_mm=controller_params["deadband_mm"],
    )

    capture = None
    serial_port = None
    last_command = None
    last_command_time = 0.0
    last_frame_time = time.monotonic()
    tracking_was_lost = False

    try:
        capture = configure_camera(CAMERA_ID, camera_params)
        frame_ok, first_frame = capture.read()
        if not frame_ok:
            raise RuntimeError("❌ Камера не отдала первый кадр")
        if not geometry_matches_frame(first_frame):
            raise RuntimeError(
                "Разрешение камеры отличается от разметки. Удалите geometry.json и выполните калибровку заново."
            )

        serial_port = serial.Serial(BT_PORT, BT_BAUDRATE, timeout=0.05)
        print(f"✅ Bluetooth подключён: {BT_PORT} @ {BT_BAUDRATE}")
        robot_tracker = RobotTracker([100, 80, 80], [140, 255, 255], tracker.M, tracker.scale_mm)
        print("🚀 Система запущена. ESC — безопасная остановка.")

        while True:
            now = time.monotonic()
            dt = min(0.1, max(0.001, now - last_frame_time))
            last_frame_time = now

            frame_ok, frame = capture.read()
            if not frame_ok:
                print("⚠️ Камера перестала отдавать кадры")
                break

            tracker.set_dt(dt)
            target_mm, trajectory_px = tracker.get_prediction(frame, now)
            robot_mm = robot_tracker.get_position(frame)

            if target_mm is None or robot_mm is None:
                if not tracking_was_lost:
                    print("⚠️ Потерян мяч или робот — отправляю стоп-команду")
                tracking_was_lost = True
                robot_controller.reset()
                if last_command != ("S", 0):
                    if send_stop(serial_port):
                        last_command = ("S", 0)
                        last_command_time = now
            else:
                tracking_was_lost = False
                signed_speed_mm_s, pwm = robot_controller.update_motion(target_mm[0], robot_mm[0], dt)
                direction = "B" if signed_speed_mm_s > 0 else "F"
                command = (direction, pwm)
                command_changed = command != last_command
                if command_changed or now - last_command_time >= COMMAND_RESEND_INTERVAL_S:
                    if send_command(serial_port, direction, pwm):
                        last_command = command
                        last_command_time = now
                        if command_changed:
                            error_mm = target_mm[0] - robot_mm[0]
                            print(
                                f"[CMD] {direction} {pwm:3d} | ошибка: {error_mm:+6.1f} мм | "
                                f"скорость: {signed_speed_mm_s:+6.1f} мм/с"
                            )

            cv2.imshow("Arkanoid Vision", tracker.draw_debug(frame, trajectory_px))
            if cv2.waitKey(1) & 0xFF == 27:
                break
    except (RuntimeError, serial.SerialException) as error:
        print(f"❌ Запуск остановлен: {error}")
    except KeyboardInterrupt:
        print("\n🛑 Программа прервана пользователем")
    finally:
        send_stop(serial_port)
        if serial_port is not None and serial_port.is_open:
            serial_port.close()
        if capture is not None:
            capture.release()
        cv2.destroyAllWindows()
        print("🧹 Ресурсы освобождены, команда остановки отправлена")


if __name__ == "__main__":
    main()
