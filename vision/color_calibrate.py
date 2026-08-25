import cv2
import numpy as np

try:
    from .config import Config
except ImportError:
    from config import Config


class ColorCalibrator:
    # Открывает камеру и создаёт ползунки для выбора HSV-диапазона мяча.
    def __init__(self, camera_id, config, frame_size):
        self.cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L)
        if not self.cap.isOpened():
            raise RuntimeError(f"❌ Не удалось открыть камеру {camera_id}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_size[1])
        self.config = config if config is not None else Config()
        self.lower, self.upper = self.config.get_ball_color_bounds()
        self.trackbars_created = False
        #cv2.namedWindow("Настройка цвета", cv2.WINDOW_AUTOSIZE)

    # def create_sliders_if_needed(self):
    #     if not self.trackbars_created:
    #         import numpy as np
    #
    #         # Создаем пустую черную картинку-заглушку (mat)
    #         dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    #
    #         # Передаем и имя, и картинку. Крутим 5 раз, чтобы Qt-поток успел проснуться
    #         for _ in range(5):
    #             cv2.imshow("Настройка цвета", dummy_frame)
    #             cv2.waitKey(20) # Ждем 20 мс, давая GUI обработать создание окна
    #
    #         # Теперь окно гарантированно инициализировано бэкендом Qt
    #         cv2.createTrackbar("H_min", "Настройка цвета", int(self.lower[0]), 180, lambda _value: None)
    #         cv2.createTrackbar("S_min", "Настройка цвета", int(self.lower[1]), 255, lambda _value: None)
    #         cv2.createTrackbar("V_min", "Настройка цвета", int(self.lower[2]), 255, lambda _value: None)
    #         cv2.createTrackbar("H_max", "Настройка цвета", int(self.upper[0]), 180, lambda _value: None)
    #         cv2.createTrackbar("S_max", "Настройка цвета", int(self.upper[1]), 255, lambda _value: None)
    #         cv2.createTrackbar("V_max", "Настройка цвета", int(self.upper[2]), 255, lambda _value: None)
    #         self.trackbars_created = True

    # Читает ползунки и возвращает выбранные нижнюю и верхнюю HSV-границы.
    # def _read_bounds(self):
    #     lower = np.array(
    #         [
    #             cv2.getTrackbarPos("H_min", "Настройка цвета"),
    #             cv2.getTrackbarPos("S_min", "Настройка цвета"),
    #             cv2.getTrackbarPos("V_min", "Настройка цвета"),
    #         ],
    #         dtype=np.uint8,
    #     )
    #     upper = np.array(
    #         [
    #             cv2.getTrackbarPos("H_max", "Настройка цвета"),
    #             cv2.getTrackbarPos("S_max", "Настройка цвета"),
    #             cv2.getTrackbarPos("V_max", "Настройка цвета"),
    #         ],
    #         dtype=np.uint8,
    #     )
    #     return lower, upper

    # Показывает маску цвета до нажатия Enter и сохраняет выбор в общую конфигурацию.
    def calibrate(self):
        print("🎨 Настрой цвет мяча и нажми Enter для продолжения; S — сохранить")
        lower, upper = self.config.get_ball_color_bounds()

        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("⚠️ Камера перестала отдавать кадры во время калибровки")

                lower, upper = self._read_bounds()
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, lower, upper)
                result = cv2.bitwise_and(frame, frame, mask=mask)

                cv2.imshow("Калибровка: камера", frame)
                cv2.imshow("Калибровка: маска", mask)
                cv2.imshow("Калибровка: результат", result)

                key = cv2.waitKey(1) & 0xFF
                if key == 13:
                    self.config.set_ball_color_bounds(lower, upper)
                    return lower, upper
                if key in (27, ord("q")):
                    raise RuntimeError("Калибровка цвета отменена оператором")
                if key in (ord("s"), ord("ы")):
                    self.config.set_ball_color_bounds(lower, upper)
        finally:
            self.cap.release()
            cv2.destroyAllWindows()
