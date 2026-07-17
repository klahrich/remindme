# remindme

Phone-call reminders **1 minute before every meeting**, across all Google Calendars
linked to one Google account. Built with Google Calendar API + Twilio, runs on
Windows via Task Scheduler (stateless minute-check every 60s).

## How it works

Every 60 seconds, `src/main.py` asks every (non-blocklisted) Google Calendar for
events starting ~60 seconds from now, filters out all-day / declined / "free" /
duplicate events, and places a Twilio call with a spoken meeting name and start
time. A small state file (`state/seen.json`) guarantees no double-calls.

## Setup

Prerequisites: [uv](https://docs.astral.sh/uv/), a Google account, a Twilio account
(trial works — callee number must be verified).

1. **Google Cloud**: create a project, enable **Google Calendar API**, configure the
   OAuth consent screen (External, add yourself as test user), create an
   **OAuth client ID (Desktop app)** and download the JSON as
   `gcp-remindme-oauth-client.json` in the repo root. (Already done for this repo.)
2. **Environment**: copy `.env.example` to `.env` and fill in your Twilio values.
3. **Install deps**: `uv sync`
4. **First run / OAuth consent** (opens a browser once, token cached in `token.json`):
   ```
   uv run src/main.py --dry-run
   ```
5. **Verify Twilio** (places one real call immediately):
   ```
   uv run src/main.py --test-call "Test Meeting"
   ```
6. **Schedule it** (registers the every-minute task):
   ```
   powershell -ExecutionPolicy Bypass -File scripts/setup_task.ps1
   ```

Alternative to Task Scheduler: `uv run scripts/loop_runner.py`

## Configuration (`.env`)

| Var | Default | Meaning |
|---|---|---|
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | — | Twilio credentials (required) |
| `TWILIO_FROM_NUMBER` / `TWILIO_TO_NUMBER` | — | Twilio number / number to call (required) |
| `LEAD_SECONDS` | `60` | call this long before event start |
| `WINDOW_SECONDS` | `60` | detection window; keep = scheduler interval |
| `SKIP_FREE_EVENTS` | `true` | skip events marked "free" |
| `CALENDAR_BLOCKLIST` | `holiday,birthday` | skip calendars matching these substrings |

## Notes & limitations

- The PC must be **awake** at meeting time — no calls while asleep/off.
- Twilio **trial** accounts prepend a recorded message and can only call verified numbers.
- Secrets (`.env`, OAuth JSON, `token.json`) are gitignored; the repo is public — keep it that way.
- Logs: `state/run.log`.
