"""Dedupe: in-run (cross-calendar) and cross-run (state file) duplicate protection."""

import datetime as dt
import json
import re

import config

PRUNE_AFTER = dt.timedelta(hours=24)


def event_key(summary: str, start_iso: str) -> str:
    """Stable key so the same meeting on multiple calendars dedupes to one call."""
    normalized = re.sub(r"\s+", " ", summary.strip().lower())
    return f"{normalized}|{start_iso}"


class DedupeStore:
    """Persists keys of already-called events in state/seen.json."""

    def __init__(self, path=config.SEEN_FILE):
        self.path = path
        self._seen: dict[str, str] = {}
        if path.exists():
            try:
                self._seen = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                self._seen = {}
        self._prune()

    def _prune(self):
        cutoff = dt.datetime.now(dt.timezone.utc) - PRUNE_AFTER
        self._seen = {
            k: ts for k, ts in self._seen.items()
            if dt.datetime.fromisoformat(ts) > cutoff
        }

    def is_new(self, key: str) -> bool:
        return key not in self._seen

    def mark(self, key: str):
        self._seen[key] = dt.datetime.now(dt.timezone.utc).isoformat()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._seen, indent=2))
