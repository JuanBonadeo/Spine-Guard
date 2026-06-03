import customtkinter as ctk


class CalibrationModal(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, **kwargs)

        self._overlay = ctk.CTkFrame(self, fg_color=("gray90", "#111111"), corner_radius=0)
        self._overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        card = ctk.CTkFrame(self._overlay, corner_radius=16, width=420, height=260)
        card.place(relx=0.5, rely=0.45, anchor="center")
        card.pack_propagate(False)

        ctk.CTkLabel(
            card, text="Calibrando postura",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(28, 8))

        ctk.CTkLabel(
            card, text="Senta derecho y mira la pantalla",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),
        ).pack(pady=(0, 20))

        self._progress = ctk.CTkProgressBar(card, width=300, height=8, corner_radius=4)
        self._progress.pack(pady=(0, 8))
        self._progress.set(0)

        self._pct_label = ctk.CTkLabel(
            card, text="0%",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#007AFF",
        )
        self._pct_label.pack(pady=(0, 8))

        self._hint_label = ctk.CTkLabel(
            card, text="Mantene la posicion...",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray50"),
        )
        self._hint_label.pack()

    def update_progress(self, progress: float):
        self._progress.set(progress)
        self._pct_label.configure(text=f"{int(progress * 100)}%")

    def show_success(self):
        self._hint_label.configure(
            text="Calibracion exitosa",
            text_color="#30D158",
        )
        self._pct_label.configure(text="100%", text_color="#30D158")
        self._progress.set(1.0)
