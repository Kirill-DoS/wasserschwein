import json
import numpy as np
from pathlib import Path

class Config:
    def __init__(self, filename="config.json"):
        self.filename = filename
        self.defaults = {
            "color_lower": [0, 100, 100],
            "color_upper": [15, 255, 255],
            "physics": {
                "curvature_k": 0.05,
                "friction": 0.015,
                "restitution": 0.82
            },
            "camera": {
                "width": 1280,
                "height": 720,
                "fps": 60
            }
        }
        self.config = self.load()

    def load(self):
        """Загрузка настроек из файла"""
        if Path(self.filename).exists():
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                print("⚠️ Ошибка загрузки конфига, использую значения по умолчанию")
                return self.defaults.copy()
        return self.defaults.copy()

    def save(self):
        """Сохранение настроек в файл"""
        with open(self.filename, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"✅ Настройки сохранены в {self.filename}")

    def get_color_bounds(self):
        """Получить границы цвета как numpy массивы"""
        lower = np.array(self.config.get("color_lower", self.defaults["color_lower"]))
        upper = np.array(self.config.get("color_upper", self.defaults["color_upper"]))
        return lower, upper

    def set_color_bounds(self, lower, upper):
        """Установить границы цвета"""
        self.config["color_lower"] = lower.tolist() if hasattr(lower, 'tolist') else list(lower)
        self.config["color_upper"] = upper.tolist() if hasattr(upper, 'tolist') else list(upper)

    def get_physics_params(self):
        """Получить физические параметры"""
        return self.config.get("physics", self.defaults["physics"])

    def update_physics(self, **kwargs):
        """Обновить физические параметры"""
        if "physics" not in self.config:
            self.config["physics"] = self.defaults["physics"]
        self.config["physics"].update(kwargs)
