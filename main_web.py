from web.server import app, start_capture


def main():
    start_capture()
    print("PostureChecker Web -> http://127.0.0.1:5000  (Ctrl+C para salir)")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
