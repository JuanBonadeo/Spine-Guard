import customtkinter as ctk

from ui.components.video_panel import VideoPanel
from ui.components.health_ring import HealthRing
from ui.components.metric_badge import MetricBadge


METRIC_NAMES = [
    ("Cabeza adelante", "forward_lean_ratio"),
    ("Cabeza baja", "slouch_drop_ratio"),
    ("Hombros adelante", "shoulder_width_norm"),
    ("Hombros tensos", "shoulder_raise_ratio"),
    ("Cabeza inclinada", "head_tilt_angle"),
    ("Descentrado", "lateral_offset"),
]

PROBLEM_MAP = {
    "Cabeza muy adelante": "forward_lean_ratio",
    "Encorvado (cabeza baja)": "slouch_drop_ratio",
    "Encorvado (hombros adelante)": "shoulder_width_norm",
    "Hombros tensos": "shoulder_raise_ratio",
    "Cabeza inclinada": "head_tilt_angle",
    "Inclinado a un lado": "lateral_offset",
}


class MonitorView(ctk.CTkFrame):

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self._app = app

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.video_panel = VideoPanel(self)
        self.video_panel.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)

        right_panel = ctk.CTkFrame(self, fg_color="transparent", width=240)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        right_panel.grid_propagate(False)
        right_panel.configure(width=240)

        self.health_ring = HealthRing(right_panel, size=150, thickness=10)
        self.health_ring.pack(pady=(8, 4))

        self.status_label = ctk.CTkLabel(
            right_panel,
            text="Postura correcta",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#30D158",
        )
        self.status_label.pack(pady=(0, 12))

        sep = ctk.CTkFrame(right_panel, height=1, fg_color=("gray75", "gray25"))
        sep.pack(fill="x", padx=8, pady=(0, 8))

        metrics_label = ctk.CTkLabel(
            right_panel, text="Metricas",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray40", "gray60"),
        )
        metrics_label.pack(anchor="w", padx=8, pady=(0, 4))

        self.badges: dict[str, MetricBadge] = {}
        for display_name, key in METRIC_NAMES:
            badge = MetricBadge(right_panel, name=display_name)
            badge.pack(fill="x", padx=4, pady=2)
            self.badges[key] = badge

        sep2 = ctk.CTkFrame(right_panel, height=1, fg_color=("gray75", "gray25"))
        sep2.pack(fill="x", padx=8, pady=8)

        self._session_label = ctk.CTkLabel(
            right_panel, text="Sesion: 0 min",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        self._session_label.pack(anchor="w", padx=12)

        self._good_pct_label = ctk.CTkLabel(
            right_panel, text="Buenos: 0%",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        self._good_pct_label.pack(anchor="w", padx=12)

        self._confidence_label = ctk.CTkLabel(
            right_panel, text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40"),
        )
        self._confidence_label.pack(anchor="w", padx=12, pady=(4, 0))

    def update_frame(self, frame, result):
        panel_w, panel_h = self.video_panel.get_display_size()
        h, w = frame.shape[:2]
        aspect = w / h
        display_h = panel_h
        display_w = int(display_h * aspect)
        if display_w > panel_w:
            display_w = panel_w
            display_h = int(display_w / aspect)

        self.video_panel.update_frame(frame, size=(display_w, display_h))

    def update_health(self, health: float):
        self.health_ring.update(health)

    def update_status(self, is_good: bool, message: str, reliable: bool):
        if not reliable:
            self.status_label.configure(
                text="Senal debil",
                text_color=("gray50", "gray50"),
            )
            return
        if is_good:
            self.status_label.configure(
                text="Postura correcta",
                text_color="#30D158",
            )
        else:
            self.status_label.configure(
                text=message,
                text_color="#FF453A",
            )

    def update_metrics(self, smoothed, problems: list[str]):
        problem_keys = set()
        for p in problems:
            if p in PROBLEM_MAP:
                problem_keys.add(PROBLEM_MAP[p])

        for key, badge in self.badges.items():
            val = getattr(smoothed, key, 0.0)
            is_ok = key not in problem_keys
            badge.update(val, is_ok)

    def update_session_info(self, total_min: float, good_pct: float):
        self._session_label.configure(text=f"Sesion: {total_min:.0f} min")
        self._good_pct_label.configure(text=f"Buenos: {good_pct:.0f}%")

    def update_confidence(self, confidence: float, reliable: bool):
        if reliable:
            self._confidence_label.configure(text="")
        else:
            self._confidence_label.configure(
                text=f"Confianza: {int(confidence * 100)}%"
            )

    def show_paused_overlay(self, paused: bool):
        if paused:
            self.status_label.configure(text="PAUSADO", text_color="#FFD60A")
        # When unpaused, status updates naturally from update_status()
