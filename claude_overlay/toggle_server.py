"""Toggle server — listens on a Unix socket for show/hide commands.

On Wayland (COSMIC), xdotool can't manage windows. Instead, the hotkey
script sends a toggle signal over a Unix socket, and the overlay
handles its own visibility.
"""
import socket
import os
import threading
import logging

logger = logging.getLogger("claude-overlay.toggle")

SOCKET_PATH = os.path.expanduser("~/.claude-overlay/overlay.sock")


class ToggleServer:
    """Listens on a Unix socket for toggle commands."""

    def __init__(self, toggle_callback):
        self.toggle_callback = toggle_callback
        self._running = False
        self._thread = None
        self._sock = None

    def start(self):
        # Clean up stale socket
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(SOCKET_PATH)
        self._sock.listen(1)
        self._sock.settimeout(1.0)
        self._running = True

        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        logger.info(f"Toggle server listening on {SOCKET_PATH}")

    def _listen(self):
        while self._running:
            try:
                conn, _ = self._sock.accept()
                data = conn.recv(64).decode().strip()
                if data == "toggle":
                    self.toggle_callback()
                elif data == "show":
                    self.toggle_callback(force_show=True)
                elif data == "hide":
                    self.toggle_callback(force_hide=True)
                elif data == "quit":
                    self._running = False
                conn.close()
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self):
        self._running = False
        if self._sock:
            self._sock.close()
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)


def send_toggle(command: str = "toggle"):
    """Send a command to the running overlay."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(SOCKET_PATH)
        sock.send(command.encode())
        sock.close()
        return True
    except (ConnectionRefusedError, FileNotFoundError):
        return False
