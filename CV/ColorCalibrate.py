import cv2
import numpy as np

class ColorCalibrator:
    def __init__(self, CamID):
        self.cap = cv2.VideoCapture(CamID)
        if not self.cap.isOpened():
            raise RuntimeError(f"❌ Не удалось открыть камеру {CamID}")
        
        cv2.namedWindow("Settings")
        cv2.createTrackbar("H_min", "Settings", 0, 180, lambda x: None)
        cv2.createTrackbar("S_min", "Settings", 100, 255, lambda x: None)
        cv2.createTrackbar("V_min", "Settings", 100, 255, lambda x: None)
        cv2.createTrackbar("H_max", "Settings", 15, 180, lambda x: None)
        cv2.createTrackbar("S_max", "Settings", 255, 255, lambda x: None)
        cv2.createTrackbar("V_max", "Settings", 255, 255, lambda x: None)

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

            if cv2.waitKey(1) & 0xFF == 13:  # ENTER
                break
        
        cv2.destroyAllWindows()
        
        # 🔑 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ:
        self.cap.release()  # Освобождаем драйвер камеры
        del self.cap        # Удаляем объект из памяти
        return lower, upper