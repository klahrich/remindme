# Plan: Google Calendar → Twilio 1-Minute Call Reminders

**Date:** 2026-07-17
**Source:** `docs/project_brief.md`

## Goal

Automatically place a phone call (via Twilio) ~1 minute before every meeting across
all Google Calendars linked to the user's primary Google account. Secondary calendars
are surfaced through the primary account's OAuth, so only one Google Cloud project /
OAuth client is needed.

## Key decisions (pending user confirmation — see Open Questions)

- **Architecture:** stateless "minute-check" script (brief's second option) instead of
  in-memory `threading.Timer`s. Rationale: survives crashes/reboots, no long-lived
  process state, idempotent.
- **Scheduler:** Windows environment (no cron). Options: Windows Task Scheduler
  (every 1 min) or a lightweight `sleep(60)` loop runner. Default: Task Scheduler
  wrapper with a loop-runner fallback for testing.
- **Query window:** events starting in `[now + 55s, now + 115s]` to tolerate scheduler
  jitter. Dedupe guard (below) prevents double-calls if a run fires twice in-window.
- **Skip:** all-day events, holiday/subscription calendars, declined events.
- **Dedupe across calendars:** same meeting on multiple calendars → one call
  (keyed on normalized summary + start time).

## Secrets & repo hygiene (repo is PUBLIC)

- `.gitignore` must include: `credentials.json`, `token.json`, `.env`, `__pycache__/`,
  `state/`, `venv/`, `.venv/`.
- All secrets via `.env` (loaded with `python-dotenv`), never hardcoded.
- A `.env.example` with placeholder keys is committed for documentation.

## Proposed project layout

```
remindme/
├── docs/project_brief.md
├── stories/2026-07-17-gcal-twilio-call-reminders.md
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── src/
│   ├── main.py            # entry point: one minute-check run
│   ├── gcal.py            # OAuth + calendar/event fetching
│   ├── caller.py          # Twilio call logic + TwiML message
│   ├── dedupe.py          # in-run + cross-run dedupe (state file)
│   └── config.py          # env loading, constants (lead time, window)
├── state/                 # gitignored; seen-events log for cross-run dedupe
└── scripts/
    ├── setup_task.ps1     # registers Windows Task Scheduler job (every 1 min)
    └── loop_runner.py     # optional: runs minute-check every 60s in a loop
```

## Implementation steps

1. **Repo scaffolding**
   - `.gitignore` (secrets + state), `requirements.txt`
     (`google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`,
     `twilio`, `python-dotenv`), `.env.example`, README with setup instructions.

2. **Google Calendar integration (`gcal.py`)**
   - OAuth installed-app flow; token persisted to `token.json` (gitignored);
     refresh automatically. Scope: `calendar.readonly`.
   - `list_calendars()`: all calendars on the primary account's calendar list,
     excluding holiday/subscription calendars (configurable blocklist).
   - `get_events_in_window(service, calendar_id, t_min, t_max)`:
     `singleEvents=True` (expands recurrences), `orderBy="startTime"`,
     skip all-day events (no `dateTime`), skip declined (attendee `self` with
     `responseStatus=declined`).

3. **Twilio caller (`caller.py`)**
   - `place_call(summary, start_time)` using inline TwiML `<Say>` (voice Polly.Joey).
   - Message includes meeting name and actual start time.
   - Errors caught and logged (never crash the run); return call SID for logging.
   - Trial-account caveat documented (verified callee, trial preamble).

4. **Dedupe (`dedupe.py`)**
   - In-run: key = `(normalized_summary, start_iso)` — collapse cross-calendar dupes.
   - Cross-run: append keys to `state/seen.json` (or date-sharded files); skip any
     key already seen. Prune entries older than 24h. Protects against Task Scheduler
     double-fires and manual reruns.

5. **Orchestrator (`main.py`)**
   - Load env → build service → compute window (`now+55s`..`now+115s`, lead time and
     window size from config) → iterate calendars → collect → dedupe → call.
   - Structured logging to stdout + `state/run.log` (gitignored).
   - Exit codes: 0 ok, 1 auth/config error, 2 partial failure (for Task Scheduler
     visibility).

6. **Scheduling (`scripts/`)**
   - `setup_task.ps1`: `schtasks` / `Register-ScheduledTask` creating a
     every-1-minute task running `python src/main.py` with the repo as working dir.
   - `loop_runner.py`: `while True: run_check(); sleep(60)` with run-duration-aware
     sleep, for dev/testing and non-Task-Scheduler use.

7. **Testing**
   - `--dry-run` flag: prints what *would* be called, no Twilio call.
   - `--test-call "Fake Meeting"`: places one real call immediately to validate
     Twilio creds + number before relying on the scheduler.
   - Manual end-to-end: create a calendar event starting in ~3 minutes, run once,
     confirm the call lands ~1 minute before start.

8. **Docs & commit**
   - README: Google Cloud setup steps, Twilio setup, first-run OAuth consent,
     scheduler install, dry-run/test-call usage, trial limitations.

## What I need from the user

| Item | Where it goes | Notes |
|---|---|---|
| Google Cloud project + Calendar API enabled + OAuth **Desktop** client → `credentials.json` | repo root (gitignored) | One-time browser consent on first run |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` | `.env` | From Twilio console |
| Twilio phone number | `.env` (`TWILIO_NUMBER`) | Must have voice capability |
| Number to call | `.env` (`MY_NUMBER`) | Must be verified if Twilio trial |
| Answers to open questions | — | Or "use defaults" |

## Open questions

1. Scheduler: Task Scheduler (recommended) vs loop runner vs in-memory timers?
2. Dedupe cross-calendar duplicates by title+time — confirm?
3. Skip "free" (non-busy) events? Skip declined? (defaults: no / yes)
4. Call content: plain TTS only, or interactive (ack/snooze)? (default: TTS only)
5. Overlapping/back-to-back meetings: allow simultaneous calls? (default: allow)
6. Twilio account exists already, or set up from scratch?
7. Local Windows machine only, or future always-on deployment (cloud VM / serverless)?
8. Lead time fixed at 1 min or configurable per calendar? (default: global config, 1 min)

## Risks / notes

- **Machine must be awake** at meeting time if running locally (no calls while asleep/off).
- **Twilio trial** prepends a recorded message before the TwiML — eat into the 1-minute warning; consider upgrading.
- **Timing drift:** Task Scheduler's minimum granularity is 1 minute and can be delayed under load; the 55–115s window absorbs this but the call may land 0–60s off target.
- **Public repo:** `.gitignore` is committed before any secret ever touches the working tree; `git status` sanity check before first commit of real code.
- **Rate limits:** negligible (Calendar API per-minute quota is huge for a handful of calendars).
