import copy
import json
from pathlib import Path

import numpy as np


class Config:
    # Создаёт объект настроек и сразу загружает сохранённые значения, если они есть.
    def __init__(self, filename="config.json"):
        self.filename = Path(filename)
        self.defaults = {
            "color_lower": [0, 100, 100],
            "color_upper": [15, 255, 255],
            "physics": {
                "curvature_k": 0.05,
                "friction": 0.015,
                "restitution": 0.82,
            },
            "camera": {
                "width": 1280,
                "height": 720,
                "fps": 30,
            },
            "controller": {
                "max_speed_mm_s": 900.0,
                "max_acc_mm_s2": 1800.0,
                "deadband_mm": 20.0,
                "max_pwm": 255,
            },
            "safety": {
                "ball_timeout_s": 0.25,
            },
        }
        self.config = self.load()

    # Загружает JSON-файл или создаёт независимую копию настроек по умолчанию.
    def load(self):
        if not self.filename.exists():
            return copy.deepcopy(self.defaults)

        try:
            with self.filename.open("r", encoding="utf-8") as config_file:
                loaded_config = json.load(config_file)
        except (OSError, json.JSONDecodeError):
            print("⚠️ Ошибка загрузки конфига, использую значения по умолчанию")
            return copy.deepcopy(self.defaults)

        return self._merge_with_defaults(loaded_config, self.defaults)

    # Рекурсивно добавляет новые настройки, не уничтожая уже сохранённые пользовательские значения.
    def _merge_with_defaults(self, loaded_value, default_value):
        if not isinstance(loaded_value, dict) or not isinstance(default_value, dict):
            return loaded_value

        result = copy.deepcopy(default_value)
        for key, value in loaded_value.items():
            result[key] = self._merge_with_defaults(value, default_value.get(key, value))
        return result

    # Сохраняет все текущие настройки в UTF-8 JSON-файл.
    def save(self):
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        with self.filename.open("w", encoding="utf-8") as config_file:
            json.dump(self.config, config_file, ensure_ascii=False, indent=2)
        print(f"✅ Настройки сохранены в {self.filename}")

    # Возвращает HSV-границы цвета мяча как массивы NumPy.
    def get_color_bounds(self):
        lower = np.array(self.config["color_lower"], dtype=np.uint8)
        upper = np.array(self.config["color_upper"], dtype=np.uint8)
        return lower, upper

    # Сохраняет новые HSV-границы цвета мяча в памяти конфигурации.
    def set_color_bounds(self, lower, upper):
        self.config["color_lower"] = np.asarray(lower, dtype=int).tolist()
        self.config["color_upper"] = np.asarray(upper, dtype=int).tolist()

    # Возвращает параметры физической модели мяча.
    def get_physics_params(self):
        return self.config["physics"]

    # Обновляет отдельные параметры физической модели.
    def update_physics(self, **kwargs):
        self.config["physics"].update(kwargs)

    # Возвращает требуемые разрешение и частоту кадров камеры.
    def get_camera_params(self):
        return self.config["camera"]

    # Возвращает параметры регулятора движения каретки.
    def get_controller_params(self):
        return self.config["controller"]

    # Возвращает интервалы времени, используемые для безопасной остановки.
    def get_safety_params(self):
        return self.config["safety"]
