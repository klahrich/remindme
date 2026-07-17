"""Entry point: one stateless minute-check run.

Queries every linked Google Calendar for events starting ~LEAD_SECONDS from now
and places a Twilio call for each (deduped). Designed to be invoked every
WINDOW_SECONDS by Windows Task Scheduler (see scripts/setup_task.ps1).

Usage:
    uv run src/main.py                      # normal check
    uv run src/main.py --dry-run            # log what would be called, no calls
    uv run src/main.py --test-call "Demo"   # place one real call immediately
    uv run src/main.py --lead-seconds 300   # override lead time for this run
"""

import argparse
import datetime as dt
import logging
import sys

import caller
import config
import dedupe
import gcal

log = logging.getLogger("remindme")

# Small buffer so scheduler jitter doesn't push an event out of the window.
BUFFER_SECONDS = 5


def setup_logging():
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handlers = [logging.StreamHandler(),
                logging.FileHandler(config.LOG_FILE, encoding="utf-8")]
    for h in handlers:
        h.setFormatter(fmt)
        log.addHandler(h)
    log.setLevel(logging.INFO)


def parse_args():
    p = argparse.ArgumentParser(description="GCal -> Twilio minute-check")
    p.add_argument("--dry-run", action="store_true",
                   help="log matches without placing calls")
    p.add_argument("--test-call", metavar="TITLE", nargs="?", const="Test Meeting",
                   help="place one real call immediately, then exit")
    p.add_argument("--lead-seconds", type=int, default=config.LEAD_SECONDS,
                   help="call this many seconds before event start")
    return p.parse_args()


def run_check(lead_seconds: int, dry_run: bool) -> int:
    """One check. Returns process exit code."""
    problems = config.validate()
    if problems:
        for p in problems:
            log.error("Config: %s", p)
        return 1

    service = gcal.get_service()
    calendars = gcal.list_calendars(service)
    log.info("Checking %d calendars (blocklist: %s)",
             len(calendars), config.CALENDAR_BLOCKLIST)

    now = dt.datetime.now(dt.timezone.utc)
    window_start = now + dt.timedelta(seconds=lead_seconds - BUFFER_SECONDS)
    window_end = window_start + dt.timedelta(seconds=config.WINDOW_SECONDS)
    log.info("Window: events starting %s .. %s",
             window_start.strftime("%H:%M:%S"), window_end.strftime("%H:%M:%S"))

    store = dedupe.DedupeStore()
    in_run: set[str] = set()
    called = 0
    failures = 0

    for cal in calendars:
        cal_summary = cal.get("summary", "?")
        try:
            events = gcal.get_events_in_window(
                service, cal["id"], window_start, window_end)
        except Exception:
            log.exception("Failed to fetch events for calendar '%s'", cal_summary)
            failures += 1
            continue

        for event in events:
            summary = event.get("summary", "Untitled Meeting")
            reason = gcal.skip_reason(event)
            if reason:
                log.info("Skip '%s' (%s) [%s]", summary, reason, cal_summary)
                continue

            start = dt.datetime.fromisoformat(
                event["start"]["dateTime"].replace("Z", "+00:00"))
            key = dedupe.event_key(summary, start.isoformat())

            if key in in_run:
                log.info("Skip '%s' (duplicate across calendars) [%s]",
                         summary, cal_summary)
                continue
            in_run.add(key)

            if not store.is_new(key):
                log.info("Skip '%s' (already called in a previous run)", summary)
                continue

            if dry_run:
                log.info("[DRY RUN] Would call for '%s' at %s [%s]",
                         summary, start.astimezone().strftime("%H:%M"), cal_summary)
                store.mark(key)
                called += 1
                continue

            log.info("Target hit: '%s' starts %s [%s]",
                     summary, start.astimezone().strftime("%H:%M"), cal_summary)
            if caller.place_call(summary, start):
                store.mark(key)
                called += 1
            else:
                failures += 1

    store.save()
    log.info("Done: %d call(s)%s, %d failure(s)",
             called, " (dry run)" if dry_run else "", failures)
    return 2 if failures else 0


def main():
    setup_logging()
    args = parse_args()

    if args.test_call is not None:
        problems = [p for p in config.validate() if "Google" not in p]
        if problems:
            for p in problems:
                log.error("Config: %s", p)
            return 1
        start = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=1)
        sid = caller.place_call(args.test_call, start)
        return 0 if sid else 2

    return run_check(lead_seconds=args.lead_seconds, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
