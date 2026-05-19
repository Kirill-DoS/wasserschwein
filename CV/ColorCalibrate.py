import cv2
import numpy as np
from Config import Config

class ColorCalibrator:
    def __init__(self, CamID, config=None):
        self.cap = cv2.VideoCapture(CamID)
        if not self.cap.isOpened():
            raise RuntimeError(f"❌ Не удалось открыть камеру {CamID}")

        self.config = config if config else Config()
        lower, upper = self.config.get_color_bounds()

        cv2.namedWindow("Settings")
        cv2.createTrackbar("H_min", "Settings", int(lower[0]), 180, lambda x: None)
        cv2.createTrackbar("S_min", "Settings", int(lower[1]), 255, lambda x: None)
        cv2.createTrackbar("V_min", "Settings", int(lower[2]), 255, lambda x: None)
        cv2.createTrackbar("H_max", "Settings", int(upper[0]), 180, lambda x: None)
        cv2.createTrackbar("S_max", "Settings", int(upper[1]), 255, lambda x: None)
        cv2.createTrackbar("V_max", "Settings", int(upper[2]), 255, lambda x: None)

        print("💡 Нажмите 'S' для сохранения настроек, ENTER для продолжения")

    def calibrate(self):
        print("🎨 Настрой цвет и нажми ENTER для сохранения...")
        lower = np.array([0, 100, 100])
        upper = np.array([15, 255, 255])

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("⚠️ Камера перестала отдавать кадры.")
                break

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            l_h = cv2.getTrackbarPos("H_min", "Settings")
            l_s = cv2.getTrackbarPos("S_min", "Settings")
            l_v = cv2.getTrackbarPos("V_min", "Settings")
            u_h = cv2.getTrackbarPos("H_max", "Settings")
            u_s = cv2.getTrackbarPos("S_max", "Settings")
            u_v = cv2.getTrackbarPos("V_max", "Settings")

            lower = np.array([l_h, l_s, l_v])
            upper = np.array([u_h, u_s, u_v])

            mask = cv2.inRange(hsv, lower, upper)
            result = cv2.bitwise_and(frame, frame, mask=mask)

            cv2.imshow("Calibration: Original", frame)
            cv2.imshow("Calibration: Mask", mask)
            cv2.imshow("Calibration: Result", result)

            key = cv2.waitKey(1) & 0xFF
            if key == 13:  # ENTER
                break
            elif key == ord('s'):  # S - сохранить настройки
                self.config.set_color_bounds(lower, upper)
                self.config.save()

        cv2.destroyAllWindows()
        self.cap.release()
        del self.cap
        return lower, upper
