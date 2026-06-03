import customtkinter as ctk

from config.settings import Settings


SLIDER_SECTIONS = [
    {
        "title": "Sensibilidad de deteccion",
        "items": [
            ("forward_lean_threshold", "Cabeza adelante", 0.05, 0.30, 2),
            ("slouch_drop_threshold", "Caida de cabeza", 0.05, 0.25, 2),
            ("slouch_shoulder_threshold", "Hombros adelante", 0.03, 0.15, 2),
            ("shoulder_raise_threshold", "Hombros tensos", 0.05, 0.20, 2),
            ("head_tilt_threshold", "Inclinacion cabeza", 3.0, 15.0, 1),
            ("lateral_lean_threshold", "Inclinacion lateral", 0.05, 0.25, 2),
        ],
    },
    {
        "title": "Alertas",
        "items": [
            ("check_interval_sec", "Intervalo entre alertas (seg)", 30, 600, 0),
            ("bad_posture_frames", "Frames consecutivos", 3, 30, 0),
        ],
    },
    {
        "title": "Salud postural",
        "items": [
            ("health_decay_rate", "Velocidad de deterioro", 0.005, 0.05, 3),
            ("health_recovery_rate", "Velocidad de recuperacion", 0.005, 0.03, 3),
        ],
    },
    {
        "title": "Descansos",
        "items": [
            ("break_interval_min", "Intervalo de break (min)", 10, 90, 0),
        ],
    },
]


class SettingsView(ctk.CTkScrollableFrame):

    def __init__(self, master, settings: Settings, on_change):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self._settings = settings
        self._on_change = on_change
        self._sliders: dict[str, ctk.CTkSlider] = {}
        self._value_labels: dict[str, ctk.CTkLabel] = {}

        header = ctk.CTkLabel(
            self, text="Ajustes",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        header.pack(anchor="w", padx=20, pady=(16, 16))

        for section in SLIDER_SECTIONS:
            self._add_section(section)

        self._add_switches_section()
        self._add_theme_section()
        self._add_reset_button()

    def _add_section(self, section: dict):
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            title_frame, text=section["title"],
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")

        sep = ctk.CTkFrame(self, height=1, fg_color=("gray75", "gray25"))
        sep.pack(fill="x", padx=20, pady=(0, 8))

        for key, label, min_val, max_val, decimals in section["items"]:
            self._add_slider_row(key, label, min_val, max_val, decimals)

    def _add_slider_row(self, key: str, label: str, min_val: float,
                         max_val: float, decimals: int):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=4)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row, text=label, font=ctk.CTkFont(size=13),
            width=200, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        current = self._settings.get(key)
        if current is None:
            current = min_val

        fmt = f"{{:.{decimals}f}}" if decimals > 0 else "{:.0f}"
        val_label = ctk.CTkLabel(
            row, text=fmt.format(current),
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#007AFF", width=60, anchor="e",
        )
        val_label.grid(row=0, column=2, padx=(8, 0))
        self._value_labels[key] = val_label

        slider = ctk.CTkSlider(
            row, from_=min_val, to=max_val,
            number_of_steps=int((max_val - min_val) / (10 ** -decimals)) if decimals > 0 else int(max_val - min_val),
            command=lambda v, k=key, d=decimals: self._on_slider(k, v, d),
        )
        slider.set(current)
        slider.grid(row=0, column=1, sticky="ew", padx=8)
        self._sliders[key] = slider

    def _on_slider(self, key: str, value: float, decimals: int):
        if decimals == 0:
            value = int(round(value))
        else:
            value = round(value, decimals)

        fmt = f"{{:.{decimals}f}}" if decimals > 0 else "{:.0f}"
        self._value_labels[key].configure(text=fmt.format(value))
        self._settings.set(key, value)
        self._on_change(key, value)

    def _add_switches_section(self):
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            title_frame, text="Notificaciones",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")

        sep = ctk.CTkFrame(self, height=1, fg_color=("gray75", "gray25"))
        sep.pack(fill="x", padx=20, pady=(0, 8))

        switches = [
            ("sound_enabled", "Sonido habilitado"),
            ("notifications_enabled", "Notificaciones del sistema"),
            ("break_reminder_enabled", "Recordatorio de break"),
        ]

        for key, label in switches:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=4)

            ctk.CTkLabel(
                row, text=label, font=ctk.CTkFont(size=13),
            ).pack(side="left")

            switch = ctk.CTkSwitch(
                row, text="", width=42,
                command=lambda k=key: self._on_switch(k),
                onvalue=1, offvalue=0,
            )
            switch.pack(side="right")
            if self._settings.get(key):
                switch.select()

    def _on_switch(self, key: str):
        current = self._settings.get(key)
        self._settings.set(key, not current)
        self._on_change(key, not current)

    def _add_theme_section(self):
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            title_frame, text="Apariencia",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")

        sep = ctk.CTkFrame(self, height=1, fg_color=("gray75", "gray25"))
        sep.pack(fill="x", padx=20, pady=(0, 8))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=4)

        ctk.CTkLabel(row, text="Tema", font=ctk.CTkFont(size=13)).pack(side="left")

        current_theme = self._settings.get("theme") or "dark"
        self._theme_seg = ctk.CTkSegmentedButton(
            row,
            values=["Oscuro", "Claro"],
            command=self._on_theme_change,
        )
        self._theme_seg.set("Oscuro" if current_theme == "dark" else "Claro")
        self._theme_seg.pack(side="right")

    def _on_theme_change(self, value: str):
        theme = "dark" if value == "Oscuro" else "light"
        self._settings.set("theme", theme)
        self._on_change("theme", theme)

    def _add_reset_button(self):
        spacer = ctk.CTkFrame(self, fg_color="transparent", height=16)
        spacer.pack()

        btn = ctk.CTkButton(
            self, text="Restaurar valores por defecto",
            fg_color="transparent",
            border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray30", "gray70"),
            hover_color=("gray80", "gray30"),
            corner_radius=8,
            height=36,
            command=self._reset_defaults,
        )
        btn.pack(padx=20, pady=(8, 24))

    def _reset_defaults(self):
        self._settings.reset()
        for key, slider in self._sliders.items():
            val = self._settings.get(key)
            if val is not None:
                slider.set(val)
        self._on_change("__reset__", None)
