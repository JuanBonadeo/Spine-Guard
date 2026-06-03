import customtkinter as ctk


class StatCard(ctk.CTkFrame):

    def __init__(self, master, title: str, value: str = "--",
                 accent: str = None, **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)

        self._accent = accent

        self._title_label = ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        self._title_label.pack(anchor="w", padx=16, pady=(14, 2))

        self._value_label = ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=accent if accent else ("gray10", "gray90"),
        )
        self._value_label.pack(anchor="w", padx=16, pady=(0, 14))

    def update_value(self, value: str):
        self._value_label.configure(text=value)

    def set_accent(self, color: str):
        self._accent = color
        self._value_label.configure(text_color=color)
