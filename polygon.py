import cv2
import numpy as np
import os

class PolygonMarker:
    def __init__(self, image_path):
        self.image_path = image_path
        self.points = []
        self.base_img = self._load_image()
        self.temp_img = None
        
        cv2.namedWindow("Marking Tool")
        cv2.setMouseCallback("Marking Tool", self._mouse_callback)

    def _load_image(self):
        if not os.path.exists(self.image_path):
            print(f"Файл {self.image_path} не найден, создан пустой холст.")
            return np.zeros((600, 800, 3), dtype=np.uint8)
        return cv2.imread(self.image_path)

    def _mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))
            # Рисуем точку клика
            cv2.circle(self.temp_img, (x, y), 5, (0, 255, 0), -1)
            # Рисуем линию, если это не первая точка
            if len(self.points) > 1:
                cv2.line(self.temp_img, self.points[-2], self.points[-1], (0, 255, 0), 1)
            cv2.imshow("Marking Tool", self.temp_img)

    def mark_zone(self, label, count, filename):
        print(f"--- Разметка: {label} ({count} точки) ---")
        self.points = []
        self.temp_img = self.base_img.copy()
        
        while len(self.points) < count:
            cv2.imshow("Marking Tool", self.temp_img)
            key = cv2.waitKey(1) & 0xFF
            if key == 27: # ESC для отмены
                return False
        
        # Сохранение
        data = np.array(self.points)
        np.save(filename, data)
        
        # Фиксация разметки на базовом изображении (синим цветом)
        self._draw_final_zone(data)
        return True

    def _draw_final_zone(self, data):
        if len(data) == 2:
            cv2.line(self.base_img, tuple(data[0]), tuple(data[1]), (255, 0, 0), 2)
        else:
            pts = data.reshape((-1, 1, 2))
            cv2.polylines(self.base_img, [pts], True, (255, 0, 0), 2)

    def run(self):
        tasks = [
            ("Периметр", 4, "perimeter.npy"),
            ("Правая стенка", 2, "right_wall.npy"),
            ("Левая стенка", 2, "left_wall.npy"),
            ("Балка робота", 2, "robot_beam.npy")
        ]
        
        for label, count, file in tasks:
            if not self.mark_zone(label, count, file):
                break
        
        print("Разметка завершена. Нажмите любую клавишу для выхода.")
        cv2.imshow("Marking Tool", self.base_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    marker = PolygonMarker("field.jpg")
    marker.run()
