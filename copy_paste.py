import argparse
import random
import shutil
from pathlib import Path


# Копирует случайную часть пар «изображение + разметка» из train в val для экспериментов YOLO.
def create_validation_split(dataset_root, fraction=0.2, seed=42):
    root = Path(dataset_root)
    train_images = root / "images/train"
    train_labels = root / "labels/train"
    val_images = root / "images/val"
    val_labels = root / "labels/val"
    val_images.mkdir(parents=True, exist_ok=True)
    val_labels.mkdir(parents=True, exist_ok=True)

    pairs = []
    for label_path in train_labels.glob("*.txt"):
        image_path = next(
            (
                train_images / f"{label_path.stem}{suffix}"
                for suffix in (".jpg", ".jpeg", ".png")
                if (train_images / f"{label_path.stem}{suffix}").exists()
            ),
            None,
        )
        if image_path is not None:
            pairs.append((image_path, label_path))

    if len(pairs) < 2:
        raise ValueError("Для разделения нужны минимум две пары изображение/разметка")

    random.Random(seed).shuffle(pairs)
    count = max(1, round(len(pairs) * fraction))
    for image_path, label_path in pairs[:count]:
        shutil.copy2(image_path, val_images / image_path.name)
        shutil.copy2(label_path, val_labels / label_path.name)
    print(f"✅ В validation скопировано {count} пар")


# Принимает параметры командной строки для создания validation-выборки.
def main():
    parser = argparse.ArgumentParser(description="Создание validation-выборки YOLO")
    parser.add_argument("dataset_root")
    parser.add_argument("--fraction", type=float, default=0.2)
    args = parser.parse_args()
    create_validation_split(args.dataset_root, args.fraction)


if __name__ == "__main__":
    main()
