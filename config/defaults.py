CAMERA_INDEX = 0
CHECK_INTERVAL_SEC = 180
BAD_POSTURE_FRAMES = 10

AUTO_CALIBRATION_FRAMES = 90

ONE_EURO_MIN_CUTOFF = 0.5
ONE_EURO_BETA = 0.01
ONE_EURO_D_CUTOFF = 1.0

FORWARD_LEAN_THRESHOLD = 0.15
FORWARD_Z_THRESHOLD = 0.10
SLOUCH_DROP_THRESHOLD = 0.12
SLOUCH_SHOULDER_THRESHOLD = 0.08
SHOULDER_RAISE_THRESHOLD = 0.10
HEAD_TILT_THRESHOLD = 8.0
LATERAL_LEAN_THRESHOLD = 0.12

VISIBILITY_THRESHOLD = 0.5
HYSTERESIS_FACTOR = 0.6
REBASELINE_RATE = 0.001

HEALTH_DECAY_RATE = 0.02
HEALTH_RECOVERY_RATE = 0.01
SEVERITY_THRESHOLDS = (0.6, 0.3)

BEEP_LEVELS = [
    (800, 300),
    (1200, 500),
    (1600, 800),
]

BREAK_INTERVAL_SEC = 2700
CSV_PATH = "session_log.csv"

DEFAULTS = {
    "camera_index": CAMERA_INDEX,
    "check_interval_sec": CHECK_INTERVAL_SEC,
    "bad_posture_frames": BAD_POSTURE_FRAMES,
    "auto_calibration_frames": AUTO_CALIBRATION_FRAMES,
    "forward_lean_threshold": FORWARD_LEAN_THRESHOLD,
    "forward_z_threshold": FORWARD_Z_THRESHOLD,
    "slouch_drop_threshold": SLOUCH_DROP_THRESHOLD,
    "slouch_shoulder_threshold": SLOUCH_SHOULDER_THRESHOLD,
    "shoulder_raise_threshold": SHOULDER_RAISE_THRESHOLD,
    "head_tilt_threshold": HEAD_TILT_THRESHOLD,
    "lateral_lean_threshold": LATERAL_LEAN_THRESHOLD,
    "health_decay_rate": HEALTH_DECAY_RATE,
    "health_recovery_rate": HEALTH_RECOVERY_RATE,
    "break_interval_min": BREAK_INTERVAL_SEC // 60,
    "sound_enabled": True,
    "notifications_enabled": True,
    "break_reminder_enabled": True,
    "theme": "dark",
    "csv_path": CSV_PATH,
}
