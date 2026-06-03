import time

import cv2

from capture import Camera
from analyzer import PostureAnalyzer
from notifier import PostureNotifier
from session_stats import SessionStats
from health_bar import HealthBar
from tray import TrayIcon
from config import (
    CAMERA_INDEX,
    CHECK_INTERVAL_SEC,
    BAD_POSTURE_FRAMES,
    AUTO_CALIBRATION_FRAMES,
    ONE_EURO_MIN_CUTOFF,
    ONE_EURO_BETA,
    ONE_EURO_D_CUTOFF,
    FORWARD_LEAN_THRESHOLD,
    FORWARD_Z_THRESHOLD,
    SLOUCH_DROP_THRESHOLD,
    SLOUCH_SHOULDER_THRESHOLD,
    SHOULDER_RAISE_THRESHOLD,
    HEAD_TILT_THRESHOLD,
    LATERAL_LEAN_THRESHOLD,
    VISIBILITY_THRESHOLD,
    HYSTERESIS_FACTOR,
    REBASELINE_RATE,
    HEALTH_DECAY_RATE,
    HEALTH_RECOVERY_RATE,
    SEVERITY_THRESHOLDS,
    BEEP_LEVELS,
    BREAK_INTERVAL_SEC,
    CSV_PATH,
)

WINDOW_NAME = "Spine Guard"


class AppState:
    def __init__(self):
        self.paused = False
        self.minimized = False
        self.should_quit = False
        self.show_stats = False


def _draw_border(frame, severity: int):
    colors = [(0, 200, 0), (0, 200, 230), (0, 0, 230)]
    thickness = [4, 8, 12][severity]
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), colors[severity], thickness)


