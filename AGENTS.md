# AGENTS.md — remindme

## Status
**Live since 2026-07-17.** E2E test passed: Task Scheduler (`RemindMeMinuteCheck`,
every 1 min) detected a test event, placed the call ~65s before start, and
dedupe correctly suppressed the repeat on the next run. Twilio trial account
(preamble plays before message; callee must be a verified number).

## What this is
Stateless Python app that calls the user's phone (Twilio) ~1 minute before every
Google Calendar meeting, across all calendars linked to one Google account.
Full rationale & decisions: `docs/project_brief.md`,
`stories/2026-07-17-gcal-twilio-call-reminders.md`.

## Non-negotiables
- **Repo is PUBLIC.** Never commit secrets: `.env`, `*-oauth-client.json`,
  `token.json`, `state/` are gitignored — keep them that way. Check `git status`
  before every commit.
- Run Python exclusively via **uv** (`uv run ...`, `uv add <pkg>`). No pip, no
  manual venv activation.
- Architecture is **stateless minute-check** (no in-memory timers, no long-running
  process required). Scheduling = Windows Task Scheduler (`scripts/setup_task.ps1`);
  `scripts/loop_runner.py` is the fallback.

## Layout
- `src/config.py` — all env vars & defaults (single source of truth for config)
- `src/gcal.py` — OAuth (token in `token.json`), calendar list, event fetch, skip rules
- `src/caller.py` — Twilio call (inline TwiML `<Say>`)
- `src/dedupe.py` — cross-calendar + cross-run dedupe (`state/seen.json`, 24h prune)
- `src/main.py` — entry point; flags: `--dry-run`, `--test-call`, `--lead-seconds`
- `scripts/setup_task.ps1` — register the every-minute scheduled task
- `state/` — runtime logs + seen-events (gitignored)

## Locked decisions (2026-07-17)
Skip: holidays/birthdays (blocklist), all-day, declined, "free" (transparent),
cancelled. Dedupe duplicate events across calendars by normalized title+start.
Plain TTS call, no interactivity. Overlapping meetings → allow multiple calls.
Local Windows only; machine must be awake. Lead time configurable (`LEAD_SECONDS`,
default 60). Twilio trial account — callee must be a verified number.

## Common commands
```bash
uv sync                                  # install deps
uv run src/main.py --dry-run             # first run: triggers OAuth consent in browser
uv run src/main.py --test-call "Demo"    # validate Twilio with one real call
uv run src/main.py                       # one minute-check (what the task runs)
powershell -ExecutionPolicy Bypass -File scripts/setup_task.ps1   # schedule it
```

## Exit codes (main.py)
0 = ok · 1 = config/auth error · 2 = partial failure (some calendar/call failed)
