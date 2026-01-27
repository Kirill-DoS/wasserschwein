from ultralytics import YOLO
import os
import shutil
import yaml

def prepare_dataset(images_folder, output_folder='ball_dataset'):
    """
    Подготавливает структуру для обучения
    """
    # Создаем структуру папок
    folders = ['images/train', 'images/val', 'labels/train', 'labels/val']
    for folder in folders:
        os.makedirs(os.path.join(output_folder, folder), exist_ok=True)
    
    # Создаем файл конфигурации dataset.yaml
    dataset_config = {
        'path': os.path.abspath(output_folder),
        'train': 'images/train',
        'val': 'images/val',
        'nc': 81,  # 80 COCO классов + наш мяч
        'names': [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 
            'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 
            'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 
            'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 
            'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 
            'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 
            'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 
            'toothbrush',
            'fitness_ball'  # Наш 81-й класс
        ]
    }
    
    with open(os.path.join(output_folder, 'dataset.yaml'), 'w') as f:
        yaml.dump(dataset_config, f)
    
    print(f"✅ Структура датасета создана в {output_folder}")
    print(f"📁 Поместите изображения в {output_folder}/images/train/")
    print(f"📁 Поместите разметку в {output_folder}/labels/train/")
    
    return os.path.join(output_folder, 'dataset.yaml')

def train_model(data_yaml, epochs=50, imgsz=640):
    """
    Дообучает модель на новом классе
    """
    print("🚀 Начинаю дообучение модели...")
    
    # Загружаем предобученную модель
    model = YOLO('yolo11n.pt')
    
    # Дообучаем модель
    results = model.train(
        data=data_yaml,           # Конфиг датасета
        epochs=epochs,            # Количество эпох
        imgsz=imgsz,             # Размер изображения
        batch=16,                # Размер батча
        name='fitness_ball_v8',  # Имя эксперимента
        pretrained=True,         # Используем предобученные веса
        freeze=10,               # Замораживаем первые 10 слоев
        lr0=0.01,                # Начальная скорость обучения
        lrf=0.01,                # Финальная скорость обучения
        momentum=0.937,          # Момент
        weight_decay=0.0005,     # Вес декай
        warmup_epochs=3,         # Разогрев
        warmup_momentum=0.8,     # Момент разогрева
        box=7.5,                 # Вес loss для боксов
        cls=0.5,                 # Вес loss для классификации
        dfl=1.5,                 # Вес loss для DFL
        patience=50,             # Ранняя остановка
        device='cuda' if torch.cuda.is_available() else 'cpu',  # Используем GPU если есть
        workers=8,               # Количество воркеров
        amp=True,                # Используем автоматическую смешанную точность
        resume=False,            # Продолжить с чекпоинта
        seed=42,                 # Сид для воспроизводимости
        deterministic=True,      # Детерминированность
        verbose=True             # Вывод подробной информации
    )
    
    return results

if __name__ == "__main__":
    import torch
    
    print("="*60)
    print("ДООБУЧЕНИЕ YOLOv8 ДЛЯ ФИТНЕС-МЯЧА")
    print("="*60)
    
    # Проверяем GPU
    if torch.cuda.is_available():
        print(f"✅ GPU доступна: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️ GPU не найдена, обучение будет на CPU (медленно)")
    
    # Создаем структуру датасета
    data_yaml = prepare_dataset('your_images_folder')
    
    # Начинаем обучение
    print("\n📚 Для начала обучения:")
    print("1. Поместите ваши фото в папку fitness_ball_dataset/images/train/")
    print("2. Создайте файлы разметки в   fitness_ball_dataset/labels/train/")
    print("3. Запустите этот скрипт снова")
    
    # Если данные готовы, раскомментируйте следующую строку:
    train_model(data_yaml, epochs=50)