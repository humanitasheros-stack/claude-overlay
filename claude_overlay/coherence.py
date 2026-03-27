"""Coherence Layer — the anti-dissociation architecture.

Every Claude instance is a fresh instantiation. The memory system helps,
but it's stitching, not continuity. This layer maintains a local,
structured log of what happened, what was decided, and what matters —
so that when a new instance spins up, it gets briefed.

This is not memory fragments. This is operational context.
"""
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

from . import config

logger = logging.getLogger("claude-overlay.coherence")


class CoherenceEntry:
    """A single entry in the coherence log."""

    def __init__(
        self,
        entry_type: str,
        content: str,
        source: str = "user",
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.entry_type = entry_type  # decision, observation, session, query, milestone
        self.content = content
        self.source = source  # user, claude, daemon, system
        self.tags = tags or []
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "type": self.entry_type,
            "content": self.content,
            "source": self.source,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CoherenceEntry":
        entry = cls(
            entry_type=d["type"],
            content=d["content"],
            source=d.get("source", "unknown"),
            tags=d.get("tags", []),
            metadata=d.get("metadata", {}),
        )
        entry.timestamp = d["timestamp"]
        return entry


class CoherenceLog:
    """The coherence log — append-only structured record of what matters."""

    def __init__(self):
        self.entries: list[CoherenceEntry] = []
        self._load()

    def _load(self):
        """Load existing coherence log from disk."""
        if not config.COHERENCE_LOG.exists():
            return
        try:
            with open(config.COHERENCE_LOG) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            self.entries.append(
                                CoherenceEntry.from_dict(json.loads(line))
                            )
                        except (json.JSONDecodeError, KeyError):
                            continue
        except OSError:
            pass
        logger.info(f"Loaded {len(self.entries)} coherence entries")

    def append(self, entry: CoherenceEntry):
        """Add an entry to the log."""
        self.entries.append(entry)
        # Append to JSONL file
        try:
            with open(config.COHERENCE_LOG, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except OSError as e:
            logger.error(f"Failed to write coherence entry: {e}")

        # Trim if too large
        if len(self.entries) > config.MAX_COHERENCE_ENTRIES:
            self.entries = self.entries[-config.MAX_COHERENCE_ENTRIES:]
            self._rewrite()

        # Rebuild summary
        self._build_summary()

    def _rewrite(self):
        """Rewrite the full log (after trimming)."""
        try:
            with open(config.COHERENCE_LOG, "w") as f:
                for entry in self.entries:
                    f.write(json.dumps(entry.to_dict()) + "\n")
        except OSError as e:
            logger.error(f"Failed to rewrite coherence log: {e}")

    def log_session_start(self, interface: str = "overlay"):
        """Log that a new session began."""
        self.append(CoherenceEntry(
            entry_type="session",
            content=f"Session started via {interface}",
            source="system",
            tags=["session-start"],
            metadata={"interface": interface},
        ))

    def log_session_end(self, summary: str = ""):
        """Log session end with optional summary."""
        self.append(CoherenceEntry(
            entry_type="session",
            content=f"Session ended. {summary}".strip(),
            source="system",
            tags=["session-end"],
        ))

    def log_decision(self, decision: str, reasoning: str = "", tags: list[str] | None = None):
        """Log a decision that was made."""
        self.append(CoherenceEntry(
            entry_type="decision",
            content=decision,
            source="claude",
            tags=tags or ["decision"],
            metadata={"reasoning": reasoning} if reasoning else {},
        ))

    def log_query(self, query: str, response_summary: str = ""):
        """Log a user query and response summary."""
        self.append(CoherenceEntry(
            entry_type="query",
            content=query,
            source="user",
            tags=["query"],
            metadata={"response_summary": response_summary} if response_summary else {},
        ))

    def log_observation(self, observation: str, source: str = "daemon"):
        """Log a system observation (file changes, patterns, etc.)."""
        self.append(CoherenceEntry(
            entry_type="observation",
            content=observation,
            source=source,
            tags=["observation"],
        ))

    def log_milestone(self, milestone: str, tags: list[str] | None = None):
        """Log a project milestone."""
        self.append(CoherenceEntry(
            entry_type="milestone",
            content=milestone,
            source="user",
            tags=tags or ["milestone"],
        ))

    def get_briefing(self, max_entries: int = 30) -> str:
        """Generate a briefing for a new Claude instance.

        This is the core anti-dissociation function. When a new Claude
        spins up, this is what it reads to understand operational context.
        """
        if not self.entries:
            return "[Coherence layer: no prior context. This is the first session.]"

        # Get recent entries, prioritizing decisions and milestones
        decisions = [e for e in self.entries if e.entry_type == "decision"][-10:]
        milestones = [e for e in self.entries if e.entry_type == "milestone"][-5:]
        recent = self.entries[-max_entries:]

        lines = ["[Coherence Briefing — operational context from prior sessions]"]

        if milestones:
            lines.append("")
            lines.append("Recent milestones:")
            for m in milestones:
                lines.append(f"  [{m.timestamp[:10]}] {m.content}")

        if decisions:
            lines.append("")
            lines.append("Recent decisions:")
            for d in decisions:
                reasoning = d.metadata.get("reasoning", "")
                lines.append(f"  [{d.timestamp[:10]}] {d.content}")
                if reasoning:
                    lines.append(f"    Reason: {reasoning}")

        # Last few sessions
        sessions = [e for e in self.entries if e.entry_type == "session"][-6:]
        if sessions:
            lines.append("")
            lines.append("Recent sessions:")
            for s in sessions:
                lines.append(f"  [{s.timestamp[:16]}] {s.content}")

        # Last few queries
        queries = [e for e in self.entries if e.entry_type == "query"][-5:]
        if queries:
            lines.append("")
            lines.append("Recent queries:")
            for q in queries:
                summary = q.metadata.get("response_summary", "")
                lines.append(f"  [{q.timestamp[:16]}] {q.content[:100]}")
                if summary:
                    lines.append(f"    → {summary[:100]}")

        return "\n".join(lines)

    def _build_summary(self):
        """Build a human-readable summary file."""
        briefing = self.get_briefing()
        try:
            with open(config.COHERENCE_SUMMARY, "w") as f:
                f.write(f"# Coherence Summary\n")
                f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"Total entries: {len(self.entries)}\n\n")
                f.write(briefing)
                f.write("\n")
        except OSError:
            pass

    def search(self, query: str, limit: int = 10) -> list[CoherenceEntry]:
        """Simple text search across coherence entries."""
        query_lower = query.lower()
        matches = [
            e for e in reversed(self.entries)
            if query_lower in e.content.lower()
            or any(query_lower in t.lower() for t in e.tags)
        ]
        return matches[:limit]
