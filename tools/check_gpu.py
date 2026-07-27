"""Диагностика GPU только для необязательных экспериментов с YOLO."""

import sys

import torch


# Печатает версию Python, состояние CUDA и свойства найденных видеокарт.
def main():
    print("=" * 50)
    print("Проверка окружения PyTorch")
    print("=" * 50)
    print(f"Версия Python: {sys.version}")
    print(f"Версия PyTorch: {torch.__version__}")
    print(f"CUDA доступна: {torch.cuda.is_available()}")
    print(f"Версия CUDA в PyTorch: {torch.version.cuda}")

    if torch.cuda.is_available():
        print("\nДетали GPU:")
        print(f"Количество GPU: {torch.cuda.device_count()}")
        for index in range(torch.cuda.device_count()):
            properties = torch.cuda.get_device_properties(index)
            print(f"  GPU {index}: {torch.cuda.get_device_name(index)}")
            print(f"    Память: {properties.total_memory / 1024**3:.1f} GB")
            print(f"    Вычислительная способность: {properties.major}.{properties.minor}")
    else:
        print("\nCUDA недоступна. Для обычного запуска робота GPU не требуется.")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
