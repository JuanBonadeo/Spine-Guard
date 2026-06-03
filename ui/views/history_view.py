import csv
import os

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class HistoryView(ctk.CTkFrame):

    def __init__(self, master, csv_path: str):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self._csv_path = csv_path
        self._data: list[dict] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=2)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            header_frame, text="Historial",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_frame, text="Actualizar", width=100,
            corner_radius=8, height=32,
            command=self.refresh,
        )
        refresh_btn.pack(side="right")

        chart_frame = ctk.CTkFrame(self, corner_radius=12)
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=6)

        ctk.CTkLabel(
            chart_frame, text="Postura buena por sesion",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 0))

        is_dark = ctk.get_appearance_mode() == "Dark"
        bg = "#2A2A2A" if is_dark else "#FFFFFF"
        text_c = "#A0A0A0" if is_dark else "#86868B"

        self._fig = Figure(figsize=(6, 2), dpi=100, facecolor=bg)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(bg)

        self._canvas_widget = FigureCanvasTkAgg(self._fig, master=chart_frame)
        self._canvas_widget.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 8))

        table_frame = ctk.CTkFrame(self, corner_radius=12)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(6, 16))

        columns = ["Fecha", "Inicio", "Duracion", "Buena %", "Alertas", "Breaks"]
        col_header = ctk.CTkFrame(table_frame, fg_color="transparent", height=32)
        col_header.pack(fill="x", padx=4, pady=(8, 0))
        for i, col in enumerate(columns):
            ctk.CTkLabel(
                col_header, text=col,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("gray40", "gray60"),
                width=100, anchor="w",
            ).pack(side="left", padx=8)

        sep = ctk.CTkFrame(table_frame, height=1, fg_color=("gray75", "gray25"))
        sep.pack(fill="x", padx=8, pady=4)

        self._table_container = ctk.CTkScrollableFrame(
            table_frame, fg_color="transparent",
        )
        self._table_container.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        self.refresh()

    def _load_data(self) -> list[dict]:
        if not os.path.isfile(self._csv_path):
            return []
        rows = []
        with open(self._csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    def refresh(self):
        self._data = self._load_data()
        self._draw_chart()
        self._draw_table()

    def _draw_chart(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg = "#2A2A2A" if is_dark else "#FFFFFF"
        text_c = "#A0A0A0" if is_dark else "#86868B"

        self._fig.set_facecolor(bg)
        self._ax.clear()
        self._ax.set_facecolor(bg)
        self._ax.tick_params(colors=text_c, labelsize=8)
        for spine in self._ax.spines.values():
            spine.set_color(text_c)

        if not self._data:
            self._ax.text(0.5, 0.5, "Sin datos", ha="center", va="center",
                          color=text_c, fontsize=12, transform=self._ax.transAxes)
            self._canvas_widget.draw_idle()
            return

        last_14 = self._data[-14:]
        labels = [r.get("fecha", "?")[-5:] for r in last_14]
        values = []
        for r in last_14:
            try:
                values.append(float(r.get("postura_buena_pct", 0)))
            except ValueError:
                values.append(0)

        colors = []
        for v in values:
            if v >= 70:
                colors.append("#30D158")
            elif v >= 40:
                colors.append("#FFD60A")
            else:
                colors.append("#FF453A")

        self._ax.bar(range(len(values)), values, color=colors, width=0.6)
        self._ax.set_xticks(range(len(labels)))
        self._ax.set_xticklabels(labels, rotation=45, fontsize=7)
        self._ax.set_ylim(0, 100)
        self._ax.set_ylabel("% Buena", color=text_c, fontsize=9)

        self._fig.tight_layout()
        self._canvas_widget.draw_idle()

    def _draw_table(self):
        for widget in self._table_container.winfo_children():
            widget.destroy()

        if not self._data:
            ctk.CTkLabel(
                self._table_container,
                text="No hay sesiones registradas",
                text_color=("gray50", "gray50"),
            ).pack(pady=20)
            return

        for row_data in reversed(self._data):
            row = ctk.CTkFrame(self._table_container, fg_color="transparent", height=30)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            fields = [
                row_data.get("fecha", ""),
                row_data.get("inicio", ""),
                f"{row_data.get('duracion_min', '0')} min",
                f"{row_data.get('postura_buena_pct', '0')}%",
                row_data.get("alertas", "0"),
                row_data.get("breaks", "0"),
            ]
            for val in fields:
                ctk.CTkLabel(
                    row, text=val,
                    font=ctk.CTkFont(size=12),
                    width=100, anchor="w",
                ).pack(side="left", padx=8)
