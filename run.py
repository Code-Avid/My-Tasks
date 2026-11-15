import os
import sys
import threading
import webbrowser

from app import create_app

app = create_app()


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    # فقط یک بار مرورگر باز بشه (نه توی reloader)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.0, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=not getattr(sys, "frozen", False))
    