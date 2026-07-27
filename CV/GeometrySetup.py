import numpy as np
import os

# Создаёт тестовые файлы геометрии только для демонстрации без настоящей калибровки камеры.
def check_or_create_files():
    files = {
        "homography.npy": np.eye(3), # Заглушка: единичная матрица
        "wall_l.npy": np.array([[10, 10], [10, 500]]),
        "wall_r.npy": np.array([[600, 10], [600, 500]]),
        "beam.npy": np.array([[10, 550], [600, 550]])
    }
    for name, data in files.items():
        if not os.path.exists(name):
            print(f"Создаю файл-заглушку: {name}")
            np.save(name, data)
