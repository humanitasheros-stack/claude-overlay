"""Context Daemon — watches the workspace and maintains a living context file.

This is the peripheral vision of the system. It knows what files exist,
what changed recently, what's active, and builds a context snapshot that
the command layer can inject into Claude Code queries.
"""
import json
import os
import hashlib
import time
import threading
import logging
from pathlib import Path
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from . import config

logger = logging.getLogger("claude-overlay.daemon")


def _file_hash(path: Path, block_size: int = 8192) -> str:
    """Quick hash of first 8KB for change detection."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            h.update(f.read(block_size))
    except (OSError, PermissionError):
        return ""
    return h.hexdigest()


def _should_track(path: Path) -> bool:
    """Check if a file should be tracked."""
    if any(part in config.IGNORE_DIRS for part in path.parts):
        return False
    if path.suffix.lower() not in config.TRACKED_EXTENSIONS:
        return False
    if path.name.startswith("."):
        return False
    return True


def _file_info(path: Path) -> dict:
    """Build info dict for a single file."""
    try:
        stat = path.stat()
        return {
            "path": str(path),
            "name": path.name,
            "suffix": path.suffix,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat(),
            "hash": _file_hash(path),
            "project": _infer_project(path),
        }
    except (OSError, PermissionError):
        return None


def _infer_project(path: Path) -> str:
    """Infer which project a file belongs to based on path."""
    active = config.WORKSPACE / "_Active_Projects"
    try:
        rel = path.relative_to(active)
        return rel.parts[0] if rel.parts else "unknown"
    except ValueError:
        # Not under _Active_Projects
        ops = config.WORKSPACE / "Ops"
        try:
            path.relative_to(ops)
            return "Ops"
        except ValueError:
            return "workspace-root"


class ContextBuilder:
    """Builds and maintains the living context snapshot."""

    def __init__(self):
        self.file_index: dict[str, dict] = {}
        self.recent_changes: list[dict] = []
        self._lock = threading.Lock()
        self._load_index()

    def _load_index(self):
        """Load existing index from disk."""
        if config.FILE_INDEX.exists():
            try:
                with open(config.FILE_INDEX) as f:
                    self.file_index = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.file_index = {}

    def full_scan(self):
        """Walk the workspace and build complete file index."""
        logger.info("Running full workspace scan...")
        new_index = {}
        for watch_dir in config.WATCH_DIRS:
            for root, dirs, files in os.walk(watch_dir):
                # Prune ignored directories
                dirs[:] = [
                    d for d in dirs
                    if d not in config.IGNORE_DIRS and not d.startswith(".")
                ]
                root_path = Path(root)
                depth = len(root_path.relative_to(watch_dir).parts)
                if depth > config.MAX_WATCH_DEPTH:
                    dirs.clear()
                    continue
                for fname in files:
                    fpath = root_path / fname
                    if _should_track(fpath):
                        info = _file_info(fpath)
                        if info:
                            new_index[str(fpath)] = info

        with self._lock:
            self.file_index = new_index
            self._save_index()

        logger.info(f"Indexed {len(new_index)} files")
        self.build_context()

    def record_change(self, path: str, event_type: str):
        """Record a file change event."""
        fpath = Path(path)
        if not _should_track(fpath):
            return

        info = _file_info(fpath)
        change = {
            "path": path,
            "event": event_type,
            "time": datetime.now(timezone.utc).isoformat(),
            "project": _infer_project(fpath),
        }

        with self._lock:
            self.recent_changes.append(change)
            # Keep last 100 changes
            self.recent_changes = self.recent_changes[-100:]

            if info and event_type != "deleted":
                self.file_index[path] = info
            elif event_type == "deleted" and path in self.file_index:
                del self.file_index[path]

            self._save_index()

        self.build_context()

    def _save_index(self):
        """Persist file index to disk."""
        try:
            with open(config.FILE_INDEX, "w") as f:
                json.dump(self.file_index, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save file index: {e}")

    def build_context(self):
        """Build the living context snapshot for the command layer."""
        with self._lock:
            index = dict(self.file_index)
            changes = list(self.recent_changes)

        # Active projects summary
        projects = {}
        for info in index.values():
            proj = info.get("project", "unknown")
            if proj not in projects:
                projects[proj] = {"file_count": 0, "latest_modified": "", "files": []}
            projects[proj]["file_count"] += 1
            projects[proj]["files"].append(info["name"])
            if info["modified"] > projects[proj]["latest_modified"]:
                projects[proj]["latest_modified"] = info["modified"]

        # Recently modified files (last 24h)
        cutoff = time.time() - 86400
        recent_files = sorted(
            [
                info for info in index.values()
                if datetime.fromisoformat(info["modified"]).timestamp() > cutoff
            ],
            key=lambda x: x["modified"],
            reverse=True,
        )[:20]

        context = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "workspace": str(config.WORKSPACE),
            "total_tracked_files": len(index),
            "projects": {
                k: {"file_count": v["file_count"], "latest_modified": v["latest_modified"]}
                for k, v in sorted(
                    projects.items(),
                    key=lambda x: x[1]["latest_modified"],
                    reverse=True,
                )
            },
            "recently_modified": [
                {"name": f["name"], "project": f["project"], "modified": f["modified"]}
                for f in recent_files
            ],
            "recent_changes": changes[-20:],
        }

        try:
            with open(config.CONTEXT_FILE, "w") as f:
                json.dump(context, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to write context: {e}")

    def get_context_for_prompt(self) -> str:
        """Return a text summary suitable for injecting into a Claude prompt."""
        try:
            with open(config.CONTEXT_FILE) as f:
                ctx = json.load(f)
        except (OSError, json.JSONDecodeError):
            return "[Context daemon: no context available yet]"

        lines = [
            f"[System Context — {ctx['generated']}]",
            f"Workspace: {ctx['workspace']} ({ctx['total_tracked_files']} tracked files)",
            "",
            "Active projects (by recency):",
        ]
        for proj, info in list(ctx["projects"].items())[:8]:
            lines.append(f"  {proj}: {info['file_count']} files, last modified {info['latest_modified'][:10]}")

        if ctx.get("recently_modified"):
            lines.append("")
            lines.append("Recently modified:")
            for f in ctx["recently_modified"][:10]:
                lines.append(f"  {f['name']} ({f['project']}) — {f['modified'][:16]}")

        if ctx.get("recent_changes"):
            lines.append("")
            lines.append("Recent activity:")
            for c in ctx["recent_changes"][-5:]:
                lines.append(f"  {c['event']}: {Path(c['path']).name} ({c['project']})")

        return "\n".join(lines)


class WorkspaceEventHandler(FileSystemEventHandler):
    """Handles filesystem events from watchdog."""

    def __init__(self, context_builder: ContextBuilder):
        self.ctx = context_builder

    def on_created(self, event):
        if not event.is_directory:
            self.ctx.record_change(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory:
            self.ctx.record_change(event.src_path, "modified")

    def on_deleted(self, event):
        if not event.is_directory:
            self.ctx.record_change(event.src_path, "deleted")

    def on_moved(self, event):
        if not event.is_directory:
            self.ctx.record_change(event.src_path, "moved_from")
            self.ctx.record_change(event.dest_path, "moved_to")


class ContextDaemon:
    """The main daemon process — runs the watcher and maintains context."""

    def __init__(self):
        self.context_builder = ContextBuilder()
        self.observer = Observer()
        self._running = False

    def start(self):
        """Start the daemon."""
        logger.info("Context daemon starting...")
        self.context_builder.full_scan()

        handler = WorkspaceEventHandler(self.context_builder)
        for watch_dir in config.WATCH_DIRS:
            self.observer.schedule(handler, str(watch_dir), recursive=True)

        self.observer.start()
        self._running = True
        logger.info("Context daemon running. Watching: %s", config.WATCH_DIRS)

    def stop(self):
        """Stop the daemon."""
        if self._running:
            self.observer.stop()
            self.observer.join()
            self._running = False
            logger.info("Context daemon stopped.")

    def get_context(self) -> str:
        """Get current context for prompt injection."""
        return self.context_builder.get_context_for_prompt()


def run_daemon():
    """Entry point for running the daemon standalone."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    daemon = ContextDaemon()
    daemon.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
