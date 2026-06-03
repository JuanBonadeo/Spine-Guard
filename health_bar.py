import cv2


class HealthBar:
    """Salud postural acumulativa: baja con frames malos, sube con buenos."""

    def __init__(self, decay_rate: float, recovery_rate: float, severity_thresholds: tuple):
        self._decay = decay_rate
        self._recovery = recovery_rate
        self._mid, self._low = severity_thresholds
        self._health = 1.0

    def update(self, is_good: bool):
        if is_good:
            self._health = min(1.0, self._health + self._recovery)
        else:
            self._health = max(0.0, self._health - self._decay)

    def get_health(self) -> float:
        return self._health

    def get_severity(self) -> int:
        """0 = leve, 1 = medio, 2 = fuerte (peor salud => mayor severidad)."""
        if self._health > self._mid:
            return 0
        if self._health > self._low:
            return 1
        return 2

    def _color(self) -> tuple:
        if self._health > self._mid:
            return (0, 200, 0)      # verde
        if self._health > self._low:
            return (0, 200, 230)    # amarillo
        return (0, 0, 230)          # rojo

    def draw(self, frame, x: int, y: int, w: int, h: int):
        color = self._color()
        # marco
        cv2.rectangle(frame, (x, y), (x + w, y + h), (80, 80, 80), 2)
        # relleno proporcional a la salud (crece desde abajo)
        fill_h = int(h * self._health)
        top = y + (h - fill_h)
        cv2.rectangle(frame, (x, top), (x + w, y + h), color, -1)
        # etiqueta
        cv2.putText(frame, f"{int(self._health * 100)}%", (x - 2, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        return frame
