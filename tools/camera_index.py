"""Поиск доступных камер OpenCV без изменения настроек робота."""

import argparse

import cv2


# Проверяет номера камер от нуля до указанной границы и печатает их реальные размеры кадра.
def find_cameras(scan_limit):
    found = []
    for index in range(scan_limit):
        capture = cv2.VideoCapture(index)
        if capture.isOpened():
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"Индекс {index}: {width}x{height}")
            found.append(index)
            capture.release()
        else:
            print(f"Индекс {index}: недоступен")
    return found


# Разбирает необязательную границу поиска и запускает диагностику камер.
def main():
    parser = argparse.ArgumentParser(description="Поиск доступных камер OpenCV")
    parser.add_argument("--limit", type=int, default=4, help="сколько индексов проверить начиная с 0")
    args = parser.parse_args()
    if args.limit <= 0:
        raise ValueError("--limit должен быть положительным числом")
    find_cameras(args.limit)


if __name__ == "__main__":
    main()
