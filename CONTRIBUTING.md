# Contributing to meetingtime

Thanks for your interest! Contributions of all kinds are welcome — bug reports,
features, docs, and ideas.

## Ways to contribute

- **Report a bug** → open an issue with the *Bug report* template
- **Suggest a feature** → open an issue with the *Feature request* template
- **Submit code** → fork, branch, PR (see below)

## Development setup

Prerequisites: [uv](https://docs.astral.sh/uv/), Python ≥ 3.11 (uv manages it).

```bash
git clone https://github.com/klahrich/meetingtime.git
cd meetingtime
uv sync --dev
```

To actually run the app you need your own Google + Twilio credentials (see the
[README](README.md#setup)). **Never commit real credentials** — `.env`,
`*-oauth-client.json`, `token.json`, and `state/` are gitignored; keep them that
way and double-check `git status` before committing.

## Testing your changes

You can exercise most paths without real calls:

```bash
uv run src/main.py --dry-run               # full calendar check, no phone calls
uv run src/main.py --test-call "Demo"      # one real call (your own Twilio creds)
uv run ruff check                          # lint (runs in CI)
```

Tips for safe testing:
- Create a throwaway calendar event 3 minutes in the future and use `--dry-run`.
- Twilio trial accounts can only call verified numbers — use your own.
- `LEAD_SECONDS` and `WINDOW_SECONDS` in `.env` make timing experiments easy.

## Pull requests

1. Fork the repo and create a branch from `main`
   (`git checkout -b feat/my-change`).
2. Keep PRs focused — one concern per PR.
3. Run `uv run ruff check` and make sure CI passes.
4. Update docs (`README.md`, `AGENTS.md`) if behavior or config changes.
5. Fill in the PR template; link any related issue.

## Project conventions

- Python runs exclusively via **uv** — no pip, no manual venvs.
- Architecture is **stateless**: each run checks a time window and exits. No
  in-memory timers or long-running state (the one exception: `state/seen.json`
  for dedupe). Please preserve this property.
- All configuration lives in `src/config.py` via `.env` with sane defaults —
  never hardcode secrets or user-specific values.
- See `AGENTS.md` for the architecture overview and locked design decisions.

## Code of conduct

Be kind and constructive. That's it — maintainers may remove anything that isn't.
