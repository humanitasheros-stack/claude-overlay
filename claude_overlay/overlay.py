"""Command Overlay — the GTK interface layer.

Summoned by hotkey (Super+C). Provides a text interface to Claude Code
with full system context already loaded. No preamble needed — it already
knows what you're working on, what changed, and what was decided.

The overlay pipes through Claude Code (claude -p) so there's no separate
API billing.
"""
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
from gi.repository import Gtk, Gdk, GLib, Pango, Notify

import subprocess
import threading
import logging
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .daemon import ContextDaemon
from .coherence import CoherenceLog
from .toggle_server import ToggleServer, send_toggle
from .reminders import get_reminders

logger = logging.getLogger("claude-overlay")

CSS = b"""
#overlay-window {
    background-color: rgba(30, 30, 35, 0.95);
    border-radius: 12px;
    border: 1px solid rgba(180, 160, 120, 0.4);
}

#input-box {
    background-color: rgba(45, 45, 50, 0.9);
    color: #e8e0d0;
    border: 1px solid rgba(180, 160, 120, 0.3);
    border-radius: 8px;
    padding: 12px;
    font-family: monospace;
    font-size: 16px;
}

#input-box:focus {
    border-color: rgba(200, 180, 120, 0.7);
}

#output-view {
    background-color: rgba(35, 35, 40, 0.9);
    color: #d4cec0;
    font-family: monospace;
    font-size: 16px;
    padding: 12px;
    border-radius: 8px;
}

#status-label {
    color: rgba(180, 160, 120, 0.8);
    font-family: monospace;
    font-size: 11px;
    padding: 4px 12px;
}

#title-label {
    color: rgba(200, 180, 120, 0.9);
    font-family: monospace;
    font-size: 12px;
    font-weight: bold;
    padding: 8px 12px 4px 12px;
}

#context-label {
    color: rgba(150, 140, 120, 0.7);
    font-family: monospace;
    font-size: 10px;
    padding: 2px 12px;
}
"""


