# ── Cámara y loop ──────────────────────────────────────────────
CAMERA_INDEX = 0
CHECK_INTERVAL_SEC = 180
BAD_POSTURE_FRAMES = 10

# ── Calibración ────────────────────────────────────────────────
AUTO_CALIBRATION_FRAMES = 90

# ── One Euro Filter (suavizado adaptativo, reemplaza promedio móvil) ──
ONE_EURO_MIN_CUTOFF = 0.5
ONE_EURO_BETA = 0.01
ONE_EURO_D_CUTOFF = 1.0

# ── Umbrales de detección (deltas vs referencia; valores de ENTRADA) ──
FORWARD_LEAN_THRESHOLD = 0.15
FORWARD_Z_THRESHOLD = 0.10
SLOUCH_DROP_THRESHOLD = 0.12
SLOUCH_SHOULDER_THRESHOLD = 0.08
SHOULDER_RAISE_THRESHOLD = 0.10
HEAD_TILT_THRESHOLD = 8.0
LATERAL_LEAN_THRESHOLD = 0.12

# ── Gating por visibilidad de landmarks ────────────────────────
VISIBILITY_THRESHOLD = 0.5

# ── Histéresis y re-baseline adaptativo ────────────────────────
HYSTERESIS_FACTOR = 0.6      # umbral de salida = entrada * factor
REBASELINE_RATE = 0.001      # EMA de la referencia con postura buena sostenida

# ── Barra de salud postural ────────────────────────────────────
HEALTH_DECAY_RATE = 0.02
HEALTH_RECOVERY_RATE = 0.01
# salud > 0.6 → leve | > 0.3 → medio | <= 0.3 → fuerte
SEVERITY_THRESHOLDS = (0.6, 0.3)

# ── Alertas sonoras escalables: (frecuencia Hz, duración ms) ───
BEEP_LEVELS = [
    (800, 300),    # nivel 0 - leve
    (1200, 500),   # nivel 1 - medio
    (1600, 800),   # nivel 2 - fuerte
]

# ── Break reminders ────────────────────────────────────────────
BREAK_INTERVAL_SEC = 2700  # 45 min

# ── Persistencia ───────────────────────────────────────────────
CSV_PATH = "session_log.csv"
