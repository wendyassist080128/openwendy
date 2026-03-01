#!/usr/bin/env python3
"""OpenWendy v2 — Entry point."""
import threading
import time
import webbrowser
from server.app import start_server

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:18888")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    start_server(port=18888)
