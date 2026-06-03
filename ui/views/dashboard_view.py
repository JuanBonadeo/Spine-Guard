import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ui.components.stat_card import StatCard


class DashboardView(ctk.CTkFrame):

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self._app = app
        self._health_history: list[float] = []
        self._problem_counts: dict[str, int] = {}

        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkLabel(
            self, text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        header.grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(16, 12))

        self.card_time = StatCard(self, "Tiempo de sesion", "0 min")
        self.card_time.grid(row=0, column=0, sticky="nsew", padx=(20, 6), pady=(56, 6))

        self.card_good = StatCard(self, "Postura buena", "0%", accent="#30D158")
        self.card_good.grid(row=0, column=1, sticky="nsew", padx=6, pady=(56, 6))

        self.card_alerts = StatCard(self, "Alertas", "0", accent="#FFD60A")
        self.card_alerts.grid(row=0, column=2, sticky="nsew", padx=6, pady=(56, 6))

        self.card_breaks = StatCard(self, "Breaks", "0", accent="#007AFF")
        self.card_breaks.grid(row=0, column=3, sticky="nsew", padx=(6, 20), pady=(56, 6))

        chart_frame = ctk.CTkFrame(self, corner_radius=12)
        chart_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=20, pady=6)

        ctk.CTkLabel(
            chart_frame, text="Salud postural durante la sesion",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 0))

        is_dark = ctk.get_appearance_mode() == "Dark"
        bg = "#2A2A2A" if is_dark else "#FFFFFF"
        text_c = "#A0A0A0" if is_dark else "#86868B"

        self._fig = Figure(figsize=(6, 2.2), dpi=100, facecolor=bg)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(bg)
        self._ax.tick_params(colors=text_c, labelsize=8)
        for spine in self._ax.spines.values():
            spine.set_color(text_c)
        self._ax.set_ylim(0, 100)
        self._ax.set_ylabel("Salud %", color=text_c, fontsize=9)

        self._canvas_widget = FigureCanvasTkAgg(self._fig, master=chart_frame)
        self._canvas_widget.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 8))

        problems_frame = ctk.CTkFrame(self, corner_radius=12)
        problems_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=20, pady=(6, 16))

        ctk.CTkLabel(
            problems_frame, text="Problemas detectados",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self._problems_container = ctk.CTkFrame(problems_frame, fg_color="transparent")
        self._problems_container.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    def update_stats(self, total_min: float, good_pct: float, alerts: int, breaks: int):
        self.card_time.update_value(f"{total_min:.0f} min")
        self.card_good.update_value(f"{good_pct:.0f}%")
        self.card_alerts.update_value(str(alerts))
        self.card_breaks.update_value(str(breaks))

    def add_health_sample(self, health: float):
        self._health_history.append(health * 100)
        if len(self._health_history) > 1800:
            self._health_history = self._health_history[-1800:]

    def record_problem(self, problem: str):
        self._problem_counts[problem] = self._problem_counts.get(problem, 0) + 1

    def refresh_chart(self):
        if not self._health_history:
            return

        is_dark = ctk.get_appearance_mode() == "Dark"
        bg = "#2A2A2A" if is_dark else "#FFFFFF"
        text_c = "#A0A0A0" if is_dark else "#86868B"

        self._fig.set_facecolor(bg)
        self._ax.clear()
        self._ax.set_facecolor(bg)
        self._ax.tick_params(colors=text_c, labelsize=8)
        for spine in self._ax.spines.values():
            spine.set_color(text_c)

        n = len(self._health_history)
        x_min = [i / 30 / 60 for i in range(n)]
        self._ax.fill_between(x_min, self._health_history, alpha=0.3, color="#007AFF")
        self._ax.plot(x_min, self._health_history, color="#007AFF", linewidth=1.5)
        self._ax.set_ylim(0, 100)
        self._ax.set_ylabel("Salud %", color=text_c, fontsize=9)
        self._ax.set_xlabel("Minutos", color=text_c, fontsize=9)

        self._canvas_widget.draw_idle()

    def refresh_problems(self):
        for widget in self._problems_container.winfo_children():
            widget.destroy()

        if not self._problem_counts:
            ctk.CTkLabel(
                self._problems_container,
                text="Sin problemas detectados",
                text_color=("gray50", "gray50"),
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", pady=4)
            return

        total = sum(self._problem_counts.values())
        sorted_problems = sorted(self._problem_counts.items(), key=lambda x: -x[1])

        for name, count in sorted_problems:
            pct = (count / total * 100) if total > 0 else 0
            row = ctk.CTkFrame(self._problems_container, fg_color="transparent", height=28)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            ctk.CTkLabel(
                row, text=name, font=ctk.CTkFont(size=12),
                text_color=("gray20", "gray80"), width=180, anchor="w",
            ).pack(side="left")

            bar_bg = ctk.CTkFrame(row, height=10, corner_radius=5,
                                   fg_color=("gray80", "gray30"))
            bar_bg.pack(side="left", fill="x", expand=True, padx=8, pady=9)

            bar_fill = ctk.CTkFrame(bar_bg, height=10, corner_radius=5,
                                     fg_color="#007AFF")
            bar_fill.place(relx=0, rely=0, relwidth=max(0.02, pct / 100), relheight=1)

            ctk.CTkLabel(
                row, text=f"{pct:.0f}%", font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray60"), width=40, anchor="e",
            ).pack(side="right")
