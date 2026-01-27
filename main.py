import cv2
import numpy as np
from ultralytics import YOLO
import torch
import time

class SmartBallTracker:
    def __init__(self):
        """
        Инициализация трекера мяча.
        Новый подход: ищем круги, а не полагаемся на YOLO
        """
        # Проверяем доступность GPU
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"⚙️  Устройство: {self.device.upper()}")
        
        # Все равно загружаем YOLO на всякий случай (можно использовать для других объектов)
        try:
            self.model = YOLO('yolo11n.pt').to(self.device)
            print("✅ YOLO модель загружена")
        except:
            print("⚠️  YOLO модель не загружена, используем только детекцию кругов")
            self.model = None
        
        # Настройки для детекции кругов
        self.min_radius = 25      # Минимальный радиус мяча в пикселях
        self.max_radius = 150     # Максимальный радиус мяча
        self.circle_threshold = 40  # Чем меньше, тем больше ложных срабатываний (30-50 оптимально)
        
        # Настройки цвета для оранжевого мяча (в HSV)
        # HSV: H - оттенок (0-180), S - насыщенность (0-255), V - яркость (0-255)
        self.orange_lower = np.array([5, 100, 100])    # Темно-оранжевый
        self.orange_upper = np.array([15, 255, 255])   # Ярко-оранжевый
        
        # Настройки сетки
        self.grid_size = 25  # Сетка 9x9 (не слишком мелкая, не слишком крупная)
        
        # Переменные для трекинга
        self.last_circle = None          # Последняя обнаруженная позиция мяча
        self.tracking_streak = 0         # Сколько кадров подряд видим мяч
        self.lost_streak = 0             # Сколько кадров не видим мяч
        self.max_lost_frames = 10        # Сколько кадров можем не видеть мяч до сброса трекинга
        
        # Статистика
        self.frame_count = 0
        self.detection_count = 0
        
        print("="*60)
        print("🎯 УМНЫЙ ТРЕКЕР МЯЧА")
        print("="*60)
        print("Новый подход: детекция кругов + цветовая фильтрация")
        print(f"📏 Диапапазон радиуса: {self.min_radius}-{self.max_radius}px")
        print(f"📊 Сетка: {self.grid_size}x{self.grid_size}")
        print("-"*60)
    
    def detect_circles(self, frame):
        """
        Находит все круги на изображении с помощью преобразования Хафа.
        Возвращает список кругов в формате (x, y, радиус).
        """
        # 1. Конвертируем в градации серого
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. Размываем для уменьшения шума
        blurred = cv2.medianBlur(gray, 5)
        
        # 3. Используем метод Хафа для поиска кругов
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=100,
            param2=self.circle_threshold,
            minRadius=self.min_radius,
            maxRadius=self.max_radius
        )
        
        if circles is not None:
            # Конвертируем в целые числа и округляем
            circles = np.uint16(np.around(circles[0]))
            # Преобразуем в список кортежей для удобства
            return [(int(c[0]), int(c[1]), int(c[2])) for c in circles]
        return []
    
    def check_circle_color(self, frame, circle):
        """
        Проверяет, является ли круг оранжевым.
        circle: (x, y, radius)
        Возвращает True если цвет соответствует оранжевому.
        """
        x, y, radius = circle
        
        # 1. Создаем маску для внутренней части круга (игнорируем границу в 5 пикселей)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), max(radius - 5, 1), 255, -1)
        
        # 2. Конвертируем область круга в HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 3. Создаем маску оранжевого цвета
        orange_mask = cv2.inRange(hsv, self.orange_lower, self.orange_upper)
        
        # 4. Применяем маску круга к оранжевой маске
        masked_orange = cv2.bitwise_and(orange_mask, orange_mask, mask=mask)
        
        # 5. Считаем процент оранжевых пикселей внутри круга
        total_pixels = np.sum(mask == 255)
        orange_pixels = np.sum(masked_orange == 255)
        
        if total_pixels > 0:
            orange_ratio = orange_pixels / total_pixels
            # Если более 40% пикселей внутри круга оранжевые - это наш мяч
            return orange_ratio > 0.4
        return False
    
    def find_best_ball(self, frame):
        """
        Находит лучший кандидат на мяч среди всех обнаруженных кругов.
        Использует комбинацию: размер + цвет + близость к предыдущей позиции.
        """
        # 1. Находим все круги
        circles = self.detect_circles(frame)
        
        if len(circles) == 0:
            return None
        
        best_circle = None
        best_score = -1
        
        # 2. Оцениваем каждый круг
        for circle in circles:
            x, y, radius = circle
            
            # Базовый балл за размер (предпочтение средним размерам)
            # ИСПРАВЛЕНО: используем float для вычислений
            size_diff = abs(float(radius) - 80.0) / 100.0
            size_score = max(0.0, 1.0 - size_diff)  # Ограничиваем снизу 0
            
            # Проверка цвета
            color_ok = self.check_circle_color(frame, circle)
            color_score = 1.0 if color_ok else 0.0
            
            # Бонус за близость к предыдущей позиции (если есть)
            proximity_score = 0.0
            if self.last_circle is not None:
                last_x, last_y, last_r = self.last_circle
                distance = np.sqrt((x - last_x)**2 + (y - last_y)**2)
                # Если близко к предыдущей позиции - даем бонус
                if distance < 100:  # В пределах 100 пикселей
                    proximity_score = max(0.0, 1.0 - distance / 100.0)
            
            # Итоговый балл (цвет самый важный)
            total_score = color_score * 0.6 + size_score * 0.2 + proximity_score * 0.2
            
            if color_ok and total_score > best_score:
                best_score = total_score
                best_circle = circle
        
        return best_circle  # Это будет либо None, либо кортеж (x, y, radius)
    
    def create_grid(self, img, grid_size):
        """Create grid for 25x25 (many lines)"""
        h, w = img.shape[:2]
        
        # Для 25x25 сетки делаем линии тоньше и светлее
        thin_color = (80, 80, 80)  # Темно-серый для тонких линий
        
        for i in range(1, grid_size):
            x = int(w * i / grid_size)
            y = int(h * i / grid_size)
            
            # Определяем цвет и толщину
            if i % 5 == 0:
                color = thin_color
                thickness = 1
            else:
                color = thin_color
                thickness = 1  # очень тонкие линии
            
            # Вертикальные линии
            cv2.line(img, (x, 0), (x, h), color, thickness)
            # Горизонтальные линии
            cv2.line(img, (0, y), (w, y), color, thickness)
        
        return img
    
    def get_grid_cell(self, x, y, width, height):
        """
        Определяет, в какой ячейке сетки находится точка.
        Возвращает номер ячейки и координаты (строка, столбец).
        """
        cell_w = width / self.grid_size
        cell_h = height / self.grid_size
        
        # Определяем столбец и строку (0-based)
        col = min(int(x / cell_w), self.grid_size - 1)
        row = min(int(y / cell_h), self.grid_size - 1)
        
        # Номер ячейки (1-based)
        cell_number = row * self.grid_size + col + 1
        
        return cell_number, (row, col)
    
    def draw_detection(self, frame, circle, cell_info):
        """
        Рисует обнаружение мяча на кадре.
        circle: (x, y, radius) - кортеж или список
        """
        # Извлекаем координаты из circle (может быть numpy массивом или кортежем)
        if isinstance(circle, np.ndarray):
            x, y, radius = int(circle[0]), int(circle[1]), int(circle[2])
        else:
            x, y, radius = circle
        
        cell_number, (row, col) = cell_info
        
        # 1. Рисуем внешний круг (зеленая граница)
        cv2.circle(frame, (x, y), radius, (0, 255, 0), 3)
        
        # 2. Рисуем внутренний круг (более тонкий)
        cv2.circle(frame, (x, y), max(radius - 3, 1), (0, 200, 100), 2)
        
        # 3. Рисуем центр мяча (желтая точка)
        cv2.circle(frame, (x, y), 8, (0, 255, 255), -1)
        
        # 4. Рисуем перекрестие в центре
        cv2.line(frame, (x - 15, y), (x + 15, y), (255, 255, 0), 2)
        cv2.line(frame, (x, y - 15), (x, y + 15), (255, 255, 0), 2)
        
        # 5. Добавляем текст с информацией
        info_text = f"Cell: {cell_number} R:{radius}px"
        cv2.putText(frame, info_text, 
                   (max(x - 70, 10), max(y - radius - 10, 30)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # 6. Добавляем номер ячейки в углу ячейки
        cell_w = frame.shape[1] / self.grid_size
        cell_h = frame.shape[0] / self.grid_size
        cell_x = int(col * cell_w + 10)
        cell_y = int(row * cell_h + 30)
        
        cv2.putText(frame, str(cell_number),
                   (cell_x, cell_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)
    
    def run_tracking(self):
        """
        Главный цикл трекинга.
        """
        # Открываем веб-камеру
        cap = cv2.VideoCapture(0)
        
        # Устанавливаем разрешение (квадратное для удобства)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Проверяем, открылась ли камера
        if not cap.isOpened():
            print("❌ Не удалось открыть камеру!")
            return
        
        print("\n🚀 Запуск трекинга...")
        print("Управление:")
        print("  G - изменить размер сетки (3-15)")
        print("  +/- - изменить чувствительность детекции кругов")
        print("  R - сбросить трекинг")
        print("  Q - выход")
        print("-"*60)
        
        # Переменные для FPS
        fps_start_time = time.time()
        fps_frame_count = 0
        
        while True:
            # Читаем кадр с камеры
            ret, frame = cap.read()
            if not ret:
                print("❌ Не удалось получить кадр")
                break
            
            self.frame_count += 1
            fps_frame_count += 1
            
            # Создаем копию кадра для отрисовки
            display = frame.copy()
            height, width = display.shape[:2]
            
            # 1. Рисуем сетку
            display = self.create_grid(display, self.grid_size)
            
            # 2. Ищем мяч
            ball_circle = self.find_best_ball(frame)
            
            # 3. Обновляем статистику трекинга
            # ИСПРАВЛЕНО: проверяем что ball_circle не None и не пустой
            if ball_circle is not None and len(ball_circle) == 3:
                # Нашли мяч
                self.detection_count += 1
                self.tracking_streak += 1
                self.lost_streak = 0
                self.last_circle = ball_circle
                
                # Определяем ячейку сетки
                x, y, radius = ball_circle
                cell_info = self.get_grid_cell(x, y, width, height)
                
                # Рисуем обнаружение
                self.draw_detection(display, ball_circle, cell_info)
                
                # Выводим информацию в консоль
                cell_number, (row, col) = cell_info
                print(f"\r✅ Мяч в ячейке {cell_number} | "
                      f"Позиция: ({x}, {y}) | "
                      f"Радиус: {radius}px | "
                      f"Трекинг: {self.tracking_streak} кадров", end="", flush=True)
            else:
                # Не нашли мяч
                self.lost_streak += 1
                self.tracking_streak = max(0, self.tracking_streak - 1)
                
                # Если долго не видим мяч, сбрасываем last_circle
                if self.lost_streak > self.max_lost_frames:
                    self.last_circle = None
                    print(f"\r🔍 Поиск мяча... (потерян {self.lost_streak} кадров)", end="", flush=True)
                else:
                    # Показываем последнюю известную позицию (если была)
                    if self.last_circle is not None and len(self.last_circle) == 3:
                        x, y, radius = self.last_circle
                        cell_info = self.get_grid_cell(x, y, width, height)
                        # Рисуем полупрозрачный круг на последней позиции
                        overlay = display.copy()
                        cv2.circle(overlay, (x, y), radius, (255, 165, 0), -1)  # Оранжевый
                        display = cv2.addWeighted(overlay, 0.3, display, 0.7, 0)
                        
                        cell_number, _ = cell_info
                        print(f"\r🟡 Предполагаемая позиция: ячейка {cell_number} "
                              f"(не видно {self.lost_streak} кадров)", end="", flush=True)
                    else:
                        print(f"\r🔍 Поиск мяча...", end="", flush=True)
            
            # 4. Отображаем информацию на кадре
            # FPS
            current_time = time.time()
            if current_time - fps_start_time >= 1.0:
                fps = fps_frame_count / (current_time - fps_start_time)
                fps_frame_count = 0
                fps_start_time = current_time
            else:
                fps = 0
            
            # Панель информации
            info_y = 40
            
            # ИСПРАВЛЕНО: правильная проверка наличия мяча
            has_ball = ball_circle is not None and len(ball_circle) == 3
            status_text = "✅ ТРЕКИНГ" if has_ball else "🔍 ПОИСК"
            
            info_lines = [
                f"Умный трекер мяча | FPS: {fps:.1f}",
                f"Сетка: {self.grid_size}x{self.grid_size} | Чувствительность: {self.circle_threshold}",
                f"Обнаружено: {self.detection_count}/{self.frame_count} кадров",
                f"Статус: {status_text}"
            ]
            
            for i, line in enumerate(info_lines):
                # Фон для текста
                text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                cv2.rectangle(display, 
                            (10, info_y + i * 30 - 25),
                            (20 + text_size[0], info_y + i * 30 + 5),
                            (40, 40, 40), -1)
                
                # Текст
                cv2.putText(display, line, 
                          (15, info_y + i * 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                          (255, 255, 0), 2)
            
            # 5. Показываем кадр
            cv2.imshow('Smart Ball Tracker', display)
            
            # 6. Обработка нажатий клавиш
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # Q или ESC
                print("\n\n⏹️  Выход по команде пользователя")
                break
            elif key == ord('g'):
                # Меняем размер сетки: 3, 5, 7, 9, 11, 13, 15
                sizes = [3, 5, 7, 9, 11, 13, 15]
                current_idx = sizes.index(self.grid_size) if self.grid_size in sizes else 3
                self.grid_size = sizes[(current_idx + 1) % len(sizes)]
                print(f"\n🔄 Сетка изменена: {self.grid_size}x{self.grid_size}")
            elif key == ord('+') or key == ord('='):
                # Увеличиваем чувствительность (меньше порог = больше ложных)
                self.circle_threshold = max(10, self.circle_threshold - 5)
                print(f"\n🔍 Чувствительность увеличена: {self.circle_threshold}")
            elif key == ord('-'):
                # Уменьшаем чувствительность (больше порог = меньше ложных)
                self.circle_threshold = min(100, self.circle_threshold + 5)
                print(f"\n🔍 Чувствительность уменьшена: {self.circle_threshold}")
            elif key == ord('r'):
                # Сброс трекинга
                self.last_circle = None
                self.tracking_streak = 0
                self.lost_streak = 0
                print(f"\n🔄 Трекинг сброшен")
        
        # Освобождаем ресурсы
        cap.release()
        cv2.destroyAllWindows()
        
        # Статистика
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА РАБОТЫ:")
        print(f"Всего кадров: {self.frame_count}")
        print(f"Обнаружено мячей: {self.detection_count}")
        if self.frame_count > 0:
            detection_rate = (self.detection_count / self.frame_count) * 100
            print(f"Процент обнаружения: {detection_rate:.1f}%")
        print("="*60)
        
        # Очищаем память GPU если использовали
        if self.device == 'cuda' and self.model is not None:
            torch.cuda.empty_cache()
            print("🧹 Память GPU очищена")

# Запуск программы
if __name__ == "__main__":
    # Создаем трекер
    tracker = SmartBallTracker()
    
    # Запускаем трекинг
    tracker.run_tracking()