import os
from pathlib import Path

import numpy as np


# Загружает пары KEY=VALUE из .env и возвращает их без внешних библиотек.
def load_env_file(env_path):
    values = {}
    with Path(env_path).open("r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", maxsplit=1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


# Перезаписывает или добавляет одно значение в .env, сохраняя остальные комментарии и строки.
def set_env_value(env_path, key, value):
    path = Path(env_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    replacement = f"{key}={value}"
    for index, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[index] = replacement
            break
    else:
        lines.append(replacement)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class Config:
    # Загружает все рабочие настройки из корневого .env и не использует скрытые значения в коде.
    def __init__(self, env_path=None):
        root_dir = Path(__file__).resolve().parent.parent
        self.env_path = Path(env_path) if env_path else root_dir / ".env"
        if not self.env_path.exists():
            raise FileNotFoundError(
                f"Не найден {self.env_path}. Скопируйте .env.example в .env и заполните настройки."
            )
        self.values = load_env_file(self.env_path)
        os.environ.update(self.values)

    # Возвращает обязательное значение .env или объясняет, какое имя нужно добавить.
    def _get(self, key):
        try:
            return self.values[key]
        except KeyError as error:
            raise KeyError(f"В .env отсутствует обязательная настройка {key}") from error

    # Возвращает целочисленную настройку из .env.
    def _get_int(self, key):
        return int(self._get(key))

    # Возвращает вещественную настройку из .env.
    def _get_float(self, key):
        return float(self._get(key))

    # Преобразует строку формата 0,184,100 в HSV-массив OpenCV.
    def _get_hsv(self, key):
        values = [int(part.strip()) for part in self._get(key).split(",")]
        if len(values) != 3 or any(value < 0 or value > 255 for value in values):
            raise ValueError(f"{key} должен содержать три значения HSV от 0 до 255")
        return np.array(values, dtype=np.uint8)

    # Возвращает номер USB-камеры.
    def get_camera_id(self):
        return self._get_int("CAMERA_ID")

    # Возвращает разрешение и частоту кадров камеры.
    def get_camera_params(self):
        return {
            "width": self._get_int("CAMERA_WIDTH"),
            "height": self._get_int("CAMERA_HEIGHT"),
            "fps": self._get_int("CAMERA_FPS"),
        }

    # Возвращает путь и скорость Bluetooth-порта.
    def get_bluetooth_params(self):
        return {
            "port": self._get("BT_PORT"),
            "baudrate": self._get_int("BT_BAUDRATE"),
            "resend_interval_s": self._get_float("COMMAND_RESEND_INTERVAL_S"),
        }

    # Возвращает HSV-границы цвета мяча.
    def get_ball_color_bounds(self):
        return self._get_hsv("BALL_HSV_LOWER"), self._get_hsv("BALL_HSV_UPPER")

    # Сохраняет выбранный оператором HSV-диапазон мяча обратно в .env.
    def set_ball_color_bounds(self, lower, upper):
        lower_text = ",".join(map(str, np.asarray(lower, dtype=int).tolist()))
        upper_text = ",".join(map(str, np.asarray(upper, dtype=int).tolist()))
        set_env_value(self.env_path, "BALL_HSV_LOWER", lower_text)
        set_env_value(self.env_path, "BALL_HSV_UPPER", upper_text)
        self.values["BALL_HSV_LOWER"] = lower_text
        self.values["BALL_HSV_UPPER"] = upper_text

    # Возвращает HSV-границы цветной метки робота.
    def get_robot_color_bounds(self):
        return self._get_hsv("ROBOT_HSV_LOWER"), self._get_hsv("ROBOT_HSV_UPPER")

    # Возвращает размеры настоящего и виртуального поля для преобразования координат.
    def get_field_params(self):
        return {
            "width_mm": self._get_float("FIELD_WIDTH_MM"),
            "height_mm": self._get_float("FIELD_HEIGHT_MM"),
            "virtual_width": self._get_int("VIRTUAL_FIELD_WIDTH"),
            "virtual_height": self._get_int("VIRTUAL_FIELD_HEIGHT"),
        }

    # Возвращает параметры прогноза движения мяча.
    def get_physics_params(self):
        return {
            "curvature_k": self._get_float("BALL_CURVATURE_K"),
            "friction": self._get_float("BALL_FRICTION"),
            "restitution": self._get_float("BALL_RESTITUTION"),
        }

    # Возвращает пороги обнаружения и параметры короткого прогноза мяча.
    def get_ball_tracker_params(self):
        return {
            "max_sim_steps": self._get_int("BALL_MAX_SIM_STEPS"),
            "history_length": self._get_int("BALL_HISTORY_LENGTH"),
            "min_radius_px": self._get_float("BALL_MIN_RADIUS_PX"),
            "max_radius_px": self._get_float("BALL_MAX_RADIUS_PX"),
            "min_area_px": self._get_float("BALL_MIN_AREA_PX"),
            "min_circularity": self._get_float("BALL_MIN_CIRCULARITY"),
            "min_prediction_speed_mm_s": self._get_float("BALL_MIN_PREDICTION_SPEED_MM_S"),
            "stop_speed_mm_s": self._get_float("BALL_STOP_SPEED_MM_S"),
        }

    # Возвращает параметры поиска цветной метки каретки.
    def get_robot_tracker_params(self):
        return {
            "filter_length": self._get_int("ROBOT_TRACKER_FILTER_LENGTH"),
            "min_radius_px": self._get_float("ROBOT_MIN_RADIUS_PX"),
            "max_radius_px": self._get_float("ROBOT_MAX_RADIUS_PX"),
        }

    # Возвращает параметры ограничения скорости и ускорения каретки.
    def get_controller_params(self):
        return {
            "max_speed_mm_s": self._get_float("CONTROLLER_MAX_SPEED_MM_S"),
            "max_acc_mm_s2": self._get_float("CONTROLLER_MAX_ACC_MM_S2"),
            "deadband_mm": self._get_float("CONTROLLER_DEADBAND_MM"),
            "max_pwm": self._get_int("MOTOR_MAX_PWM"),
        }

    # Возвращает время, после которого потеря мяча считается опасной.
    def get_safety_params(self):
        return {"ball_timeout_s": self._get_float("BALL_TIMEOUT_S")}

    # Возвращает параметры необязательных экспериментов YOLO из того же .env.
    def get_ml_params(self):
        return {
            "model": self._get("YOLO_MODEL"),
            "confidence": self._get_float("YOLO_CONFIDENCE"),
            "default_epochs": self._get_int("YOLO_DEFAULT_EPOCHS"),
            "image_size": self._get_int("YOLO_IMAGE_SIZE"),
            "batch_size": self._get_int("YOLO_BATCH_SIZE"),
            "freeze_layers": self._get_int("YOLO_FREEZE_LAYERS"),
            "patience": self._get_int("YOLO_PATIENCE"),
            "workers": self._get_int("YOLO_WORKERS"),
            "validation_fraction": self._get_float("YOLO_VALIDATION_FRACTION"),
            "random_seed": self._get_int("YOLO_RANDOM_SEED"),
        }
