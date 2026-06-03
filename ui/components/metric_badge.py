import customtkinter as ctk


class MetricBadge(ctk.CTkFrame):

    def __init__(self, master, name: str, **kwargs):
        super().__init__(master, height=32, corner_radius=8, **kwargs)

        self._name = name
        self._is_ok = True

        self.grid_columnconfigure(1, weight=1)

        self._dot = ctk.CTkLabel(
            self, text="", width=10, height=10,
            corner_radius=5,
            fg_color="#30D158",
        )
        self._dot.grid(row=0, column=0, padx=(10, 6), pady=8)

        self._name_label = ctk.CTkLabel(
            self, text=name,
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self._name_label.grid(row=0, column=1, sticky="w")

        self._value_label = ctk.CTkLabel(
            self, text="--",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=("gray40", "gray60"),
            anchor="e",
        )
        self._value_label.grid(row=0, column=2, padx=(4, 10))

    def update(self, value: float, is_ok: bool):
        self._is_ok = is_ok
        color = "#30D158" if is_ok else "#FF453A"
        self._dot.configure(fg_color=color)
        self._value_label.configure(text=f"{value:.2f}")

    def set_ok(self):
        self._dot.configure(fg_color="#30D158")
        self._value_label.configure(text="OK")
        self._is_ok = True
