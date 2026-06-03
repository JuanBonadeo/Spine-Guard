import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np
import cv2


class VideoPanel(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)

        self._image_label = ctk.CTkLabel(self, text="", corner_radius=12)
        self._image_label.pack(fill="both", expand=True, padx=2, pady=2)

        self._ctk_image = None
        self._overlay_text = None

        self._no_cam_label = ctk.CTkLabel(
            self,
            text="No se detecta camara\nVerifica la conexion",
            font=ctk.CTkFont(size=16),
            text_color="gray50",
        )

    def update_frame(self, frame: np.ndarray, size: tuple[int, int] = None):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        if size:
            pil_img = pil_img.resize(size, Image.LANCZOS)

        w, h = pil_img.size
        self._ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
        self._image_label.configure(image=self._ctk_image)
        self._no_cam_label.place_forget()

    def show_no_camera(self):
        self._image_label.configure(image=None)
        self._no_cam_label.place(relx=0.5, rely=0.5, anchor="center")

    def get_display_size(self) -> tuple[int, int]:
        w = self._image_label.winfo_width()
        h = self._image_label.winfo_height()
        if w <= 1 or h <= 1:
            return (640, 480)
        return (w, h)
