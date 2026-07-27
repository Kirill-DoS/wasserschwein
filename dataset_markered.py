import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO


# Создаёт черновую YOLO-разметку одного класса ball, которую обязательно нужно проверить вручную.
def auto_label_with_yolo(images_folder, output_labels_folder):
    model = YOLO("yolo11n.pt")
    images_path = Path(images_folder)
    labels_path = Path(output_labels_folder)
    labels_path.mkdir(parents=True, exist_ok=True)

    for image_path in images_path.iterdir():
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"⚠️ Не удалось прочитать {image_path.name}")
            continue
        height, width = image.shape[:2]
        results = model(str(image_path), conf=0.25, verbose=False)
        label_path = labels_path / f"{image_path.stem}.txt"

        with label_path.open("w", encoding="utf-8") as label_file:
            boxes = results[0].boxes
            if boxes is None:
                continue
            classes = boxes.cls.cpu().numpy()
            coordinates = boxes.xyxy.cpu().numpy()
            for class_id, (x1, y1, x2, y2) in zip(classes, coordinates):
                if int(class_id) != 32:
                    continue
                center_x = ((x1 + x2) / 2) / width
                center_y = ((y1 + y2) / 2) / height
                box_width = (x2 - x1) / width
                box_height = (y2 - y1) / height
                label_file.write(f"0 {center_x:.6f} {center_y:.6f} {box_width:.6f} {box_height:.6f}\n")
        print(f"✅ Черновая разметка: {image_path.name}")


# Разбирает пути для запуска авторазметки без выполнения работы при простом импорте файла.
def main():
    parser = argparse.ArgumentParser(description="Черновая авторазметка мяча через YOLO")
    parser.add_argument("images_folder")
    parser.add_argument("output_labels_folder")
    args = parser.parse_args()
    auto_label_with_yolo(args.images_folder, args.output_labels_folder)


if __name__ == "__main__":
    main()
