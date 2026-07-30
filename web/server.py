import os
import threading
import time

import cv2
from flask import Flask, Response, abort, jsonify, render_template, request, send_file

from config.defaults import CAMERA_INDEX
from config.settings import Settings
from core.capture import Camera
from core.voice import audio_path, ensure_cached
from web.engine import PostureEngine

app = Flask(__name__)

_settings = Settings()
engine = PostureEngine(_settings)

_capture_thread: threading.Thread | None = None
_running = False


def _capture_loop() -> None:
    """Modo local: lee la webcam con OpenCV y alimenta el motor.

    Para el modo remoto (a futuro), este hilo se reemplaza por un endpoint
    que recibe frames del navegador y llama a `engine.process_frame(frame)`.
    """
    global _running
    cam = Camera(_settings.get("camera_index") or CAMERA_INDEX)
    if not cam.is_opened():
        print("[web] Error: no se pudo abrir la camara.")
        return

    _running = True
    try:
        while _running:
            ok, frame = cam.read_frame()
            if not ok:
                time.sleep(0.03)
                continue
            frame = cv2.flip(frame, 1)
            engine.process_frame(frame)
    finally:
        cam.release()


def start_capture() -> None:
    global _capture_thread
    # Genera el cache de voz (gTTS) en segundo plano: no bloquea el arranque
    # y solo hace falta internet la primera vez.
    threading.Thread(target=ensure_cached, daemon=True).start()
    if _capture_thread is None or not _capture_thread.is_alive():
        _capture_thread = threading.Thread(target=_capture_loop, daemon=True)
        _capture_thread.start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    def gen():
        boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
        while True:
            jpeg = engine.get_jpeg()
            if jpeg is None:
                time.sleep(0.05)
                continue
            yield boundary + jpeg + b"\r\n"
            time.sleep(0.033)

    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/status")
def status():
    return jsonify(engine.get_status())


@app.route("/voice/<sev>")
def voice(sev: str):
    # El navegador reproduce la alerta hablada (mismos MP3 que el escritorio).
    if sev not in ("0", "1", "2", "break"):
        abort(404)
    path = audio_path(sev)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype="audio/mpeg")


@app.route("/recalibrate", methods=["POST"])
def recalibrate():
    engine.request_recalibration()
    return jsonify({"ok": True})


@app.route("/pause", methods=["POST"])
def pause():
    return jsonify({"paused": engine.toggle_pause()})


@app.route("/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        return jsonify(engine.update_config(
            check_interval_sec=data.get("check_interval_sec"),
            bad_posture_sec=data.get("bad_posture_sec"),
            break_interval_min=data.get("break_interval_min"),
        ))
    return jsonify(engine.get_config())
