import cv2


class Camera:
    def __init__(self, device_index: int = 0):
        self._cap = cv2.VideoCapture(device_index)

    def read_frame(self):
        return self._cap.read()

    def is_opened(self) -> bool:
        return self._cap.isOpened()

    def release(self):
        self._cap.release()