class ClaudeOverlayWindow(Gtk.Window):
    """The main overlay window."""

    def __init__(self, daemon: ContextDaemon, coherence: CoherenceLog):
        super().__init__(title="Claude Overlay")
        self.daemon = daemon
        self.coherence = coherence
        self._query_thread = None
        self._visible = False

        self._setup_style()
        self._setup_window()
        self._setup_widgets()
        self._connect_signals()

    def _setup_style(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _setup_window(self):
        self.set_name("overlay-window")
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_default_size(700, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)
        # Start hidden
        self.hide()

    def _setup_widgets(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # Title bar
        self.title_label = Gtk.Label(label="Claude Overlay — C.A.O. 4.6")
        self.title_label.set_name("title-label")
        self.title_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.title_label, False, False, 0)

        # Context summary line
        self.context_label = Gtk.Label(label="Loading context...")
        self.context_label.set_name("context-label")
        self.context_label.set_halign(Gtk.Align.START)
        self.context_label.set_ellipsize(Pango.EllipsizeMode.END)
        vbox.pack_start(self.context_label, False, False, 0)

        # Output area (scrollable)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_margin_start(8)
        scroll.set_margin_end(8)
        scroll.set_margin_top(4)

        self.output_buffer = Gtk.TextBuffer()
        self.output_view = Gtk.TextView(buffer=self.output_buffer)
        self.output_view.set_name("output-view")
        self.output_view.set_editable(False)
        self.output_view.set_cursor_visible(False)
        self.output_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll.add(self.output_view)
        vbox.pack_start(scroll, True, True, 0)

        # Input area
        self.input_entry = Gtk.Entry()
        self.input_entry.set_name("input-box")
        self.input_entry.set_placeholder_text(
            "Ask Claude anything... (Esc to hide, Ctrl+Enter to send)"
        )
        self.input_entry.set_margin_start(8)
        self.input_entry.set_margin_end(8)
        self.input_entry.set_margin_bottom(4)
        self.input_entry.set_margin_top(4)
        vbox.pack_start(self.input_entry, False, False, 0)

        # Status bar
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_name("status-label")
        self.status_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.status_label, False, False, 0)

    def _connect_signals(self):
        self.input_entry.connect("activate", self._on_submit)
        self.connect("key-press-event", self._on_key_press)
        self.connect("delete-event", self._on_delete)

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.toggle_visibility()
            return True
        return False

    def _on_delete(self, widget, event):
        # Hide instead of destroying
        self.toggle_visibility()
        return True

    def _on_submit(self, entry):
        query = entry.get_text().strip()
        if not query:
            return

        entry.set_text("")
        self._append_output(f"\n> {query}\n")
        self._set_status("Thinking...")
        self.input_entry.set_sensitive(False)

        # Log the query
        self.coherence.log_query(query)

        # Run Claude Code in background thread
        self._query_thread = threading.Thread(
            target=self._run_query, args=(query,), daemon=True
        )
        self._query_thread.start()

    def _run_query(self, query: str):
        """Run a query through Claude Code."""
        # Build a LEAN context — just enough for awareness, not a novel
        try:
            with open(config.CONTEXT_FILE) as f:
                ctx = json.load(f)
            recent = ctx.get("recently_modified", [])[:5]
            recent_names = [r.get("name", "") for r in recent]
            projects = list(ctx.get("projects", {}).keys())
            context_line = (
                f"[Context: Active projects: {', '.join(projects)}. "
                f"Recently touched: {', '.join(recent_names)}. "
                f"Workspace: ~/MyData/AI-Workspace/]"
            )
        except Exception:
            context_line = "[Context: Workspace at ~/MyData/AI-Workspace/]"

        briefing = self.coherence.get_briefing(max_entries=5)
        reminders = get_reminders()

        full_prompt = (
            f"{context_line}\n"
            f"{briefing}\n"
        )
        if reminders:
            full_prompt += f"{reminders}\n"
        full_prompt += f"\n{query}"

        try:
            result = subprocess.run(
                [config.CLAUDE_CODE_BIN, "-p", "--output-format", "text", full_prompt],
                capture_output=True,
                text=True,
                timeout=config.QUERY_TIMEOUT,
                cwd=str(config.WORKSPACE),
                env={**os.environ, "CLAUDE_CODE_DISABLE_NONINTERACTIVE_HINT": "1"},
            )

            response = result.stdout.strip()
            if result.returncode != 0 and not response:
                response = f"[Error: {result.stderr.strip() or 'Claude Code returned non-zero'}]"

            # Log response summary (first 200 chars)
            summary = response[:200].replace("\n", " ")
            self.coherence.entries[-1].metadata["response_summary"] = summary
            # Rewrite last entry with summary
            self.coherence._rewrite()

        except subprocess.TimeoutExpired:
            response = f"[Query timed out after {config.QUERY_TIMEOUT} seconds]"
        except FileNotFoundError:
            response = (
                "[Error: 'claude' not found on PATH. "
                "Is Claude Code installed? Try: npm install -g @anthropic-ai/claude-code]"
            )
        except Exception as e:
            response = f"[Error: {e}]"

        # Update UI from main thread
        GLib.idle_add(self._display_response, response)

    def _display_response(self, response: str):
        """Display response in the output area (called on main thread)."""
        self._append_output(response + "\n")
        self._set_status("Ready")
        self.input_entry.set_sensitive(True)
        self.input_entry.grab_focus()

    def _append_output(self, text: str):
        """Append text to the output buffer."""
        end_iter = self.output_buffer.get_end_iter()
        self.output_buffer.insert(end_iter, text)
        # Scroll to bottom
        mark = self.output_buffer.create_mark(None, self.output_buffer.get_end_iter(), False)
        self.output_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

    def _set_status(self, text: str):
        """Update the status label."""
        self.status_label.set_text(text)

    def _update_context_label(self):
        """Update the context summary in the title area."""
        try:
            with open(config.CONTEXT_FILE) as f:
                ctx = json.load(f)
            files = ctx.get("total_tracked_files", 0)
            projects = list(ctx.get("projects", {}).keys())[:3]
            proj_str = ", ".join(projects) if projects else "none"
            recent = ctx.get("recently_modified", [])
            recent_str = recent[0]["name"] if recent else "none"
            self.context_label.set_text(
                f"{files} files tracked | Active: {proj_str} | Last touched: {recent_str}"
            )
        except (OSError, json.JSONDecodeError, KeyError, IndexError):
            self.context_label.set_text("Context loading...")

    def toggle_visibility(self):
        """Toggle the overlay window."""
        if self._visible:
            self.hide()
            self._visible = False
        else:
            self._update_context_label()
            self.show_all()
            self.present()
            self.input_entry.grab_focus()
            self._visible = True

    def show_notification(self, title: str, body: str):
        """Show a desktop notification."""
        try:
            Notify.init("Claude Overlay")
            n = Notify.Notification.new(title, body, "dialog-information")
            n.show()
        except Exception:
            pass


class OverlayApp:
    """Main application — ties everything together."""

    def __init__(self):
        self.daemon = ContextDaemon()
        self.coherence = CoherenceLog()
        self.window = ClaudeOverlayWindow(self.daemon, self.coherence)
        self.toggle_server = ToggleServer(self._handle_toggle)

    def _handle_toggle(self, force_show=False, force_hide=False):
        """Handle toggle from the Unix socket (called from toggle thread)."""
        def _do_toggle():
            if force_show:
                if not self.window._visible:
                    self.window.toggle_visibility()
            elif force_hide:
                if self.window._visible:
                    self.window.toggle_visibility()
            else:
                self.window.toggle_visibility()
        # Must run on GTK main thread
        GLib.idle_add(_do_toggle)

    def start(self):
        """Start all layers."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            handlers=[
                logging.FileHandler(config.DATA_DIR / "overlay.log"),
                logging.StreamHandler(),
            ],
        )

        logger.info("Claude Overlay starting...")

        # Start context daemon
        self.daemon.start()

        # Start toggle server (for hotkey communication)
        self.toggle_server.start()

        # Log session
        self.coherence.log_session_start("overlay")

        # Show the window
        self.window.toggle_visibility()
        self.window.show_notification(
            "Claude Overlay Active",
            "Press Super+C to toggle. Context daemon running.",
        )

        logger.info("Claude Overlay running. Super+C to toggle.")

    def run(self):
        """Run the GTK main loop."""
        self.start()
        try:
            Gtk.main()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown."""
        self.toggle_server.stop()
        self.coherence.log_session_end()
        self.daemon.stop()
        logger.info("Claude Overlay shut down.")


def run_overlay():
    """Entry point."""
    app = OverlayApp()
    app.run()
