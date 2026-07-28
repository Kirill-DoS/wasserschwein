import argparse
import shutil
from pathlib import Path
import sys

import torch
import yaml
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from vision.config import Config


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
def train_model(data_yaml, model_name, epochs, image_size, batch_size, freeze_layers, patience, workers, seed):
    model = YOLO(model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=image_size,
        batch=batch_size,
        name="ball_detector",
        pretrained=True,
        freeze=freeze_layers,
        patience=patience,
        device=device,
        workers=workers,
        amp=torch.cuda.is_available(),
        seed=seed,
        deterministic=True,
    )


# Показывает безопасный интерфейс подготовки или явного запуска экспериментального обучения YOLO.
def main():
    config = Config(Path(__file__).resolve().parents[2] / ".env")
    ml_params = config.get_ml_params()
    parser = argparse.ArgumentParser(description="Подготовка и обучение отдельного детектора мяча")
    parser.add_argument("--output", default="ball_dataset")
    parser.add_argument("--images", help="Папка исходных изображений для train")
    parser.add_argument("--train", action="store_true", help="Явно запустить обучение")
    parser.add_argument("--epochs", default=ml_params["default_epochs"], type=int)
    args = parser.parse_args()

    dataset_path = prepare_dataset(args.images, args.output)
    print(f"✅ Структура датасета: {dataset_path}")
    if not args.train:
        print("Добавьте пары изображение/разметка в train и val, затем запустите с --train.")
        return
    train_model(
        dataset_path,
        ml_params["model"],
        args.epochs,
        ml_params["image_size"],
        ml_params["batch_size"],
        ml_params["freeze_layers"],
        ml_params["patience"],
        ml_params["workers"],
        ml_params["random_seed"],
    )


if __name__ == "__main__":
    main()
