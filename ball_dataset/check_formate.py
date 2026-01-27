import os
def check_labels(labels_folder):
    """Проверяет правильность разметки"""
    for label_file in os.listdir(labels_folder):
        if label_file.endswith('.txt'):
            path = os.path.join(labels_folder, label_file)
            with open(path, 'r') as f:
                content = f.read().strip()
                
            if not content:  # Пустой файл
                print(f"❌ Пустой файл: {label_file}")
                continue
            
            lines = content.split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) != 5:
                    print(f"❌ Неправильный формат в {label_file}: {line}")
                else:
                    # Проверяем, что значения от 0 до 1
                    values = list(map(float, parts[1:]))
                    if not all(0 <= v <= 1 for v in values):
                        print(f"⚠️  Значения вне диапазона в {label_file}: {values}")

# Проверяем
check_labels("fitness_ball_dataset/labels/train")
check_labels("fitness_ball_dataset/labels/val")