import os
import shutil
import random

# Пути
train_labels = "fitness_ball_dataset/labels/train"
val_labels = "fitness_ball_dataset/labels/val"

# Создаем папку val если нет
os.makedirs(val_labels, exist_ok=True)

# Получаем все файлы разметки
all_label_files = [f for f in os.listdir(train_labels) if f.endswith('.txt')]

# Берем 20% для валидации
val_count = max(1, int(len(all_label_files) * 0.2))
val_files = random.sample(all_label_files, val_count)

# Копируем файлы в val
for file in val_files:
    src = os.path.join(train_labels, file)
    dst = os.path.join(val_labels, file)
    shutil.copy2(src, dst)
    print(f"📄 Скопирован: {file}")

print(f"\n✅ Создано {len(val_files)} файлов разметки в val/")