import time

import cv2
import customtkinter as ctk

from core.capture import Camera
from core.analyzer import PostureAnalyzer
from core.notifier import PostureNotifier
from core.session_stats import SessionStats
from core.health_bar import HealthBar
from config.defaults import (
    CAMERA_INDEX, CHECK_INTERVAL_SEC, BAD_POSTURE_FRAMES,
    AUTO_CALIBRATION_FRAMES, ONE_EURO_MIN_CUTOFF, ONE_EURO_BETA,
    ONE_EURO_D_CUTOFF, FORWARD_LEAN_THRESHOLD, FORWARD_Z_THRESHOLD,
    SLOUCH_DROP_THRESHOLD, SLOUCH_SHOULDER_THRESHOLD,
    SHOULDER_RAISE_THRESHOLD, HEAD_TILT_THRESHOLD, LATERAL_LEAN_THRESHOLD,
    VISIBILITY_THRESHOLD, HYSTERESIS_FACTOR, REBASELINE_RATE,
    HEALTH_DECAY_RATE, HEALTH_RECOVERY_RATE, SEVERITY_THRESHOLDS,
    BEEP_LEVELS, BREAK_INTERVAL_SEC, CSV_PATH,
)
from config.settings import Settings
from tray import TrayIcon
from ui.theme import Theme
from ui.sidebar import Sidebar
from ui.views.monitor_view import MonitorView
from ui.views.dashboard_view import DashboardView
from ui.views.settings_view import SettingsView
from ui.views.history_view import HistoryView
from ui.components.toast import ToastManager
from ui.components.calibration_modal import CalibrationModal


class SpineGuardApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Spine Guard")
        self.geometry("1200x750")
        self.minsize(950, 620)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.is_paused = False
        self.is_calibrating = True
        self.should_quit = False
        self.current_view = "monitor"

        self.settings = Settings()
        self.theme = Theme(self.settings.get("theme") or "dark")

        self._chart_counter = 0
        self._bad_count = 0

        self.camera = Camera(self.settings.get("camera_index") or CAMERA_INDEX)
        if not self.camera.is_opened():
            print("Error: no se pudo abrir la camara.")

        self.analyzer = PostureAnalyzer(
            forward_threshold=self.settings.get("forward_lean_threshold") or FORWARD_LEAN_THRESHOLD,
            forward_z_threshold=self.settings.get("forward_z_threshold") or FORWARD_Z_THRESHOLD,
            slouch_drop_threshold=self.settings.get("slouch_drop_threshold") or SLOUCH_DROP_THRESHOLD,
            slouch_shoulder_threshold=self.settings.get("slouch_shoulder_threshold") or SLOUCH_SHOULDER_THRESHOLD,
            shoulder_raise_threshold=self.settings.get("shoulder_raise_threshold") or SHOULDER_RAISE_THRESHOLD,
            tilt_threshold=self.settings.get("head_tilt_threshold") or HEAD_TILT_THRESHOLD,
            lateral_threshold=self.settings.get("lateral_lean_threshold") or LATERAL_LEAN_THRESHOLD,
            visibility_threshold=VISIBILITY_THRESHOLD,
            hysteresis_factor=HYSTERESIS_FACTOR,
            rebaseline_rate=REBASELINE_RATE,
            one_euro_min_cutoff=ONE_EURO_MIN_CUTOFF,
            one_euro_beta=ONE_EURO_BETA,
            one_euro_d_cutoff=ONE_EURO_D_CUTOFF,
            auto_calibration_frames=AUTO_CALIBRATION_FRAMES,
        )

        self.notifier = PostureNotifier(
            self.settings.get("check_interval_sec") or CHECK_INTERVAL_SEC,
            BEEP_LEVELS,
            (self.settings.get("break_interval_min") or 45) * 60,
        )

        self.stats = SessionStats()
        self.health = HealthBar(
            self.settings.get("health_decay_rate") or HEALTH_DECAY_RATE,
            self.settings.get("health_recovery_rate") or HEALTH_RECOVERY_RATE,
            SEVERITY_THRESHOLDS,
        )

        self._create_layout()

        self.toast = ToastManager(self)

        self.notifier.set_toast_callback(self._on_posture_toast)

        self.tray = TrayIcon(
            on_show=lambda: self._restore_window(),
            on_pause=lambda: self.toggle_pause(),
            on_quit=lambda: self._request_quit(),
            on_stats=lambda: self._show_stats_toast(),
        )
        self.tray.start()

        self._bind_shortcuts()

        self.after(200, self._start_calibration)

    def _create_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(
            self,
            on_navigate=self.show_view,
            on_pause=self.toggle_pause,
            on_calibrate=self.recalibrate,
            on_theme_toggle=self.toggle_theme,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.views: dict[str, ctk.CTkFrame] = {}

        self.monitor_view = MonitorView(self.content, self)
        self.monitor_view.grid(row=0, column=0, sticky="nsew")
        self.views["monitor"] = self.monitor_view

        self.dashboard_view = DashboardView(self.content, self)
        self.dashboard_view.grid(row=0, column=0, sticky="nsew")
        self.views["dashboard"] = self.dashboard_view

        self.settings_view = SettingsView(self.content, self.settings, self._on_setting_change)
        self.settings_view.grid(row=0, column=0, sticky="nsew")
        self.views["settings"] = self.settings_view

        self.history_view = HistoryView(self.content, self.settings.get("csv_path") or CSV_PATH)
        self.history_view.grid(row=0, column=0, sticky="nsew")
        self.views["history"] = self.history_view

        self.calib_modal = CalibrationModal(self.content)
        self.calib_modal.grid(row=0, column=0, sticky="nsew")

        self.show_view("monitor")

    def show_view(self, name: str):
        self.current_view = name
        if name == "history":
            self.history_view.refresh()
        if name == "dashboard":
            self.dashboard_view.refresh_chart()
            self.dashboard_view.refresh_problems()

        for vname, view in self.views.items():
            if vname == name:
                view.tkraise()
        self.sidebar.set_active(name)

    def _bind_shortcuts(self):
        self.bind("<Control-q>", lambda e: self._request_quit())
        self.bind("<Control-p>", lambda e: self.toggle_pause())
        self.bind("<Control-c>", lambda e: self.recalibrate())
        self.bind("<Control-b>", lambda e: self._manual_break())
        self.bind("<Control-t>", lambda e: self.toggle_theme())
        self.bind("<Control-Key-1>", lambda e: self.show_view("monitor"))
        self.bind("<Control-Key-2>", lambda e: self.show_view("dashboard"))
        self.bind("<Control-Key-3>", lambda e: self.show_view("settings"))
        self.bind("<Control-Key-4>", lambda e: self.show_view("history"))

    def _start_calibration(self):
        self.is_calibrating = True
        self.calib_modal.tkraise()
        self._calibration_loop()

    def _calibration_loop(self):
        if self.should_quit:
            return

        ok, frame = self.camera.read_frame()
        if not ok:
            self.after(33, self._calibration_loop)
            return

        frame = cv2.flip(frame, 1)
        progress = self.analyzer.auto_calibrate(frame)
        self.calib_modal.update_progress(progress)

        if progress >= 1.0:
            self.calib_modal.show_success()
            self.is_calibrating = False
            self.notifier.reset_timer()
            self.notifier.reset_break_timer()
            self.after(800, self._finish_calibration)
            return

        self.after(33, self._calibration_loop)

    def _finish_calibration(self):
        self.calib_modal.grid_forget()
        self.show_view("monitor")
        self._process_frame()

    def _process_frame(self):
        if self.should_quit:
            return

        ok, frame = self.camera.read_frame()
        if not ok:
            self.after(33, self._process_frame)
            return

        frame = cv2.flip(frame, 1)

        if self.is_paused:
            if self.current_view == "monitor":
                display = self.analyzer.draw(frame, self.analyzer.analyze(frame))
                self.monitor_view.update_frame(display, None)
                self.monitor_view.show_paused_overlay(True)
            self.after(33, self._process_frame)
            return

        result = self.analyzer.analyze(frame)

        if result.reliable:
            self.health.update(result.is_good)
            self.stats.update(result.is_good)
            self.tray.update_icon(result.is_good)

            if not result.is_good:
                self._bad_count += 1
                for p in result.problems:
                    self.dashboard_view.record_problem(p)
            else:
                self._bad_count = 0

            bad_frames_threshold = self.settings.get("bad_posture_frames") or BAD_POSTURE_FRAMES
            if self._bad_count >= bad_frames_threshold and self.notifier.should_notify():
                self.notifier.notify(result.message, self.health.get_severity())
                self.stats.register_alert()
                self._bad_count = 0
        else:
            self._bad_count = 0
            self.tray.update_icon(True)

        if self.notifier.should_break_remind():
            self.notifier.break_remind()
            self.stats.register_break()

        self._chart_counter += 1
        if self._chart_counter % 10 == 0:
            self.dashboard_view.add_health_sample(self.health.get_health())

        display = self.analyzer.draw(frame, result)

        if self.current_view == "monitor":
            self.monitor_view.update_frame(display, result)
            self.monitor_view.update_health(self.health.get_health())
            self.monitor_view.update_status(result.is_good, result.message, result.reliable)
            self.monitor_view.update_confidence(result.confidence, result.reliable)
            if result.reliable:
                self.monitor_view.update_metrics(result.smoothed, result.problems)

            summary = self.stats.get_summary()
            self.monitor_view.update_session_info(
                summary.total_time_sec / 60, summary.good_percentage
            )

        if self.current_view == "dashboard":
            summary = self.stats.get_summary()
            self.dashboard_view.update_stats(
                summary.total_time_sec / 60,
                summary.good_percentage,
                summary.total_alerts,
                summary.breaks_taken,
            )

        self.after(33, self._process_frame)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.sidebar.set_paused(self.is_paused)
        if not self.is_paused and self.current_view == "monitor":
            self.monitor_view.show_paused_overlay(False)

    def recalibrate(self):
        if self.is_calibrating:
            return
        ok, frame = self.camera.read_frame()
        if ok:
            frame = cv2.flip(frame, 1)
            if self.analyzer.calibrate(frame):
                self.toast.show("Postura recalibrada", "success")
                self._bad_count = 0

    def toggle_theme(self):
        self.theme.toggle()
        self.settings.set("theme", self.theme.current)

    def _manual_break(self):
        self.notifier.reset_break_timer()
        self.stats.register_break()
        self.toast.show("Break registrado", "info")

    def _on_posture_toast(self, message: str, severity: int):
        if severity == -1:
            self.toast.show(message, "info", 5000)
        elif severity >= 2:
            self.toast.show(message, "error", 4000)
        elif severity >= 1:
            self.toast.show(message, "warning", 3500)
        else:
            self.toast.show(message, "warning", 3000)

    def _on_setting_change(self, key: str, value):
        if key == "theme":
            mode = "dark" if value == "dark" else "light"
            ctk.set_appearance_mode(mode)
            self.theme = Theme(mode)

    def _restore_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _show_stats_toast(self):
        s = self.stats.get_summary()
        self.tray.notify(
            "Estadisticas de sesion",
            f"Tiempo: {s.total_time_sec / 60:.1f} min | "
            f"Buena postura: {s.good_percentage:.0f}% | "
            f"Alertas: {s.total_alerts}",
        )

    def _request_quit(self):
        self.should_quit = True
        self._on_close()

    def _on_close(self):
        self.should_quit = True
        try:
            csv_path = self.settings.get("csv_path") or CSV_PATH
            self.stats.export_csv(csv_path)
            s = self.stats.get_summary()
            print(f"\nSesion: {s.total_time_sec / 60:.1f} min | "
                  f"Buena postura: {s.good_percentage:.0f}% | "
                  f"Alertas: {s.total_alerts} | Breaks: {s.breaks_taken}")
        except Exception as e:
            print(f"Error exportando CSV: {e}")

        self.camera.release()
        self.analyzer.close()
        self.tray.stop()
        self.destroy()
