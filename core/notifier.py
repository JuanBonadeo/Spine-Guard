import time
import winsound

from plyer import notification

SEVERITY_MESSAGES = [
    "Corregi un poco la postura",
    "Tu postura empeoro bastante",
    "Postura muy mala, sentate derecho",
]


class PostureNotifier:

    def __init__(self, interval_sec: int, beep_levels: list, break_interval_sec: int):
        self._interval = interval_sec
        self._beep_levels = beep_levels
        self._break_interval = break_interval_sec
        self._last_notification = 0.0
        self._last_break = time.time()
        self._on_toast = None

    def set_toast_callback(self, callback):
        self._on_toast = callback

    def should_notify(self) -> bool:
        return (time.time() - self._last_notification) >= self._interval

    def notify(self, problems_msg: str, severity: int):
        severity = max(0, min(severity, len(self._beep_levels) - 1))
        freq, duration = self._beep_levels[severity]
        winsound.Beep(freq, duration)

        header = SEVERITY_MESSAGES[severity]
        body = f"{header}\n{problems_msg}" if problems_msg else header
        notification.notify(
            title="Postura Incorrecta",
            message=body,
            app_name="Spine Guard",
            timeout=10,
        )
        if self._on_toast:
            self._on_toast(header, severity)
        self._last_notification = time.time()

    def reset_timer(self):
        self._last_notification = time.time()

    def should_break_remind(self) -> bool:
        return (time.time() - self._last_break) >= self._break_interval

    def break_remind(self):
        winsound.Beep(600, 400)
        notification.notify(
            title="Hora de un descanso",
            message="Llevas un buen rato sentado. Levantate y estira un poco.",
            app_name="Spine Guard",
            timeout=10,
        )
        if self._on_toast:
            self._on_toast("Hora de un descanso", -1)
        self._last_break = time.time()

    def reset_break_timer(self):
        self._last_break = time.time()