def _draw_controls(frame):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, h - 30), (w, h), (30, 30, 30), -1)
    cv2.putText(frame, "[C] Calibrar  [P] Pausa  [B] Break  [M] Minimizar  [Q] Salir",
                (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)


def _run_auto_calibration(camera, analyzer, state) -> bool:
    """Devuelve True si calibró, False si se canceló/cerró."""
    fail_count = 0
    while not state.should_quit:
        ok, frame = camera.read_frame()
        if not ok:
            # La cámara puede fallar los primeros reads mientras arranca;
            # toleramos un rato antes de rendirnos.
            fail_count += 1
            if fail_count > 60:
                print("Error: la camara no entrega frames.")
                return False
            time.sleep(0.03)
            continue
        fail_count = 0
        frame = cv2.flip(frame, 1)

        progress = analyzer.auto_calibrate(frame)

        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

        cv2.putText(frame, "CALIBRANDO POSTURA DE REFERENCIA", (w // 2 - 230, h // 2 - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, "Sentate derecho y mira la pantalla", (w // 2 - 200, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        bar_w = 400
        bar_x = w // 2 - bar_w // 2
        bar_y = h // 2 + 30
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + 25), (80, 80, 80), 2)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_w * progress), bar_y + 25),
                      (0, 200, 0), -1)
        cv2.putText(frame, f"{int(progress * 100)}%", (bar_x + bar_w + 15, bar_y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            state.should_quit = True
            return False

        if progress >= 1.0:
            return True

    return False


def main():
    camera = Camera(CAMERA_INDEX)
    if not camera.is_opened():
        print("Error: no se pudo abrir la camara.")
        return

    analyzer = PostureAnalyzer(
        forward_threshold=FORWARD_LEAN_THRESHOLD,
        forward_z_threshold=FORWARD_Z_THRESHOLD,
        slouch_drop_threshold=SLOUCH_DROP_THRESHOLD,
        slouch_shoulder_threshold=SLOUCH_SHOULDER_THRESHOLD,
        shoulder_raise_threshold=SHOULDER_RAISE_THRESHOLD,
        tilt_threshold=HEAD_TILT_THRESHOLD,
        lateral_threshold=LATERAL_LEAN_THRESHOLD,
        visibility_threshold=VISIBILITY_THRESHOLD,
        hysteresis_factor=HYSTERESIS_FACTOR,
        rebaseline_rate=REBASELINE_RATE,
        one_euro_min_cutoff=ONE_EURO_MIN_CUTOFF,
        one_euro_beta=ONE_EURO_BETA,
        one_euro_d_cutoff=ONE_EURO_D_CUTOFF,
        auto_calibration_frames=AUTO_CALIBRATION_FRAMES,
    )
    notifier = PostureNotifier(CHECK_INTERVAL_SEC, BEEP_LEVELS, BREAK_INTERVAL_SEC)
    stats = SessionStats()
    health = HealthBar(HEALTH_DECAY_RATE, HEALTH_RECOVERY_RATE, SEVERITY_THRESHOLDS)
    state = AppState()

    tray = TrayIcon(
        on_show=lambda: setattr(state, "minimized", False),
        on_pause=lambda: setattr(state, "paused", not state.paused),
        on_quit=lambda: setattr(state, "should_quit", True),
        on_stats=lambda: setattr(state, "show_stats", True),
    )
    tray.start()

    cv2.namedWindow(WINDOW_NAME)
    window_open = True

    print("Spine Guard v2.1 iniciado.")
    print("Calibrando... sentate derecho.")

    if not _run_auto_calibration(camera, analyzer, state):
        _shutdown(camera, analyzer, tray, stats, window_open)
        return

    print("Calibracion lista. Monitoreando postura.")
    notifier.reset_timer()
    notifier.reset_break_timer()
    bad_count = 0
    read_fails = 0

    while not state.should_quit:
        ok, frame = camera.read_frame()
        if not ok:
            read_fails += 1
            if read_fails > 90:
                print("Error: se perdio la camara.")
                break
            time.sleep(0.02)
            continue
        read_fails = 0
        frame = cv2.flip(frame, 1)

        # ── Gestión de ventana (minimizar / restaurar) ──────────
        if state.minimized and window_open:
            cv2.destroyWindow(WINDOW_NAME)
            window_open = False
        elif not state.minimized and not window_open:
            cv2.namedWindow(WINDOW_NAME)
            window_open = True

        # ── Estadísticas pedidas desde el tray ──────────────────
        if state.show_stats:
            state.show_stats = False
            s = stats.get_summary()
            tray.notify(
                "Estadisticas de sesion",
                f"Tiempo: {s.total_time_sec/60:.1f} min | "
                f"Buena postura: {s.good_percentage:.0f}% | "
                f"Alertas: {s.total_alerts}",
            )

        # ── Pausa ───────────────────────────────────────────────
        if state.paused:
            tray.update_icon(True)
            if window_open:
                paused_frame = frame.copy()
                h, w = paused_frame.shape[:2]
                cv2.rectangle(paused_frame, (0, 0), (w, h), (20, 20, 20), -1)
                cv2.addWeighted(paused_frame, 0.6, frame, 0.4, 0, paused_frame)
                cv2.putText(paused_frame, "PAUSADO", (w // 2 - 90, h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 200, 230), 3)
                _draw_controls(paused_frame)
                cv2.imshow(WINDOW_NAME, paused_frame)
                if not _handle_keys(cv2.waitKey(1) & 0xFF, state, analyzer, frame, notifier, stats):
                    pass
                if window_open and cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    state.should_quit = True
            else:
                time.sleep(0.03)
            continue

        # ── Análisis ────────────────────────────────────────────
        result = analyzer.analyze(frame)

        if result.reliable:
            health.update(result.is_good)
            stats.update(result.is_good)
            tray.update_icon(result.is_good)

            if not result.is_good:
                bad_count += 1
            else:
                bad_count = 0

            if bad_count >= BAD_POSTURE_FRAMES and notifier.should_notify():
                notifier.notify(result.message, health.get_severity())
                stats.register_alert()
                bad_count = 0
        else:
            # frame poco confiable: congelar estado, sin alertas espurias
            bad_count = 0
            tray.update_icon(True)

        if notifier.should_break_remind():
            notifier.break_remind()
            stats.register_break()

        # ── Render ──────────────────────────────────────────────
        if window_open:
            display = analyzer.draw(frame, result)
            h, w = display.shape[:2]
            health.draw(display, 15, 95, 25, h - 95 - 45)
            if result.reliable:
                _draw_border(display, health.get_severity())
            else:
                cv2.rectangle(display, (0, 0), (w - 1, h - 1), (120, 120, 120), 4)
            _draw_controls(display)
            cv2.imshow(WINDOW_NAME, display)

            _handle_keys(cv2.waitKey(1) & 0xFF, state, analyzer, frame, notifier, stats)

            if window_open and not state.minimized and \
                    cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                state.should_quit = True
        else:
            time.sleep(0.02)

    _shutdown(camera, analyzer, tray, stats, window_open)


def _handle_keys(key, state, analyzer, frame, notifier, stats) -> bool:
    if key == ord("q"):
        state.should_quit = True
    elif key == ord("c"):
        if analyzer.calibrate(frame):
            print("Recalibrado.")
            notifier.reset_timer()
    elif key == ord("p"):
        state.paused = not state.paused
    elif key == ord("b"):
        notifier.reset_break_timer()
        stats.register_break()
        print("Break registrado.")
    elif key == ord("m"):
        state.minimized = True
    return True


def _shutdown(camera, analyzer, tray, stats, window_open):
    try:
        stats.export_csv(CSV_PATH)
        s = stats.get_summary()
        print(f"\nSesion: {s.total_time_sec/60:.1f} min | "
              f"Buena postura: {s.good_percentage:.0f}% | "
              f"Alertas: {s.total_alerts} | Breaks: {s.breaks_taken}")
        print(f"Log guardado en {CSV_PATH}")
    except Exception as e:
        print(f"No se pudo exportar el CSV: {e}")

    camera.release()
    analyzer.close()
    tray.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
