from ultralytics import YOLO
import cv2
import os

def auto_label_with_yolo(images_folder, output_labels_folder):
    """Использует YOLOv8 для авторазметки, потом можно поправить вручную"""
    
    # Загружаем модель
    model = YOLO('yolov8n.pt')
    
    os.makedirs(output_labels_folder, exist_ok=True)
    
    # Проходим по всем изображениям
    for img_file in os.listdir(images_folder):
        if not img_file.endswith(('.jpg', '.jpeg', '.png')):
            continue
            
        img_path = os.path.join(images_folder, img_file)
        image = cv2.imread(img_path)
        h, w = image.shape[:2]
        
        # Детекция объектов
        results = model(img_path, conf=0.25, verbose=False)
        
        # Создаем файл разметки
        label_file = os.path.join(output_labels_folder, 
                                 os.path.splitext(img_file)[0] + '.txt')
        
        with open(label_file, 'w') as f:
            if results[0].boxes is not None:
                boxes = results[0].boxes.cpu().numpy()
                
                for i in range(len(boxes.cls)):
                    # Проверяем, что это мяч (класс 32)
                    if int(boxes.cls[i]) == 32:  # sports ball
                        x1, y1, x2, y2 = boxes.xyxy[i]
                        
                        # Конвертируем в YOLO формат
                        center_x = ((x1 + x2) / 2) / w
                        center_y = ((y1 + y2) / 2) / h
                        bbox_width = (x2 - x1) / w
                        bbox_height = (y2 - y1) / h
                        
                        # Записываем
                        f.write(f"0 {center_x:.6f} {center_y:.6f} {bbox_width:.6f} {bbox_height:.6f}\n")
        
        print(f"✅ Авторазметка: {img_file}")

# Запуск
auto_label_with_yolo("fitness_ball_dataset/images/train", 
                     "fitness_ball_dataset/labels/train")