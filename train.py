import argparse
import os
import shutil
from pathlib import Path

import torch
import yaml
from ultralytics import YOLO


# Создаёт структуру датасета с одним классом ball и при желании копирует исходные изображения в train.
def prepare_dataset(images_folder=None, output_folder="ball_dataset"):
    output_path = Path(output_folder).resolve()
    for folder in ("images/train", "images/val", "labels/train", "labels/val"):
        (output_path / folder).mkdir(parents=True, exist_ok=True)

    if images_folder:
        source_path = Path(images_folder)
        if not source_path.exists():
            raise FileNotFoundError(f"Папка с изображениями не найдена: {source_path}")
        for image_path in source_path.iterdir():
            if image_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                shutil.copy2(image_path, output_path / "images/train" / image_path.name)

    dataset_config = {
        "path": str(output_path),
        "train": "images/train",
        "val": "images/val",
        "nc": 1,
        "names": ["ball"],
    }
    dataset_path = output_path / "dataset.yaml"
    with dataset_path.open("w", encoding="utf-8") as dataset_file:
        yaml.safe_dump(dataset_config, dataset_file, allow_unicode=True, sort_keys=False)
    return dataset_path


# Запускает дообучение YOLO только после того, как оператор подготовил train и val разметку.
def train_model(data_yaml, epochs=50, imgsz=640):
    model = YOLO("yolo11n.pt")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=16,
        name="ball_detector",
        pretrained=True,
        freeze=10,
        patience=50,
        device=device,
        workers=8,
        amp=torch.cuda.is_available(),
        seed=42,
        deterministic=True,
    )


# Показывает безопасный интерфейс подготовки или явного запуска экспериментального обучения YOLO.
def main():
    parser = argparse.ArgumentParser(description="Подготовка и обучение отдельного детектора мяча")
    parser.add_argument("--output", default="ball_dataset")
    parser.add_argument("--images", help="Папка исходных изображений для train")
    parser.add_argument("--train", action="store_true", help="Явно запустить обучение")
    parser.add_argument("--epochs", default=50, type=int)
    args = parser.parse_args()

    dataset_path = prepare_dataset(args.images, args.output)
    print(f"✅ Структура датасета: {dataset_path}")
    if not args.train:
        print("Добавьте пары изображение/разметка в train и val, затем запустите с --train.")
        return
    train_model(dataset_path, epochs=args.epochs)


if __name__ == "__main__":
    main()
