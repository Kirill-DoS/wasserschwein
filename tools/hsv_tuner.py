"""Отдельная настройка HSV-диапазона мяча через общую конфигурацию .env."""

from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vision.config import Config


# Создаёт ползунок OpenCV; изменение считывается в основном цикле, поэтому обработчик пустой.
def on_trackbar_change(_value):
    pass


# Читает положение шести ползунков и возвращает нижнюю и верхнюю HSV-границы.
def read_bounds():
    lower = np.array(
        [
            cv2.getTrackbarPos("H_min", "HSV мяча"),
            cv2.getTrackbarPos("S_min", "HSV мяча"),
            cv2.getTrackbarPos("V_min", "HSV мяча"),
        ],
        dtype=np.uint8,
    )
    upper = np.array(
        [
            cv2.getTrackbarPos("H_max", "HSV мяча"),
            cv2.getTrackbarPos("S_max", "HSV мяча"),
            cv2.getTrackbarPos("V_max", "HSV мяча"),
        ],
        dtype=np.uint8,
    )
    return lower, upper


# Открывает камеру из .env, показывает маску мяча и сохраняет диапазон по клавише S.
def main():
    config = Config(Path(__file__).resolve().parent.parent / ".env")
    camera_params = config.get_camera_params()
    lower, upper = config.get_ball_color_bounds()
    capture = cv2.VideoCapture(config.get_camera_id())
    if not capture.isOpened():
        raise RuntimeError("Не удалось открыть камеру из CAMERA_ID")

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, camera_params["width"])
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_params["height"])
    cv2.namedWindow("HSV мяча")
    for name, value, maximum in (
        ("H_min", int(lower[0]), 180),
        ("S_min", int(lower[1]), 255),
        ("V_min", int(lower[2]), 255),
        ("H_max", int(upper[0]), 180),
        ("S_max", int(upper[1]), 255),
        ("V_max", int(upper[2]), 255),
    ):
        cv2.createTrackbar(name, "HSV мяча", value, maximum, on_trackbar_change)

    print("Нажмите S, чтобы сохранить HSV в .env; Q или Esc — чтобы выйти без сохранения.")
    try:
        while True:
            frame_ok, frame = capture.read()
            if not frame_ok:
                raise RuntimeError("Камера перестала отдавать кадры")
            lower, upper = read_bounds()
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower, upper)
            cv2.imshow("Камера", frame)
            cv2.imshow("HSV маска", mask)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                return
            if key in (ord("s"), ord("ы")):
                config.set_ball_color_bounds(lower, upper)
                print("✅ Диапазон мяча сохранён в .env")
                return
    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
