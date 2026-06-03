import tkinter as tk
import customtkinter as ctk


class HealthRing(ctk.CTkFrame):

    def __init__(self, master, size: int = 140, thickness: int = 10, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._size = size
        self._thickness = thickness
        self._health = 1.0
        self._display_health = 1.0

        self.canvas = tk.Canvas(
            self, width=size, height=size,
            bg=self._get_bg(), highlightthickness=0, bd=0,
        )
        self.canvas.pack()

        self._pct_label = ctk.CTkLabel(
            self, text="100%",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self._pct_label.place(relx=0.5, rely=0.42, anchor="center")

        self._status_label = ctk.CTkLabel(
            self, text="Excelente",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        self._status_label.place(relx=0.5, rely=0.62, anchor="center")

        self._render_ring()

    def _get_bg(self) -> str:
        mode = ctk.get_appearance_mode()
        return "#2A2A2A" if mode == "Dark" else "#FFFFFF"

    def _get_track_color(self) -> str:
        mode = ctk.get_appearance_mode()
        return "#3A3A3A" if mode == "Dark" else "#E5E5EA"

    def _get_arc_color(self) -> str:
        if self._display_health > 0.6:
            return "#30D158"
        if self._display_health > 0.3:
            return "#FFD60A"
        return "#FF453A"

    def _get_status_text(self) -> str:
        if self._display_health > 0.8:
            return "Excelente"
        if self._display_health > 0.6:
            return "Buena"
        if self._display_health > 0.3:
            return "Regular"
        return "Mala"

    def update(self, health: float):
        self._health = max(0.0, min(1.0, health))
        self._animate()

    def _animate(self):
        diff = self._health - self._display_health
        if abs(diff) < 0.005:
            self._display_health = self._health
            self._render_ring()
            return

        self._display_health += diff * 0.15
        self._render_ring()
        self.after(16, self._animate)

    def _render_ring(self):
        self.canvas.configure(bg=self._get_bg())
        self.canvas.delete("all")

        s = self._size
        t = self._thickness
        pad = t + 4

        self.canvas.create_arc(
            pad, pad, s - pad, s - pad,
            start=90, extent=-360,
            width=t, style="arc",
            outline=self._get_track_color(),
        )

        extent = -360 * self._display_health
        if abs(extent) > 0.5:
            self.canvas.create_arc(
                pad, pad, s - pad, s - pad,
                start=90, extent=extent,
                width=t, style="arc",
                outline=self._get_arc_color(),
            )

        pct = int(self._display_health * 100)
        self._pct_label.configure(text=f"{pct}%", text_color=self._get_arc_color())
        self._status_label.configure(text=self._get_status_text())

    def refresh_theme(self):
        self._render_ring()
