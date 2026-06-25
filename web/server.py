import threading
import time

import cv2
from flask import Flask, Response, jsonify, render_template

from config.defaults import CAMERA_INDEX
from config.settings import Settings
from core.capture import Camera
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


@app.route("/recalibrate", methods=["POST"])
def recalibrate():
    engine.request_recalibration()
    return jsonify({"ok": True})


@app.route("/pause", methods=["POST"])
def pause():
    return jsonify({"paused": engine.toggle_pause()})
