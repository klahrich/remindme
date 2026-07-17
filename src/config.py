"""Central configuration, loaded from .env with sane defaults."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# --- Google ---
GOOGLE_CREDENTIALS_FILE = ROOT / os.getenv(
    "GOOGLE_CREDENTIALS_FILE", "gcp-remindme-oauth-client.json"
)
TOKEN_FILE = ROOT / "token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# --- Twilio ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
TWILIO_TO_NUMBER = os.getenv("TWILIO_TO_NUMBER", "")

# --- Behavior ---
LEAD_SECONDS = int(os.getenv("LEAD_SECONDS", "60"))
WINDOW_SECONDS = int(os.getenv("WINDOW_SECONDS", "60"))
SKIP_FREE_EVENTS = os.getenv("SKIP_FREE_EVENTS", "true").lower() == "true"
CALENDAR_BLOCKLIST = [
    s.strip().lower()
    for s in os.getenv("CALENDAR_BLOCKLIST", "holiday,birthday").split(",")
    if s.strip()
]

# --- State ---
STATE_DIR = ROOT / "state"
SEEN_FILE = STATE_DIR / "seen.json"
LOG_FILE = STATE_DIR / "run.log"


def validate() -> list[str]:
    """Return a list of missing/invalid config items (empty = all good)."""
    problems = []
    if not GOOGLE_CREDENTIALS_FILE.exists():
        problems.append(f"Google credentials file not found: {GOOGLE_CREDENTIALS_FILE}")
    for name in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
                 "TWILIO_FROM_NUMBER", "TWILIO_TO_NUMBER"):
        if not globals()[name]:
            problems.append(f"Missing env var: {name}")
    return problems
