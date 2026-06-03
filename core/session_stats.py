import csv
import os
import time
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SessionSummary:
    total_time_sec: float
    good_time_sec: float
    bad_time_sec: float
    good_percentage: float
    total_alerts: int
    breaks_taken: int


class SessionStats:

    def __init__(self):
        self._start_ts = time.time()
        self._good_frames = 0
        self._bad_frames = 0
        self._last_update = self._start_ts
        self._good_time = 0.0
        self._bad_time = 0.0
        self.total_alerts = 0
        self.breaks_taken = 0

    def update(self, is_good: bool):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now
        if is_good:
            self._good_time += dt
            self._good_frames += 1
        else:
            self._bad_time += dt
            self._bad_frames += 1

    def register_alert(self):
        self.total_alerts += 1

    def register_break(self):
        self.breaks_taken += 1

    def get_summary(self) -> SessionSummary:
        total = self._good_time + self._bad_time
        pct = (self._good_time / total * 100) if total > 0 else 0.0
        return SessionSummary(
            total_time_sec=total,
            good_time_sec=self._good_time,
            bad_time_sec=self._bad_time,
            good_percentage=pct,
            total_alerts=self.total_alerts,
            breaks_taken=self.breaks_taken,
        )

    def export_csv(self, path: str):
        summary = self.get_summary()
        start_dt = datetime.fromtimestamp(self._start_ts)
        file_exists = os.path.isfile(path)

        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "fecha", "inicio", "duracion_min",
                    "postura_buena_pct", "alertas", "breaks",
                ])
            writer.writerow([
                start_dt.strftime("%Y-%m-%d"),
                start_dt.strftime("%H:%M:%S"),
                f"{summary.total_time_sec / 60:.1f}",
                f"{summary.good_percentage:.1f}",
                summary.total_alerts,
                summary.breaks_taken,
            ])

    def reset(self):
        self.__init__()
