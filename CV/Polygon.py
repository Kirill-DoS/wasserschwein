import cv2
import numpy as np
import os

class PolygonMarker:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.points = []
        self.frame = None
        self.temp_frame = None
        self.current_label = ""
        self.required_points = 0
        
        # Открываем камеру
        self._init_camera()
        
        cv2.namedWindow("Marking Tool", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Marking Tool", self._mouse_callback)
    
    def _init_camera(self):
        """Инициализация камеры"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"ОШИБКА: Не удалось открыть камеру {self.camera_id}")
            return False
        
        # Устанавливаем разрешение (опционально)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Получаем первый кадр
        ret, frame = self.cap.read()
        if ret:
            self.frame = frame.copy()
            print(f"✓ Камера инициализирована: {frame.shape[1]}x{frame.shape[0]}")
            return True
        else:
            print("ОШИБКА: Не удалось получить кадр с камеры")
            return False

    def _mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))
            
            # Обновляем временный кадр
            self.temp_frame = self.frame.copy()
            
            # Рисуем все точки
            for i, point in enumerate(self.points):
                cv2.circle(self.temp_frame, point, 5, (0, 255, 0), -1)
                if i > 0:
                    cv2.line(self.temp_frame, self.points[i-1], point, (0, 255, 0), 2)
            
            # Если набрано 4 точки, рисуем замкнутый контур
            if len(self.points) == 4:
                pts = np.array(self.points).reshape((-1, 1, 2))
                cv2.polylines(self.temp_frame, [pts], True, (0, 255, 0), 2)
            
            # Показываем информацию
            info_text = f"{self.current_label}: {len(self.points)}/{self.required_points} точек"
            cv2.putText(self.temp_frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(self.temp_frame, "ESC - отмена | U - отменить последнюю", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            cv2.imshow("Marking Tool", self.temp_frame)
            print(f"  Точка {len(self.points)}: ({x}, {y})")

    def _calculate_homography(self, src_points):
        """Рассчитывает матрицу гомографии из исходных точек в целевые"""
        if len(src_points) != 4:
            print(f"Ошибка: для гомографии нужно 4 точки, получено {len(src_points)}")
            return None
        
        src = np.array(src_points, dtype=np.float32)
        
        # Определяем целевые точки для стандартного прямоугольника
        width = 800
        height = 600
        
        dst = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype=np.float32)
        
        # Вычисляем гомографию
        H, _ = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        return H

    def mark_zone(self, label, count, filename, calculate_homography=False):
        """Разметка зоны"""
        print(f"\n{'='*50}")
        print(f"Разметка: {label}")
        print(f"Нужно отметить: {count} точек")
        print(f"{'='*50}")
        
        self.points = []
        self.current_label = label
        self.required_points = count
        
        # Получаем текущий кадр с камеры
        ret, frame = self.cap.read()
        if not ret:
            print("ОШИБКА: Не удалось получить кадр с камеры")
            return False
        
        self.frame = frame.copy()
        self.temp_frame = self.frame.copy()
        
        # Добавляем информационную строку
        info_text = f"{label}: кликните {count} раз(а)"
        cv2.putText(self.temp_frame, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(self.temp_frame, "ESC - отмена | U - отменить последнюю", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        cv2.imshow("Marking Tool", self.temp_frame)
        
        print("\nУправление:")
        print("  • ЛКМ - добавить точку")
        print("  • U   - отменить последнюю точку")
        print("  • ESC - отменить текущую разметку")
        print(f"\nНачинаем разметку {label}...")
        
        while len(self.points) < count:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                print(f"\n✗ Разметка {label} отменена")
                return False
            elif key == ord('u') and len(self.points) > 0:  # U - отмена последней точки
                self.points.pop()
                # Перерисовываем
                self.temp_frame = self.frame.copy()
                for i, point in enumerate(self.points):
                    cv2.circle(self.temp_frame, point, 5, (0, 255, 0), -1)
                    if i > 0:
                        cv2.line(self.temp_frame, self.points[i-1], point, (0, 255, 0), 2)
                if len(self.points) == 4:
                    pts = np.array(self.points).reshape((-1, 1, 2))
                    cv2.polylines(self.temp_frame, [pts], True, (0, 255, 0), 2)
                
                info_text = f"{label}: {len(self.points)}/{count} точек"
                cv2.putText(self.temp_frame, info_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(self.temp_frame, "ESC - отмена | U - отменить последнюю", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
                cv2.imshow("Marking Tool", self.temp_frame)
                print(f"  Отменена последняя точка. Осталось: {len(self.points)} точек")
        
        print(f"\n✓ Собрано {len(self.points)} точек для {label}")
        
        # Сохранение данных
        data = np.array(self.points)
        
        if calculate_homography and count == 4:
            H = self._calculate_homography(data)
            if H is not None:
                np.save(filename, H)
                print(f"✓ Гомографическая матрица сохранена в {filename}")
                print(f"  Размер матрицы: {H.shape}")
                print(f"  Матрица:\n{H}")
            else:
                print(f"✗ Не удалось рассчитать гомографию для {label}")
                return False
        else:
            np.save(filename, data)
            print(f"✓ Точки сохранены в {filename}")
            print(f"  Координаты точек:\n{data}")
        
        # Фиксация разметки (рисуем синим на финальном кадре)
        self._draw_final_zone(data)
        return True

    def _draw_final_zone(self, data):
        """Отрисовка финальной разметки на кадре"""
        if len(data) == 2:
            cv2.line(self.frame, tuple(data[0]), tuple(data[1]), (255, 0, 0), 3)
            for point in data:
                cv2.circle(self.frame, tuple(point), 6, (255, 0, 0), -1)
        elif len(data) == 4:
            pts = data.reshape((-1, 1, 2))
            cv2.polylines(self.frame, [pts], True, (255, 0, 0), 3)
            for i, point in enumerate(data):
                cv2.circle(self.frame, tuple(point), 6, (255, 0, 0), -1)
                cv2.putText(self.frame, str(i+1), (point[0]+5, point[1]-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    def run(self):
        """Запуск процесса разметки"""
        if self.cap is None or not self.cap.isOpened():
            print("\n❌ Невозможно начать разметку: камера не доступна")
            return
        
        tasks = [
            ("Периметр", 4, "perimeter.npy", True),
            ("Правая стенка", 2, "right_wall.npy", False),
            ("Левая стенка", 2, "left_wall.npy", False),
            ("Балка робота", 2, "robot_beam.npy", False)
        ]
        
        print("\n" + "="*50)
        print(" НАЧАЛО РАЗМЕТКИ С КАМЕРЫ")
        print("="*50)
        
        for label, count, file, calc_h in tasks:
            if not self.mark_zone(label, count, file, calc_h):
                print(f"\n❌ Разметка прервана на этапе: {label}")
                break
        
        print("\n" + "="*50)
        print(" РАЗМЕТКА ЗАВЕРШЕНА")
        print("="*50)
        print("Нажмите любую клавишу для выхода...")
        
        # Показываем финальный кадр со всей разметкой
        final_display = self.frame.copy()
        cv2.putText(final_display, "Press any key to exit", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Marking Tool", final_display)
        cv2.waitKey(0)
        
        # Освобождаем ресурсы
        self.cap.release()
        cv2.destroyAllWindows()

class HomographyTransformer:
    """Класс для работы с сохраненными гомографическими матрицами"""
    
    def __init__(self, homography_path="perimeter.npy"):
        self.H = self._load_homography(homography_path)
    
    def _load_homography(self, path):
        """Загрузка гомографической матрицы"""
        if os.path.exists(path):
            H = np.load(path)
            if H.shape == (3, 3):
                return H
            else:
                print(f"Файл {path} не содержит матрицу гомографии (формат {H.shape})")
        return None
    
    def transform_point(self, point):
        """Преобразование одной точки"""
        if self.H is None:
            return point
        
        src = np.array([point], dtype=np.float32).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(src, self.H)
        return dst[0][0]
    
    def transform_points(self, points):
        """Преобразование массива точек"""
        if self.H is None:
            return points
        
        src = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(src, self.H)
        return dst.reshape(-1, 2)

if __name__ == "__main__":
    print("\n=== РАЗМЕТКА ЧЕРЕЗ ВЕБ-КАМЕРУ ===\n")
    
    # Пробуем открыть камеру
    camera_id = 0
    print(f"Пытаюсь открыть камеру {camera_id}...")
    
    # Запускаем разметку
    marker = PolygonMarker(camera_id)
    marker.run()
    
    # Демонстрация использования гомографии
    if os.path.exists("perimeter.npy"):
        print("\n=== Демонстрация применения гомографии ===")
        transformer = HomographyTransformer("perimeter.npy")
        
        if transformer.H is not None:
            print("\n✓ Гомографическая матрица загружена:")
            print(transformer.H)