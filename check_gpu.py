import torch
import sys

print("=" * 50)
print("Проверка окружения PyTorch")
print("=" * 50)

print(f"Версия Python: {sys.version}")
print(f"Версия PyTorch: {torch.__version__}")
print(f"CUDA доступна: {torch.cuda.is_available()}")
print(f"Версия CUDA в PyTorch: {torch.version.cuda}")

if torch.cuda.is_available():
    print(f"\nДетали GPU:")
    print(f"Количество GPU: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"    Память: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
        print(f"    Вычислительная способность: {torch.cuda.get_device_properties(i).major}.{torch.cuda.get_device_properties(i).minor}")
else:
    print("\n❌ CUDA недоступна! Причины могут быть:")
    print("1. Не установлен CUDA Toolkit")
    print("2. Не установлен правильный драйвер NVIDIA")
    print("3. PyTorch установлен без поддержки CUDA")
    
print("\n" + "=" * 50)