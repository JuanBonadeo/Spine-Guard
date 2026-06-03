class HealthBar:

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
        if self._health > self._mid:
            return 0
        if self._health > self._low:
            return 1
        return 2
