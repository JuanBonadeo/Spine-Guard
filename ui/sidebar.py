import customtkinter as ctk


class Sidebar(ctk.CTkFrame):

    NAV_ITEMS = [
        ("monitor", "Monitor"),
        ("dashboard", "Dashboard"),
        ("settings", "Ajustes"),
        ("history", "Historial"),
    ]

    def __init__(self, master, on_navigate, on_pause, on_calibrate, on_theme_toggle):
        super().__init__(master, width=220, corner_radius=0)
        self.grid_propagate(False)
        self.configure(width=220)

        self._on_navigate = on_navigate
        self._on_pause = on_pause
        self._on_calibrate = on_calibrate
        self._active = "monitor"
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self.grid_rowconfigure(10, weight=1)

        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(24, 4), sticky="ew")
        ctk.CTkLabel(
            logo_frame, text="Spine Guard",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo_frame, text="v3.0",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40"),
        ).pack(anchor="w")

        sep1 = ctk.CTkFrame(self, height=1, fg_color=("gray75", "gray25"))
        sep1.grid(row=1, column=0, padx=16, pady=(12, 8), sticky="ew")

        for i, (key, label) in enumerate(self.NAV_ITEMS):
            btn = ctk.CTkButton(
                self,
                text=f"  {label}",
                anchor="w",
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(size=14),
                fg_color="transparent",
                text_color=("gray20", "gray80"),
                hover_color=("gray80", "gray30"),
                command=lambda k=key: self._on_nav_click(k),
            )
            btn.grid(row=2 + i, column=0, padx=12, pady=2, sticky="ew")
            self._nav_buttons[key] = btn

        sep2 = ctk.CTkFrame(self, height=1, fg_color=("gray75", "gray25"))
        sep2.grid(row=7, column=0, padx=16, pady=8, sticky="ew")

        self.pause_btn = ctk.CTkButton(
            self,
            text="  Pausar",
            anchor="w",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color=("gray20", "gray80"),
            hover_color=("gray80", "gray30"),
            command=self._on_pause_click,
        )
        self.pause_btn.grid(row=8, column=0, padx=12, pady=2, sticky="ew")

        self.calibrate_btn = ctk.CTkButton(
            self,
            text="  Calibrar",
            anchor="w",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color=("gray20", "gray80"),
            hover_color=("gray80", "gray30"),
            command=self._on_calibrate,
        )
        self.calibrate_btn.grid(row=9, column=0, padx=12, pady=2, sticky="ew")

        sep3 = ctk.CTkFrame(self, height=1, fg_color=("gray75", "gray25"))
        sep3.grid(row=11, column=0, padx=16, pady=8, sticky="ew")

        theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        theme_frame.grid(row=12, column=0, padx=20, pady=(4, 20), sticky="ew")
        ctk.CTkLabel(
            theme_frame, text="Tema",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        ).pack(side="left")
        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="",
            width=42,
            command=on_theme_toggle,
            onvalue=1,
            offvalue=0,
        )
        self.theme_switch.pack(side="right")
        self.theme_switch.select()

        self.set_active("monitor")

    def _on_nav_click(self, key: str):
        self.set_active(key)
        self._on_navigate(key)

    def _on_pause_click(self):
        self._on_pause()

    def set_active(self, key: str):
        self._active = key
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=("gray75", "#1A3A5C"),
                    text_color=("gray10", "#4DA3FF"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray20", "gray80"),
                )

    def set_paused(self, paused: bool):
        self.pause_btn.configure(text="  Reanudar" if paused else "  Pausar")
