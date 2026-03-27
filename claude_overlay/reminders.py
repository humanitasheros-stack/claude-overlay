"""Reminders — appointment and self-care context injection.

Parses CLAUDE.md for time-sensitive operational info:
- Upcoming appointments
- Latest vitals
- Self-care flags

This is the somatic awareness layer. If appointments or vitals
are missing from context, the system isn't doing its job.
"""
import re
import logging
from datetime import datetime, date, timedelta
from pathlib import Path

from . import config

logger = logging.getLogger("claude-overlay.reminders")


def _read_claude_md() -> str:
    """Read the canonical CLAUDE.md."""
    try:
        return config.CLAUDE_MD.read_text(encoding="utf-8")
    except OSError:
        logger.warning("Could not read CLAUDE.md at %s", config.CLAUDE_MD)
        return ""


def _extract_section(text: str, heading: str) -> str:
    """Extract a markdown section by heading (## level)."""
    pattern = rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_appointments(section: str) -> list[dict]:
    """Parse appointment lines into structured data.

    Looks for patterns like:
    - **Name** (details) — **Day Month DD, HH:MM AM/PM**
    - ⚑ **Action** — details
    """
    appointments = []
    today = date.today()

    for line in section.splitlines():
        line = line.strip()
        if not line or line.startswith("|") or line.startswith("**Note"):
            continue

        # Try to extract a date from the line
        # Match patterns like "March 27, 11:30 AM", "May 6, 4:30 PM", "May 12, 10:20 AM"
        date_patterns = [
            r"(\w+ \d{1,2},?\s*\d{1,2}:\d{2}\s*[AP]M)",
            r"(\w+ \d{1,2})",
        ]

        appt_date = None
        for pat in date_patterns:
            m = re.search(pat, line)
            if m:
                date_str = m.group(1)
                # Try parsing with various formats
                for fmt in [
                    "%B %d, %I:%M %p",
                    "%B %d %I:%M %p",
                    "%B %d",
                ]:
                    try:
                        parsed = datetime.strptime(date_str, fmt)
                        # Assume current year if not specified
                        appt_date = parsed.replace(year=today.year).date()
                        break
                    except ValueError:
                        continue
                if appt_date:
                    break

        # Clean up the line for display
        clean = line.lstrip("- ").strip()

        appointments.append({
            "text": clean,
            "date": appt_date,
            "is_flag": line.startswith("- ⚑") or "⚑" in line,
        })

    return appointments


def _parse_vitals(section: str) -> dict | None:
    """Extract the most recent vitals entry from the table."""
    lines = section.strip().splitlines()
    # Find table rows (skip header and separator)
    data_lines = [
        l for l in lines
        if l.strip().startswith("|") and not l.strip().startswith("| Date")
        and "---" not in l
    ]
    if not data_lines:
        return None

    # Last row is most recent
    last = data_lines[-1]
    cells = [c.strip() for c in last.split("|")[1:-1]]  # skip empty first/last from split
    if len(cells) >= 6:
        return {
            "date": cells[0],
            "bp": cells[2],
            "weight": cells[3],
            "energy": cells[4],
            "sleep": cells[5],
            "notes": cells[6] if len(cells) > 6 else "",
        }
    return None


def get_reminders() -> str:
    """Build a compact reminders string for prompt injection.

    Returns a short block of text with:
    - Upcoming appointments (next 14 days highlighted)
    - Action flags (⚑ items)
    - Latest vitals snapshot
    """
    text = _read_claude_md()
    if not text:
        return ""

    lines = []
    today = date.today()
    soon = today + timedelta(days=14)

    # --- Appointments ---
    appt_section = _extract_section(text, "Appointments")
    if appt_section:
        appointments = _parse_appointments(appt_section)
        upcoming = []
        flags = []

        for appt in appointments:
            if appt["is_flag"]:
                flags.append(appt["text"])
            elif appt["date"]:
                if appt["date"] >= today:
                    days_away = (appt["date"] - today).days
                    if days_away == 0:
                        urgency = "TODAY"
                    elif days_away == 1:
                        urgency = "TOMORROW"
                    elif days_away <= 7:
                        urgency = f"in {days_away} days"
                    else:
                        urgency = f"{appt['date'].strftime('%b %d')}"
                    upcoming.append(f"  [{urgency}] {appt['text']}")
            else:
                # No parseable date but still an appointment line
                upcoming.append(f"  {appt['text']}")

        if upcoming or flags:
            lines.append("[Appointments & Reminders]")
            for u in upcoming:
                lines.append(u)
            for f in flags:
                # Avoid double ⚑ if already in the text
                prefix = "  ⚑ " if "⚑" not in f else "  "
                lines.append(f"{prefix}{f}")

    # --- Vitals ---
    vitals_section = _extract_section(text, "Vitals Log")
    if vitals_section:
        vitals = _parse_vitals(vitals_section)
        if vitals:
            parts = []
            if vitals["weight"] and vitals["weight"] != "—":
                parts.append(f"Wt: {vitals['weight']}")
            if vitals["bp"] and vitals["bp"] != "—":
                parts.append(f"BP: {vitals['bp']}")
            if parts:
                lines.append(f"[Last vitals ({vitals['date']}): {', '.join(parts)}]")

    # --- Self-care check ---
    # If no vitals in last 7 days, flag it
    if vitals_section:
        vitals = _parse_vitals(vitals_section)
        if vitals and vitals["date"]:
            try:
                for fmt in ["%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        last_vitals_date = datetime.strptime(vitals["date"], fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    last_vitals_date = None

                if last_vitals_date and (today - last_vitals_date).days > 7:
                    lines.append(f"[⚠ Vitals last recorded {vitals['date']} — over a week ago]")
            except Exception:
                pass

    return "\n".join(lines)
