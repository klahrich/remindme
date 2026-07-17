"""Alternative to Task Scheduler: run the minute-check every 60s in a loop.

Usage (from repo root):
    uv run scripts/loop_runner.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import config  # noqa: E402
import main  # noqa: E402

INTERVAL = config.WINDOW_SECONDS


def run():
    main.setup_logging()
    while True:
        started = time.monotonic()
        try:
            main.run_check(lead_seconds=config.LEAD_SECONDS, dry_run=False)
        except Exception:
            main.log.exception("Check run crashed")
        elapsed = time.monotonic() - started
        time.sleep(max(1.0, INTERVAL - elapsed))


if __name__ == "__main__":
    run()
