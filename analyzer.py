import math
import os
import time
from dataclasses import dataclass, field, fields, replace

import cv2
import mediapipe as mp
import numpy as np

from filters import MetricsSmoother

vision = mp.tasks.vision
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = vision.PoseLandmarker
PoseLandmarkerOptions = vision.PoseLandmarkerOptions
PoseLandmark = vision.PoseLandmark
RunningMode = vision.RunningMode

MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker_lite.task")

# Atajos de landmarks
NOSE = PoseLandmark.NOSE
LSH = PoseLandmark.LEFT_SHOULDER
RSH = PoseLandmark.RIGHT_SHOULDER
LEAR = PoseLandmark.LEFT_EAR
REAR = PoseLandmark.RIGHT_EAR
LEYE = PoseLandmark.LEFT_EYE_OUTER
REYE = PoseLandmark.RIGHT_EYE_OUTER

POSE_CONNECTIONS = [
    (NOSE, PoseLandmark.LEFT_EYE_INNER),
    (PoseLandmark.LEFT_EYE_INNER, PoseLandmark.LEFT_EYE),
    (PoseLandmark.LEFT_EYE, LEYE),
    (NOSE, PoseLandmark.RIGHT_EYE_INNER),
    (PoseLandmark.RIGHT_EYE_INNER, PoseLandmark.RIGHT_EYE),
    (PoseLandmark.RIGHT_EYE, REYE),
    (LEAR, LEYE),
    (REAR, REYE),
    (LSH, RSH),
    (LSH, PoseLandmark.LEFT_ELBOW),
    (RSH, PoseLandmark.RIGHT_ELBOW),
    (LSH, PoseLandmark.LEFT_HIP),
    (RSH, PoseLandmark.RIGHT_HIP),
]


def _dist(a, b) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


@dataclass
class PostureMetrics:
    forward_lean_ratio: float
    forward_z_ratio: float
    slouch_drop_ratio: float
    shoulder_width_norm: float
    shoulder_raise_ratio: float
    head_tilt_angle: float
    lateral_offset: float

    @staticmethod
    def average(items: list["PostureMetrics"]) -> "PostureMetrics":
        n = len(items)
        acc = {f.name: 0.0 for f in fields(PostureMetrics)}
        for m in items:
            for name in acc:
                acc[name] += getattr(m, name)
        return PostureMetrics(**{name: total / n for name, total in acc.items()})


@dataclass
class PostureResult:
    is_good: bool
    metrics: PostureMetrics
    smoothed: PostureMetrics
    problems: list[str] = field(default_factory=list)
    message: str = ""
    has_landmarks: bool = False
    landmarks_px: list[tuple[int, int]] = field(default_factory=list)
    confidence: float = 0.0
    reliable: bool = False


_ZERO = PostureMetrics(0, 0, 0, 0, 0, 0, 0)


