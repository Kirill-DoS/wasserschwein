import cv2
for i in range(4):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Индекс {i}: {w}x{h}")
        cap.release()
    else:
        print(f"Индекс {i}: Не доступен")