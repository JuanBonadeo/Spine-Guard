import threading

import pystray
from PIL import Image, ImageDraw


def _make_image(color: tuple) -> Image.Image:
    img = Image.new("RGB", (64, 64), (40, 40, 40))
    draw = ImageDraw.Draw(img)
    draw.ellipse([12, 12, 52, 52], fill=color)
    return img


class TrayIcon:
    """Ícono en la bandeja del sistema. Corre en un thread daemon aparte."""

    GREEN = (0, 200, 0)
    RED = (230, 0, 0)

    def __init__(self, on_show, on_pause, on_quit, on_stats):
        self._on_show = on_show
        self._on_pause = on_pause
        self._on_quit = on_quit
        self._on_stats = on_stats
        self._last_good = None

        menu = pystray.Menu(
            pystray.MenuItem("Mostrar ventana", lambda icon, item: self._on_show()),
            pystray.MenuItem("Pausar / Reanudar", lambda icon, item: self._on_pause()),
            pystray.MenuItem("Estadisticas", lambda icon, item: self._on_stats()),
            pystray.MenuItem("Salir", lambda icon, item: self._on_quit()),
        )
        self._icon = pystray.Icon(
            "SpineGuard", _make_image(self.GREEN), "Spine Guard", menu
        )
        self._thread: threading.Thread | None = None

    def start(self):
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def update_icon(self, is_good: bool):
        if is_good == self._last_good:
            return
        self._last_good = is_good
        self._icon.icon = _make_image(self.GREEN if is_good else self.RED)

    def notify(self, title: str, message: str):
        try:
            self._icon.notify(message, title)
        except Exception:
            pass

    def stop(self):
        self._icon.stop()
