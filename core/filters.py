import math
from dataclasses import fields, replace


class OneEuroFilter:

    def __init__(self, min_cutoff: float, beta: float, d_cutoff: float = 1.0):
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self._x_prev: float | None = None
        self._dx_prev = 0.0
        self._t_prev: float | None = None

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, x: float, t: float) -> float:
        if self._x_prev is None or self._t_prev is None:
            self._x_prev = x
            self._t_prev = t
            self._dx_prev = 0.0
            return x

        dt = t - self._t_prev
        if dt <= 0:
            dt = 1e-3

        dx = (x - self._x_prev) / dt
        a_d = self._alpha(self._d_cutoff, dt)
        dx_hat = a_d * dx + (1 - a_d) * self._dx_prev

        cutoff = self._min_cutoff + self._beta * abs(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1 - a) * self._x_prev

        self._x_prev = x_hat
        self._dx_prev = dx_hat
        self._t_prev = t
        return x_hat

    def reset(self):
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None


class MetricsSmoother:

    def __init__(self, min_cutoff: float, beta: float, d_cutoff: float = 1.0):
        self._params = (min_cutoff, beta, d_cutoff)
        self._filters: dict[str, OneEuroFilter] = {}

    def smooth(self, metrics, t: float):
        updates = {}
        for f in fields(metrics):
            if f.name not in self._filters:
                self._filters[f.name] = OneEuroFilter(*self._params)
            updates[f.name] = self._filters[f.name].filter(getattr(metrics, f.name), t)
        return replace(metrics, **updates)

    def reset(self):
        for filt in self._filters.values():
            filt.reset()
