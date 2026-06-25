import threading
import time

import cv2

from config.defaults import (
    AUTO_CALIBRATION_FRAMES, BAD_POSTURE_FRAMES, CHECK_INTERVAL_SEC,
    FORWARD_LEAN_THRESHOLD, FORWARD_Z_THRESHOLD, HEAD_TILT_THRESHOLD,
    HEALTH_DECAY_RATE, HEALTH_RECOVERY_RATE, HYSTERESIS_FACTOR,
    LATERAL_LEAN_THRESHOLD, ONE_EURO_BETA, ONE_EURO_D_CUTOFF,
    ONE_EURO_MIN_CUTOFF, REBASELINE_RATE, SEVERITY_THRESHOLDS,
    SHOULDER_RAISE_THRESHOLD, SLOUCH_DROP_THRESHOLD,
    SLOUCH_SHOULDER_THRESHOLD, VISIBILITY_THRESHOLD,
)
from config.settings import Settings
from core.analyzer import PostureAnalyzer
from core.health_bar import HealthBar
from core.session_stats import SessionStats

# Mismas 6 metricas que muestra el panel del escritorio (ui/views/monitor_view.py)
METRIC_KEYS = (
    "forward_lean_ratio",
    "slouch_drop_ratio",
    "shoulder_width_norm",
    "shoulder_raise_ratio",
    "head_tilt_angle",
    "lateral_offset",
)


class PostureEngine:
    """Nucleo de analisis para la version web, agnostico al transporte.

    `process_frame(frame)` puede alimentarse desde la camara local (modo local,
    via un hilo de captura) o desde frames enviados por el navegador (modo
    remoto, a futuro). Reutiliza los mismos modulos de `core/` que el desktop.
    """

    def __init__(self, settings: Settings | None = None):
        s = settings or Settings()
        self._settings = s

        self.analyzer = PostureAnalyzer(
            forward_threshold=s.get("forward_lean_threshold") or FORWARD_LEAN_THRESHOLD,
            forward_z_threshold=s.get("forward_z_threshold") or FORWARD_Z_THRESHOLD,
            slouch_drop_threshold=s.get("slouch_drop_threshold") or SLOUCH_DROP_THRESHOLD,
            slouch_shoulder_threshold=s.get("slouch_shoulder_threshold") or SLOUCH_SHOULDER_THRESHOLD,
            shoulder_raise_threshold=s.get("shoulder_raise_threshold") or SHOULDER_RAISE_THRESHOLD,
            tilt_threshold=s.get("head_tilt_threshold") or HEAD_TILT_THRESHOLD,
            lateral_threshold=s.get("lateral_lean_threshold") or LATERAL_LEAN_THRESHOLD,
            visibility_threshold=VISIBILITY_THRESHOLD,
            hysteresis_factor=HYSTERESIS_FACTOR,
            rebaseline_rate=REBASELINE_RATE,
            one_euro_min_cutoff=ONE_EURO_MIN_CUTOFF,
            one_euro_beta=ONE_EURO_BETA,
            one_euro_d_cutoff=ONE_EURO_D_CUTOFF,
            auto_calibration_frames=s.get("auto_calibration_frames") or AUTO_CALIBRATION_FRAMES,
        )
        self.stats = SessionStats()
        self.health = HealthBar(
            s.get("health_decay_rate") or HEALTH_DECAY_RATE,
            s.get("health_recovery_rate") or HEALTH_RECOVERY_RATE,
            SEVERITY_THRESHOLDS,
        )

        self._check_interval = s.get("check_interval_sec") or CHECK_INTERVAL_SEC
        self._bad_frames_threshold = s.get("bad_posture_frames") or BAD_POSTURE_FRAMES

        self._lock = threading.Lock()
        self._latest_jpeg: bytes | None = None
        self._bad_count = 0
        self._calibrating = True
        self._calib_progress = 0.0
        self._paused = False
        self._last_result = None
        self._last_alert_ts = 0.0
        self._alert_id = 0
        self._status: dict = {
            "calibrating": True,
            "calib_progress": 0.0,
            "paused": False,
            "is_good": True,
            "reliable": False,
            "message": "Iniciando...",
            "problems": [],
            "metrics": {},
            "confidence": 0.0,
            "health": 1.0,
            "severity": 0,
            "alert_id": 0,
            "session_min": 0.0,
            "good_pct": 0.0,
            "alerts": 0,
        }

    # -- entrada de frames (transporte-agnostica) --

    def process_frame(self, frame) -> None:
        if self._paused:
            # El video sigue vivo pero el analisis queda congelado (= pausa desktop).
            self._encode(frame)
            self._refresh_status(self._last_result)
            return

        if self._calibrating:
            progress = self.analyzer.auto_calibrate(frame)
            with self._lock:
                self._calib_progress = progress
                if progress >= 1.0:
                    self._calibrating = False
            self._encode(frame)
            self._refresh_status(None)
            return

        result = self.analyzer.analyze(frame)
        self._last_result = result

        if result.reliable:
            self.health.update(result.is_good)
            self.stats.update(result.is_good)
            if not result.is_good:
                self._bad_count += 1
            else:
                self._bad_count = 0

            if self._bad_count >= self._bad_frames_threshold:
                now = time.time()
                if now - self._last_alert_ts >= self._check_interval:
                    self.stats.register_alert()
                    self._last_alert_ts = now
                    self._alert_id += 1
                    self._bad_count = 0
        else:
            self._bad_count = 0

        display = self.analyzer.draw(frame, result)
        self._encode(display)
        self._refresh_status(result)

    def request_recalibration(self) -> None:
        with self._lock:
            self._calibrating = True
            self._calib_progress = 0.0
        self._bad_count = 0

    def toggle_pause(self) -> bool:
        self._paused = not self._paused
        return self._paused

    def _encode(self, frame_bgr) -> None:
        ok, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ok:
            with self._lock:
                self._latest_jpeg = buf.tobytes()

    def _refresh_status(self, result) -> None:
        metrics = {}
        if result is not None and result.reliable:
            sm = result.smoothed
            metrics = {k: round(getattr(sm, k), 2) for k in METRIC_KEYS}

        summary = self.stats.get_summary()
        with self._lock:
            self._status = {
                "calibrating": self._calibrating,
                "calib_progress": round(self._calib_progress, 3),
                "paused": self._paused,
                "is_good": result.is_good if result else True,
                "reliable": result.reliable if result else False,
                "message": result.message if result else "Calibrando...",
                "problems": list(result.problems) if result else [],
                "metrics": metrics,
                "confidence": round(result.confidence, 2) if result else 0.0,
                "health": round(self.health.get_health(), 3),
                "severity": self.health.get_severity(),
                "alert_id": self._alert_id,
                "session_min": round(summary.total_time_sec / 60, 1),
                "good_pct": round(summary.good_percentage, 1),
                "alerts": summary.total_alerts,
            }

    # -- salida (consumida por las rutas Flask) --

    def get_jpeg(self) -> bytes | None:
        with self._lock:
            return self._latest_jpeg

    def get_status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def close(self) -> None:
        self.analyzer.close()