class PostureAnalyzer:
    def __init__(
        self,
        forward_threshold: float,
        forward_z_threshold: float,
        slouch_drop_threshold: float,
        slouch_shoulder_threshold: float,
        shoulder_raise_threshold: float,
        tilt_threshold: float,
        lateral_threshold: float,
        visibility_threshold: float,
        hysteresis_factor: float,
        rebaseline_rate: float,
        one_euro_min_cutoff: float,
        one_euro_beta: float,
        one_euro_d_cutoff: float,
        auto_calibration_frames: int,
    ):
        self._forward_threshold = forward_threshold
        self._forward_z_threshold = forward_z_threshold
        self._slouch_drop_threshold = slouch_drop_threshold
        self._slouch_shoulder_threshold = slouch_shoulder_threshold
        self._shoulder_raise_threshold = shoulder_raise_threshold
        self._tilt_threshold = tilt_threshold
        self._lateral_threshold = lateral_threshold
        self._visibility_threshold = visibility_threshold
        self._hysteresis_factor = hysteresis_factor
        self._rebaseline_rate = rebaseline_rate

        self._frame_count = 0
        self._smoother = MetricsSmoother(one_euro_min_cutoff, one_euro_beta, one_euro_d_cutoff)
        self._calib_buffer: list[PostureMetrics] = []
        self._auto_calib_frames = auto_calibration_frames

        self._active_problems: set[str] = set()
        self._last_is_good = True

        with open(MODEL_PATH, "rb") as f:
            model_data = f.read()

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_buffer=model_data),
            running_mode=RunningMode.VIDEO,
            num_poses=1,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)

        self._ref: PostureMetrics | None = None

    # ── Detección y extracción ──────────────────────────────────
    def _detect(self, frame: np.ndarray):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._frame_count += 1
        timestamp_ms = int(self._frame_count * (1000 / 30))
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        if not result.pose_landmarks or len(result.pose_landmarks) == 0:
            return None
        return result.pose_landmarks[0]

    @staticmethod
    def _vis(lm, idx) -> float:
        v = getattr(lm[idx], "visibility", None)
        return v if v is not None else 1.0

    def _all_visible(self, lm, ids) -> bool:
        return all(self._vis(lm, i) >= self._visibility_threshold for i in ids)

    def _core_confidence(self, lm) -> float:
        return min(self._vis(lm, NOSE), self._vis(lm, LSH), self._vis(lm, RSH))

    def _extract_metrics(self, lm) -> PostureMetrics:
        nose = lm[NOSE]
        l_eye_out = lm[LEYE]
        r_eye_out = lm[REYE]
        l_ear = lm[LEAR]
        r_ear = lm[REAR]
        l_shoulder = lm[LSH]
        r_shoulder = lm[RSH]

        shoulder_width = _dist(l_shoulder, r_shoulder)
        if shoulder_width < 0.01:
            shoulder_width = 0.01

        # cabeza adelantada (tamaño): cara crece relativo a hombros
        face_width = _dist(l_eye_out, r_eye_out)
        forward_lean_ratio = face_width / shoulder_width

        # cabeza adelantada (profundidad): nariz se acerca en Z respecto a hombros
        mid_shoulder_z = (l_shoulder.z + r_shoulder.z) / 2
        forward_z_ratio = (mid_shoulder_z - nose.z) / shoulder_width

        # encorvado (caída): nariz se acerca verticalmente a los hombros
        mid_shoulder_x = (l_shoulder.x + r_shoulder.x) / 2
        mid_shoulder_y = (l_shoulder.y + r_shoulder.y) / 2
        nose_to_shoulder = math.hypot(nose.x - mid_shoulder_x, nose.y - mid_shoulder_y)
        slouch_drop_ratio = nose_to_shoulder / shoulder_width

        # encorvado (hombros adelante): el ancho de hombros crece al acercarse a la cámara
        shoulder_width_norm = shoulder_width

        # hombros subidos (tensión): distancia oreja->hombro se achica
        ear_sh_left = _dist(l_ear, l_shoulder)
        ear_sh_right = _dist(r_ear, r_shoulder)
        shoulder_raise_ratio = ((ear_sh_left + ear_sh_right) / 2) / shoulder_width

        # inclinación de cabeza
        ear_dy = l_ear.y - r_ear.y
        ear_dx = l_ear.x - r_ear.x
        head_tilt_angle = math.degrees(math.atan2(ear_dy, ear_dx)) if ear_dx != 0 else 0.0

        # inclinación lateral del cuerpo
        lateral_offset = (nose.x - mid_shoulder_x) / shoulder_width

        return PostureMetrics(
            forward_lean_ratio=forward_lean_ratio,
            forward_z_ratio=forward_z_ratio,
            slouch_drop_ratio=slouch_drop_ratio,
            shoulder_width_norm=shoulder_width_norm,
            shoulder_raise_ratio=shoulder_raise_ratio,
            head_tilt_angle=head_tilt_angle,
            lateral_offset=lateral_offset,
        )

    @staticmethod
    def _landmarks_to_px(lm, w: int, h: int) -> list[tuple[int, int]]:
        return [(int(p.x * w), int(p.y * h)) for p in lm]

    # ── Calibración ─────────────────────────────────────────────
    def auto_calibrate(self, frame: np.ndarray) -> float:
        """Acumula métricas. Devuelve progreso 0..1; al completar fija la referencia."""
        lm = self._detect(frame)
        if lm is not None and self._core_confidence(lm) >= self._visibility_threshold:
            self._calib_buffer.append(self._extract_metrics(lm))

        if len(self._calib_buffer) >= self._auto_calib_frames:
            self._ref = PostureMetrics.average(self._calib_buffer)
            self._calib_buffer.clear()
            self._smoother.reset()
            self._active_problems.clear()
            return 1.0
        return len(self._calib_buffer) / self._auto_calib_frames

    def calibrate(self, frame: np.ndarray) -> bool:
        """Recalibración manual instantánea (tecla C)."""
        lm = self._detect(frame)
        if lm is None or self._core_confidence(lm) < self._visibility_threshold:
            return False
        self._ref = self._extract_metrics(lm)
        self._smoother.reset()
        self._active_problems.clear()
        return True

    def is_calibrated(self) -> bool:
        return self._ref is not None

    # ── Histéresis y re-baseline ────────────────────────────────
    def _threshold(self, key: str, enter_th: float) -> float:
        """Umbral de salida (más bajo) si el problema ya estaba activo."""
        if key in self._active_problems:
            return enter_th * self._hysteresis_factor
        return enter_th

    def _rebaseline(self, smoothed: PostureMetrics):
        r = self._rebaseline_rate
        updates = {
            f.name: (1 - r) * getattr(self._ref, f.name) + r * getattr(smoothed, f.name)
            for f in fields(PostureMetrics)
        }
        self._ref = replace(self._ref, **updates)

    # ── Evaluación con gating + histéresis + Z ──────────────────
    def _evaluate(self, m: PostureMetrics, lm) -> tuple[bool, list[str]]:
        ref = self._ref
        problems = []
        new_active: set[str] = set()

        # Cabeza muy adelante: ratio de tamaño confirmado por profundidad Z
        key = "Cabeza muy adelante"
        if self._all_visible(lm, (NOSE, LEYE, REYE, LSH, RSH)):
            lean_delta = m.forward_lean_ratio - ref.forward_lean_ratio
            z_delta = m.forward_z_ratio - ref.forward_z_ratio
            th_lean = self._threshold(key, self._forward_threshold)
            confirmed = lean_delta > th_lean and z_delta > self._forward_z_threshold
            strong = lean_delta > self._forward_threshold * 1.6
            if confirmed or strong:
                problems.append(key)
                new_active.add(key)

        # Encorvado (cabeza baja)
        key = "Encorvado (cabeza baja)"
        if self._all_visible(lm, (NOSE, LSH, RSH)):
            delta = ref.slouch_drop_ratio - m.slouch_drop_ratio
            if delta > self._threshold(key, self._slouch_drop_threshold):
                problems.append(key)
                new_active.add(key)

        # Encorvado (hombros adelante)
        key = "Encorvado (hombros adelante)"
        if self._all_visible(lm, (LSH, RSH)):
            growth = (m.shoulder_width_norm - ref.shoulder_width_norm) / ref.shoulder_width_norm
            if growth > self._threshold(key, self._slouch_shoulder_threshold):
                problems.append(key)
                new_active.add(key)

        # Hombros tensos
        key = "Hombros tensos"
        if self._all_visible(lm, (LEAR, REAR, LSH, RSH)):
            delta = ref.shoulder_raise_ratio - m.shoulder_raise_ratio
            if delta > self._threshold(key, self._shoulder_raise_threshold):
                problems.append(key)
                new_active.add(key)

        # Cabeza inclinada
        key = "Cabeza inclinada"
        if self._all_visible(lm, (LEAR, REAR)):
            delta = abs(m.head_tilt_angle - ref.head_tilt_angle)
            if delta > self._threshold(key, self._tilt_threshold):
                problems.append(key)
                new_active.add(key)

        # Inclinado a un lado
        key = "Inclinado a un lado"
        if self._all_visible(lm, (NOSE, LSH, RSH)):
            delta = abs(m.lateral_offset - ref.lateral_offset)
            if delta > self._threshold(key, self._lateral_threshold):
                problems.append(key)
                new_active.add(key)

        self._active_problems = new_active
        return len(problems) == 0, problems

    def analyze(self, frame: np.ndarray) -> PostureResult:
        t = time.time()
        lm = self._detect(frame)
        h, w = frame.shape[:2]

        if lm is None:
            return PostureResult(
                is_good=self._last_is_good,
                metrics=_ZERO,
                smoothed=_ZERO,
                message="No se detecta persona",
                confidence=0.0,
                reliable=False,
            )

        raw = self._extract_metrics(lm)
        smoothed = self._smoother.smooth(raw, t)
        conf = self._core_confidence(lm)
        landmarks_px = self._landmarks_to_px(lm, w, h)
        reliable = conf >= self._visibility_threshold

        if not reliable or self._ref is None:
            msg = "Senal debil" if not reliable else "Sin calibrar - presiona C"
            return PostureResult(
                is_good=self._last_is_good,
                metrics=raw,
                smoothed=smoothed,
                message=msg,
                has_landmarks=True,
                landmarks_px=landmarks_px,
                confidence=conf,
                reliable=reliable,
            )

        is_good, problems = self._evaluate(smoothed, lm)
        if is_good:
            self._rebaseline(smoothed)
        self._last_is_good = is_good

        message = "Postura correcta" if is_good else " | ".join(problems)
        return PostureResult(
            is_good=is_good,
            metrics=raw,
            smoothed=smoothed,
            problems=problems,
            message=message,
            has_landmarks=True,
            landmarks_px=landmarks_px,
            confidence=conf,
            reliable=True,
        )

    # ── Render ──────────────────────────────────────────────────
    def draw(self, frame: np.ndarray, result: PostureResult) -> np.ndarray:
        output = frame.copy()
        h, w = output.shape[:2]

        if result.has_landmarks:
            for start, end in POSE_CONNECTIONS:
                cv2.line(output, result.landmarks_px[start], result.landmarks_px[end],
                         (200, 200, 200), 2)
            for idx in (NOSE, LEYE, REYE, LEAR, REAR, LSH, RSH):
                cv2.circle(output, result.landmarks_px[idx], 5, (0, 255, 255), -1)

            if self._ref is not None and result.reliable:
                lsh = result.landmarks_px[LSH]
                rsh = result.landmarks_px[RSH]
                mid = ((lsh[0] + rsh[0]) // 2, (lsh[1] + rsh[1]) // 2)
                line_color = (0, 200, 0) if result.is_good else (0, 0, 230)
                cv2.line(output, result.landmarks_px[NOSE], mid, line_color, 2)

        cv2.rectangle(output, (0, 0), (w, 80), (30, 30, 30), -1)

        if not result.reliable:
            cv2.putText(output, "SENAL DEBIL - acomodate frente a la camara", (10, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (160, 160, 160), 2)
            cv2.putText(output, f"Confianza: {int(result.confidence * 100)}%", (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)
        else:
            color = (0, 200, 0) if result.is_good else (0, 0, 230)
            status = "OK" if result.is_good else "MALA"
            cv2.putText(output, f"POSTURA: {status}", (10, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            s = result.smoothed
            detail = (f"Fwd:{s.forward_lean_ratio:.2f} Z:{s.forward_z_ratio:.2f} "
                      f"Drop:{s.slouch_drop_ratio:.2f} ShW:{s.shoulder_width_norm:.2f} "
                      f"Rise:{s.shoulder_raise_ratio:.2f}")
            cv2.putText(output, detail, (10, 52),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.36, (180, 180, 180), 1)
            cv2.putText(output, result.message, (10, 72),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        return output

    def close(self):
        self._landmarker.close()
