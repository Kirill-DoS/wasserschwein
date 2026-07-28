import json
import time
from pathlib import Path

import cv2
import serial

try:
    from .ball_tracker import BallTracker
    from .color_calibrate import ColorCalibrator
    from .config import Config
    from .polygon import PolygonMarker
    from .robot_controller import RobotController
    from .robot_tracker import RobotTracker
except ImportError:
    from ball_tracker import BallTracker
    from color_calibrate import ColorCalibrator
    from config import Config
    from polygon import PolygonMarker
    from robot_controller import RobotController
    from robot_tracker import RobotTracker


BASE_DIR = Path(__file__).resolve().parent
GEOMETRY_FILES = ("perimeter.npy", "left_wall.npy", "right_wall.npy", "robot_beam.npy", "geometry.json")


# Возвращает полный путь к файлу калибровки, чтобы запуск не зависел от текущей папки терминала.
def calibration_path(filename):
    return BASE_DIR / "calibration" / filename


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
    metadata_path = calibration_path("geometry.json")
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
    config = Config(BASE_DIR.parent / ".env")
    camera_id = config.get_camera_id()
    camera_params = config.get_camera_params()
    bluetooth_params = config.get_bluetooth_params()
    field_params = config.get_field_params()
    geometry_paths = [calibration_path(filename) for filename in GEOMETRY_FILES]

    if not all(path.exists() for path in geometry_paths):
        print("📐 Нет полной калибровки поля. Запускаю разметку.")
        PolygonMarker(
            camera_id,
            frame_size=(camera_params["width"], camera_params["height"]),
            virtual_field_size=(field_params["virtual_width"], field_params["virtual_height"]),
            output_dir=BASE_DIR / "calibration",
        ).run()
        if not all(path.exists() for path in geometry_paths):
            raise RuntimeError("Калибровка не завершена: рабочий запуск отменён ради безопасности")

    calibrator = ColorCalibrator(
        camera_id,
        config=config,
        frame_size=(camera_params["width"], camera_params["height"]),
    )
    color_lower, color_upper = calibrator.calibrate()

    safety_params = config.get_safety_params()
    physics_params = config.get_physics_params()
    ball_tracker_params = config.get_ball_tracker_params()
    tracker = BallTracker(
        calibration_path("perimeter.npy"),
        calibration_path("left_wall.npy"),
        calibration_path("right_wall.npy"),
        calibration_path("robot_beam.npy"),
        detection_timeout_s=safety_params["ball_timeout_s"],
        field_size_mm=(field_params["width_mm"], field_params["height_mm"]),
        virtual_field_size=(field_params["virtual_width"], field_params["virtual_height"]),
        physics_params=physics_params,
        tracker_params=ball_tracker_params,
        color_lower=color_lower,
        color_upper=color_upper,
    )

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
        capture = configure_camera(camera_id, camera_params)
        frame_ok, first_frame = capture.read()
        if not frame_ok:
            raise RuntimeError("❌ Камера не отдала первый кадр")
        if not geometry_matches_frame(first_frame):
            raise RuntimeError(
                "Разрешение камеры отличается от разметки. Удалите geometry.json и выполните калибровку заново."
            )

        serial_port = serial.Serial(bluetooth_params["port"], bluetooth_params["baudrate"], timeout=0.05)
        print(f"✅ Bluetooth подключён: {bluetooth_params['port']} @ {bluetooth_params['baudrate']}")
        robot_lower, robot_upper = config.get_robot_color_bounds()
        robot_tracker = RobotTracker(
            robot_lower,
            robot_upper,
            tracker.M,
            tracker.scale_mm,
            config.get_robot_tracker_params(),
        )
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
                if command_changed or now - last_command_time >= bluetooth_params["resend_interval_s"]:
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
